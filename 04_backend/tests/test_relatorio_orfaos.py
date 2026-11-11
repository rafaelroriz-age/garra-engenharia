"""Testes do relatório de órfãos em dry-run (DEC-44). Sem banco nem MinIO."""
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.scripts.relatorio_orfaos import gerar_relatorio
from app.services.storage.s3_client import S3StorageClient

AGORA = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


class _Pag:
    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **kw):
        return iter(self._pages)


class _FakeS3:
    def __init__(self, objetos):
        self.objetos = objetos
        self.deletes = []

    def get_paginator(self, name):
        return _Pag([{"Contents": [{"Key": k, "LastModified": m} for k, m in self.objetos]}])

    def delete_object(self, **kw):
        self.deletes.append(kw)

    def delete_objects(self, **kw):
        self.deletes.append(kw)


def _storage(fake):
    cli = S3StorageClient.__new__(S3StorageClient)
    cli._bucket = "bkt"
    cli._client = fake
    return cli


def _cenario():
    return _FakeS3(
        [
            ("fotos/novo.jpg", AGORA - timedelta(hours=2)),
            ("fotos/antigo-orfao.jpg", AGORA - timedelta(hours=48)),
            ("fotos/antigo-vinculado.jpg", AGORA - timedelta(hours=72)),
        ]
    )


def test_so_antigo_sem_vinculo_aparece_e_nada_e_apagado():
    fake = _cenario()
    texto, orfaos = gerar_relatorio(
        _storage(fake), lambda: {"fotos/antigo-vinculado.jpg"}, "fotos/", 24, agora=AGORA
    )
    assert [o[0] for o in orfaos] == ["fotos/antigo-orfao.jpg"]
    assert "fotos/antigo-orfao.jpg" in texto
    assert "fotos/novo.jpg" not in texto
    assert "fotos/antigo-vinculado.jpg" not in texto
    assert "Total de órfãos: 1" in texto
    assert fake.deletes == []


def test_sem_orfaos_relatorio_vazio():
    fake = _cenario()
    vinc = {"fotos/novo.jpg", "fotos/antigo-orfao.jpg", "fotos/antigo-vinculado.jpg"}
    texto, orfaos = gerar_relatorio(_storage(fake), lambda: vinc, "fotos/", 24, agora=AGORA)
    assert orfaos == []
    assert "Total de órfãos: 0" in texto
    assert fake.deletes == []


def test_idade_minima_configuravel():
    fake = _cenario()
    _, orfaos = gerar_relatorio(_storage(fake), lambda: set(), "fotos/", 1, agora=AGORA)
    assert len(orfaos) == 3


def test_script_nao_tem_chamada_de_exclusao():
    src = Path(__file__).parents[1].joinpath("app/scripts/relatorio_orfaos.py").read_text(encoding="utf-8")
    assert ".delete(" not in src
    assert "delete_object" not in src
