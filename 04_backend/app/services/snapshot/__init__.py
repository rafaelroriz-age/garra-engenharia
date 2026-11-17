"""Snapshot cifrado da leitura da equipe (DEC-57, T81).

Com o PC do dono desligado, o site estático (GitHub Pages) abre em modo
leitura a partir de `snapshot.enc`: as respostas dos GETs de leitura da equipe,
coletadas em processo (`coletor`) e cifradas com a senha da equipe (`cifra`).
O formato está documentado em `00_docs/backlog-auto/snapshot-cifrado.md`.
"""
from app.services.snapshot.cifra import (
    SnapshotSenhaInvalida,
    cifrar_snapshot,
    decifrar_snapshot,
    hash_rotas,
)
from app.services.snapshot.coletor import (
    EMAIL_SERVICO_PADRAO,
    ResultadoColeta,
    coletar_rotas,
    garantir_usuario_servico,
)

__all__ = [
    "EMAIL_SERVICO_PADRAO",
    "ResultadoColeta",
    "SnapshotSenhaInvalida",
    "cifrar_snapshot",
    "coletar_rotas",
    "decifrar_snapshot",
    "garantir_usuario_servico",
    "hash_rotas",
]
