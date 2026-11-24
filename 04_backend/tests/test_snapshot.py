"""Testes do snapshot cifrado da leitura da equipe (DEC-57, T81).

- Cifra: ida e volta, senha errada, e o vetor de teste fixo publicado em
  `00_docs/backlog-auto/snapshot-cifrado.md` (o front, T83, decifra o mesmo vetor).
- Coleta: contra o PostgreSQL de teste com o seed de demonstração (prefixo
  `SNAPTESTE`, storage em memória), via ASGITransport.
- Script: `--somente-se-mudou` e validação da senha, com a coleta substituída.
"""
import json
import uuid

import pytest
from sqlalchemy import delete, select

from app.main import app
from app.models import Usuario
from app.scripts import gerar_snapshot, seed_demo
from app.scripts.seed_demo import Prefixos
from app.services.snapshot import (
    ResultadoColeta,
    SnapshotSenhaInvalida,
    cifrar_snapshot,
    coletar_rotas,
    decifrar_snapshot,
    garantir_usuario_servico,
    hash_rotas,
)
from app.services.snapshot.coletor import SnapshotUsuarioInvalido
from tests.conftest import TestSessionLocal

PREF = Prefixos(base="SNAPTESTE")

# Vetor de teste fixo (copiado no Doc da tarefa; não altere sem atualizar o Doc e o T83).
VETOR_SENHA = "garra-vetor-de-teste-2026"
VETOR_CLARO = {
    "gerado_em": "2026-11-17T12:00:00+00:00",
    "rotas": {
        "/api/v1/auth/me": {
            "email": "snapshot.servico@garra-engenharia.com.br",
            "nome": "Snapshot de leitura (serviço)",
            "role": "auditor",
        },
        "/api/v1/edificacoes?page=1&page_size=10": {"items": [], "page": 1, "page_size": 10, "total": 0},
    },
}
VETOR_ENVELOPE = {
    "v": 1,
    "kdf": {"alg": "PBKDF2-SHA256", "iter": 600000, "salt": "AAECAwQFBgcICQoLDA0ODw=="},
    "cifra": "AES-256-GCM",
    "iv": "ZGVmZ2hpamtsbW5v",
    "ct": (
        "LS0+PjfaRdi0+WO5lD5DRc89s4wxV+TCZUANmOA1UrzmHO7qjPSmqwGI00eU2I4LxAKVDSu0g7qQuJolJdIMME/Tn09fMmxT"
        "MFfPmLfGkKEfK4UHX9UMhYF7P9CYWpH+G6Rk6jMm3mnUj3Hp5TXjORUECdJwyZ7tqpCUxp7gKbLItpUgf0tbxXswcoXkCE80"
        "VxlUnde+/aYeJAg/KWcCmOO0uh9Hn5g2kLV+ZObQBr9p5b7EnGq4p30F8P/2X76dmv3ZSjKeP4HXllsuiyODZUnx9ONVSGBx"
        "8u7hTDScEnCZUnQ8BM3X0Ot/ug=="
    ),
    "gerado_em": "2026-11-17T12:00:00+00:00",
}

# Iterações baixas só nos testes que não validam o vetor, para não gastar 600k a cada caso.
_ITER_RAPIDO = 1000


# --- Cifra -----------------------------------------------------------------------


def test_cifrar_e_decifrar_ida_e_volta():
    conteudo = {"gerado_em": "2026-01-01T00:00:00+00:00", "rotas": {"/api/v1/x?a=1": {"ç": [1, "ã"]}}}
    envelope = cifrar_snapshot(conteudo, "senha-da-equipe-longa", iteracoes=_ITER_RAPIDO)

    assert envelope["v"] == 1 and envelope["kdf"]["alg"] == "PBKDF2-SHA256"
    assert envelope["gerado_em"] == conteudo["gerado_em"]
    assert "ç" not in json.dumps(envelope)  # nada do texto claro vaza no envelope
    assert decifrar_snapshot(envelope, "senha-da-equipe-longa") == conteudo


def test_salt_e_iv_aleatorios_a_cada_geracao():
    a = cifrar_snapshot({"rotas": {}}, "s" * 16, iteracoes=_ITER_RAPIDO)
    b = cifrar_snapshot({"rotas": {}}, "s" * 16, iteracoes=_ITER_RAPIDO)
    assert a["kdf"]["salt"] != b["kdf"]["salt"] and a["iv"] != b["iv"] and a["ct"] != b["ct"]


def test_senha_errada_falha():
    envelope = cifrar_snapshot({"rotas": {"/a": 1}}, "senha-certa-da-equipe", iteracoes=_ITER_RAPIDO)
    with pytest.raises(SnapshotSenhaInvalida):
        decifrar_snapshot(envelope, "senha-errada-da-equipe")


