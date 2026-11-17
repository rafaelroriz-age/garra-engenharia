"""Cifra do snapshot: PBKDF2-HMAC-SHA256 + AES-256-GCM sobre gzip(JSON UTF-8) (DEC-57, T81).

Escolhida para o front decifrar só com WebCrypto + `DecompressionStream('gzip')`:

- chave: `PBKDF2(SHA-256, senha UTF-8, salt 16 bytes, 600000 iterações) -> 32 bytes`;
- cifra: AES-256-GCM, iv 12 bytes, sem AAD, tag de 16 bytes **anexada** ao fim do
  texto cifrado (o mesmo layout que `crypto.subtle.decrypt` espera);
- texto claro: `gzip(json.dumps({"gerado_em": ..., "rotas": {...}}).encode("utf-8"))`.

O envelope gravado em disco é um JSON com os binários em base64 padrão:
`{"v": 1, "kdf": {"alg": "PBKDF2-SHA256", "iter": 600000, "salt": b64},
"cifra": "AES-256-GCM", "iv": b64, "ct": b64, "gerado_em": iso8601}`.
"""
import base64
import gzip
import hashlib
import json
import os
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

VERSAO = 1
KDF_ALG = "PBKDF2-SHA256"
KDF_ITERACOES = 600_000
CIFRA_ALG = "AES-256-GCM"
TAMANHO_SALT = 16
TAMANHO_IV = 12
TAMANHO_CHAVE = 32


class SnapshotSenhaInvalida(ValueError):
    """Senha errada ou envelope adulterado (a tag do GCM não confere)."""


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("ascii")


def _derivar_chave(senha: str, salt: bytes, iteracoes: int) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=TAMANHO_CHAVE, salt=salt, iterations=iteracoes)
    return kdf.derive(senha.encode("utf-8"))


def serializar(conteudo: dict[str, Any]) -> bytes:
    """JSON UTF-8 compacto e estável (chaves ordenadas)."""
    return json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_rotas(rotas: dict[str, Any]) -> str:
    """SHA-256 do texto claro das rotas (sem `gerado_em`), para `--somente-se-mudou`."""
    return hashlib.sha256(serializar(rotas)).hexdigest()


def cifrar_snapshot(
    conteudo: dict[str, Any],
    senha: str,
    *,
    salt: bytes | None = None,
    iv: bytes | None = None,
    iteracoes: int = KDF_ITERACOES,
) -> dict[str, Any]:
    """Cifra `conteudo` (`{"gerado_em", "rotas"}`) e devolve o envelope JSON.

    `salt`/`iv` só são passados no vetor de teste; em uso normal são aleatórios
    a cada geração (nunca reutilizar o par chave+iv no GCM).
    """
    if not senha:
        raise ValueError("Senha do snapshot vazia.")
    salt = os.urandom(TAMANHO_SALT) if salt is None else salt
    iv = os.urandom(TAMANHO_IV) if iv is None else iv
    if len(salt) != TAMANHO_SALT or len(iv) != TAMANHO_IV:
        raise ValueError("salt deve ter 16 bytes e iv 12 bytes.")

    claro = gzip.compress(serializar(conteudo), mtime=0)
    ct = AESGCM(_derivar_chave(senha, salt, iteracoes)).encrypt(iv, claro, None)
    return {
        "v": VERSAO,
        "kdf": {"alg": KDF_ALG, "iter": iteracoes, "salt": _b64(salt)},
        "cifra": CIFRA_ALG,
        "iv": _b64(iv),
        "ct": _b64(ct),
        "gerado_em": conteudo.get("gerado_em"),
    }


def decifrar_snapshot(envelope: dict[str, Any], senha: str) -> dict[str, Any]:
    """Inverso de `cifrar_snapshot`; lança `SnapshotSenhaInvalida` se a senha não confere."""
    if envelope.get("v") != VERSAO:
        raise ValueError(f"Versão de snapshot não suportada: {envelope.get('v')!r}")
    kdf = envelope["kdf"]
    if kdf.get("alg") != KDF_ALG:
        raise ValueError(f"KDF não suportado: {kdf.get('alg')!r}")
    chave = _derivar_chave(senha, base64.b64decode(kdf["salt"]), int(kdf["iter"]))
    try:
        claro = AESGCM(chave).decrypt(base64.b64decode(envelope["iv"]), base64.b64decode(envelope["ct"]), None)
    except InvalidTag as exc:
        raise SnapshotSenhaInvalida("Senha incorreta ou snapshot corrompido.") from exc
    return json.loads(gzip.decompress(claro).decode("utf-8"))
