"""Testes do `S3StorageClient` com cliente S3 falso (BL-07, fluxo de legendas/
artefatos de IA). Não exigem MinIO nem PostgreSQL."""
import pytest
from botocore.exceptions import ClientError

from app.services.storage.s3_client import S3StorageClient


class _FakePaginator:
    def __init__(self, pages):
        self._pages = pages
        self.kwargs = None

    def paginate(self, **kwargs):
        self.kwargs = kwargs
        return iter(self._pages)


class _FakeS3:
    def __init__(self, keys=(), pages=None):
        self.keys = set(keys)
        self.paginator = _FakePaginator(
            pages if pages is not None else [{"Contents": [{"Key": k} for k in sorted(keys)]}]
        )
        self.presign_args = None

    def head_object(self, Bucket, Key):
        if Key not in self.keys:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {}

    def get_paginator(self, name):
        assert name == "list_objects_v2"
        return self.paginator

    def generate_presigned_url(self, op, Params, ExpiresIn):
        self.presign_args = (op, Params, ExpiresIn)
        return "http://fake/url"


def _client(fake: _FakeS3) -> S3StorageClient:
    cli = S3StorageClient.__new__(S3StorageClient)  # evita boto3/bucket real
    cli._bucket = "bkt"
    cli._client = fake
    return cli


def test_exists_true_e_false():
    cli = _client(_FakeS3(keys={"fotos/a.jpg"}))
    assert cli.exists("fotos/a.jpg") is True
    assert cli.exists("fotos/b.jpg") is False
    with pytest.raises(ValueError):
        cli.exists("")


def test_exists_propaga_outros_erros():
    class _Boom(_FakeS3):
        def head_object(self, Bucket, Key):
            raise ClientError({"Error": {"Code": "403"}}, "HeadObject")

    with pytest.raises(ClientError):
        _client(_Boom()).exists("x")


def test_list_keys_pagina_e_usa_prefixo():
    fake = _FakeS3(pages=[{"Contents": [{"Key": "ia/1.png"}]}, {}, {"Contents": [{"Key": "ia/2.png"}]}])
    assert _client(fake).list_keys("ia/") == ["ia/1.png", "ia/2.png"]
    assert fake.paginator.kwargs == {"Bucket": "bkt", "Prefix": "ia/"}


def test_listar_orfaos_nao_apaga_e_devolve_sem_registro():
    fake = _FakeS3(keys={"ia/1.png", "ia/2.png", "ia/3.png"})
    fake.delete_object = lambda **kw: pytest.fail("listar_orfaos não pode apagar")
    assert _client(fake).listar_orfaos(["ia/1.png", "ia/9.png"], prefix="ia/") == ["ia/2.png", "ia/3.png"]


def test_presigned_url_expiracao_curta():
    fake = _FakeS3()
    assert _client(fake).generate_presigned_url("ia/1.png", 60) == "http://fake/url"
    assert fake.presign_args == ("get_object", {"Bucket": "bkt", "Key": "ia/1.png"}, 60)
    with pytest.raises(ValueError):
        _client(fake).generate_presigned_url("ia/1.png", 0)