def test_envelope_adulterado_falha():
    envelope = cifrar_snapshot({"rotas": {"/a": 1}}, "senha-certa-da-equipe", iteracoes=_ITER_RAPIDO)
    ct = bytearray(envelope["ct"].encode())
    ct[5] = ord("A") if ct[5] != ord("A") else ord("B")
    with pytest.raises(SnapshotSenhaInvalida):
        decifrar_snapshot({**envelope, "ct": ct.decode()}, "senha-certa-da-equipe")


def test_vetor_de_teste_fixo_decifra():
    assert decifrar_snapshot(VETOR_ENVELOPE, VETOR_SENHA) == VETOR_CLARO
    with pytest.raises(SnapshotSenhaInvalida):
        decifrar_snapshot(VETOR_ENVELOPE, VETOR_SENHA + "x")


def test_vetor_de_teste_recifra_igual_com_salt_e_iv_fixos():
    envelope = cifrar_snapshot(VETOR_CLARO, VETOR_SENHA, salt=bytes(range(16)), iv=bytes(range(100, 112)))
    # O `ct` não é comparado byte a byte: a saída do gzip varia com a plataforma/zlib.
    assert {k: v for k, v in envelope.items() if k != "ct"} == {k: v for k, v in VETOR_ENVELOPE.items() if k != "ct"}
    assert decifrar_snapshot(envelope, VETOR_SENHA) == VETOR_CLARO


def test_hash_rotas_ignora_ordem_das_chaves():
    assert hash_rotas({"/a": {"x": 1, "y": 2}, "/b": []}) == hash_rotas({"/b": [], "/a": {"y": 2, "x": 1}})
    assert hash_rotas({"/a": 1}) != hash_rotas({"/a": 2})


# --- Coleta ----------------------------------------------------------------------


class _StorageFake:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def upload(self, key, data, content_type="application/octet-stream"):
        self.objetos[key] = data
        return key

    def delete(self, key):
        self.objetos.pop(key, None)


@pytest.fixture
async def semeado():
    storage = _StorageFake()
    email = f"snapshot-{uuid.uuid4().hex[:8]}@garra-engenharia.com.br"
    async with TestSessionLocal() as db:
        await seed_demo.limpar(db, PREF, storage)
        resumo = await seed_demo.seed(db, storage, PREF)
    yield resumo, email
    async with TestSessionLocal() as db:
        await seed_demo.limpar(db, PREF, storage)
        await db.execute(delete(Usuario).where(Usuario.email == email))
        await db.commit()


async def test_coleta_contem_rotas_esperadas(semeado):
    resumo, email = semeado
    resultado = await coletar_rotas(app, TestSessionLocal, email_servico=email)
    rotas = resultado.rotas

    async with TestSessionLocal() as db:
        servico = await db.scalar(select(Usuario).where(Usuario.email == email))
    assert servico is not None and servico.role == "auditor" and servico.ativo

    for fixa in (
        "/api/v1/auth/me",
        "/api/v1/ia/uso",
        "/api/v1/sistemas-prediais",
        "/api/v1/gabarito/tipos-anomalia",
        "/api/v1/gabarito/tipos-falha",
        "/api/v1/gabarito/localizacoes",
        "/api/v1/responsaveis",
        "/api/v1/edificacoes",
        "/api/v1/edificacoes?page=1&page_size=100",
        "/api/v1/edificacoes?page=1&page_size=10",
        "/api/v1/contratos?page=1&page_size=10",
    ):
        assert fixa in rotas, fixa
    assert rotas["/api/v1/auth/me"]["email"] == email

    edificacao = next(
        e for e in rotas["/api/v1/edificacoes?page=1&page_size=100"]["items"] if e["nome"].startswith(PREF.nome)
    )
    eid = edificacao["id"]
    assert f"/api/v1/edificacoes/{eid}" in rotas
    assert f"/api/v1/edificacoes/{eid}/dashboard" in rotas
    assert f"/api/v1/contratos?page=1&page_size=10&edificacao_id={eid}" in rotas
    assert "/api/v1/contratos?page=1&page_size=10&tipo_servico=RFO" in rotas

    for tipo, iid in resumo.inspecoes.items():
        assert f"/api/v1/inspecoes/{iid}" in rotas
        assert f"/api/v1/inspecoes/{iid}/relatorios" in rotas
        assert f"/api/v1/inspecoes/{iid}/conteudo/{tipo.lower()}" in rotas
        assert f"/api/v1/inspecoes/{iid}/ocorrencias" in rotas

    rfo = rotas[f"/api/v1/inspecoes/{resumo.inspecoes['RFO']}"]
    assert rfo["visitas"]
    for visita in rfo["visitas"]:
        for suf in ("", "/mao-obra", "/medicoes"):
            assert f"/api/v1/visitas/{visita['id']}{suf}" in rotas

    ltip = resumo.inspecoes["LTIP"]
    ocorrencias = rotas[f"/api/v1/inspecoes/{ltip}/ocorrencias"]["items"]
    assert ocorrencias
    for o in ocorrencias:
        assert f"/api/v1/ocorrencias/{o['id']}" in rotas
        assert f"/api/v1/inspecoes/{ltip}/ocorrencias?sistema_id={o['sistema_id']}" in rotas
        assert f"/api/v1/inspecoes/{ltip}/ocorrencias?grau_risco={o['grau_risco']}" in rotas
        assert (
            f"/api/v1/inspecoes/{ltip}/ocorrencias?sistema_id={o['sistema_id']}&grau_risco={o['grau_risco']}"
            in rotas
        )

    # Nada de portal, login, downloads, fotos ou documentos.
    for chave in rotas:
        assert chave.startswith("/api/v1/")
        assert "/portal" not in chave and "/auth/login" not in chave
        assert "/download" not in chave and "/fotos/" not in chave and "/documentos" not in chave
    assert not [c for c in resultado.falhas if PREF.base in c]

    # O snapshot inteiro cifra e volta igual.
    conteudo = {"gerado_em": "2026-11-17T00:00:00+00:00", "rotas": rotas}
    envelope = cifrar_snapshot(conteudo, "senha-da-equipe-longa", iteracoes=_ITER_RAPIDO)
    assert decifrar_snapshot(envelope, "senha-da-equipe-longa") == json.loads(json.dumps(conteudo))


async def test_usuario_servico_reutilizado_e_nunca_alterado():
    email = f"snapshot-{uuid.uuid4().hex[:8]}@garra-engenharia.com.br"
    try:
        async with TestSessionLocal() as db:
            primeiro = await garantir_usuario_servico(db, email)
            hash_original = primeiro.senha_hash
        async with TestSessionLocal() as db:
            segundo = await garantir_usuario_servico(db, email)
        assert segundo.id == primeiro.id and segundo.senha_hash == hash_original

        async with TestSessionLocal() as db:
            usuario = await db.scalar(select(Usuario).where(Usuario.email == email))
            usuario.role = "cliente"
            await db.commit()
        async with TestSessionLocal() as db:
            with pytest.raises(SnapshotUsuarioInvalido):
                await garantir_usuario_servico(db, email)
            assert (await db.scalar(select(Usuario).where(Usuario.email == email))).role == "cliente"
    finally:
        async with TestSessionLocal() as db:
            await db.execute(delete(Usuario).where(Usuario.email == email))
            await db.commit()


# --- Script ----------------------------------------------------------------------


def _coleta_fake(rotas: dict):
    async def _fake(_app, _factory, **_kw):
        return ResultadoColeta(rotas=dict(rotas))

    return _fake


def test_script_somente_se_mudou(tmp_path, monkeypatch):
    senha = "senha-da-equipe-com-16+"
    monkeypatch.setenv("SNAPSHOT_SENHA", senha)
    monkeypatch.setattr(gerar_snapshot, "cifrar_snapshot", lambda c, s: cifrar_snapshot(c, s, iteracoes=_ITER_RAPIDO))
    saida = tmp_path / "snapshot.enc"

    monkeypatch.setattr(gerar_snapshot, "coletar_rotas", _coleta_fake({"/api/v1/a": 1}))
    assert gerar_snapshot.main(["--saida", str(saida), "--somente-se-mudou"]) == gerar_snapshot.SAIDA_OK
    envelope = json.loads(saida.read_text(encoding="utf-8"))
    assert decifrar_snapshot(envelope, senha)["rotas"] == {"/api/v1/a": 1}
    assert (tmp_path / "snapshot.enc.sha256").read_text().strip() == hash_rotas({"/api/v1/a": 1})

    # Mesmo conteúdo (gerado_em muda, mas não entra no hash): não grava, código 3.
    antes = saida.read_bytes()
    assert gerar_snapshot.main(["--saida", str(saida), "--somente-se-mudou"]) == gerar_snapshot.SAIDA_SEM_MUDANCA
    assert saida.read_bytes() == antes

    # Sem a flag, grava de novo mesmo sem mudança; com mudança, grava.
    assert gerar_snapshot.main(["--saida", str(saida)]) == gerar_snapshot.SAIDA_OK
    monkeypatch.setattr(gerar_snapshot, "coletar_rotas", _coleta_fake({"/api/v1/a": 2}))
    assert gerar_snapshot.main(["--saida", str(saida), "--somente-se-mudou"]) == gerar_snapshot.SAIDA_OK
    assert decifrar_snapshot(json.loads(saida.read_text(encoding="utf-8")), senha)["rotas"] == {"/api/v1/a": 2}


def test_script_recusa_senha_curta(tmp_path, monkeypatch):
    monkeypatch.setenv("SNAPSHOT_SENHA", "curta")
    assert gerar_snapshot.main(["--saida", str(tmp_path / "s.enc")]) == gerar_snapshot.SAIDA_CONFIG
    assert not (tmp_path / "s.enc").exists()
