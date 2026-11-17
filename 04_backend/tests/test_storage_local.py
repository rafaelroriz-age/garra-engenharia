"""Storage em disco local + download assinado (DEC-57). Sem banco: usa tmp_path."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.storage import ObjectNotFoundError, get_storage_client
from app.services.storage.local_client import LocalStorageClient, assinar_token, request_base_url


@pytest.fixture
def storage(tmp_path):
    return LocalStorageClient(root=tmp_path / "store")


@pytest.fixture
def client(storage):
    app.dependency_overrides[get_storage_client] = lambda: storage
    yield TestClient(app)
    app.dependency_overrides.pop(get_storage_client, None)


def test_ida_e_volta(storage):
    assert storage.upload("fotos/a.jpg", b"abc", "image/jpeg") == "fotos/a.jpg"
    assert storage.download("fotos/a.jpg") == b"abc"
    storage.upload("fotos/a.jpg", b"xyz", "image/jpeg")  # sobrescreve
    assert storage.download("fotos/a.jpg") == b"xyz"
    assert not list(storage._root.rglob(".tmp-*"))


def test_exists_delete_list(storage):
    storage.upload("fotos/a.jpg", b"1", "image/jpeg")
    storage.upload("relatorios/r.pdf", b"2", "application/pdf")
    assert storage.exists("fotos/a.jpg") and not storage.exists("fotos/b.jpg")
    assert storage.list_keys() == ["fotos/a.jpg", "relatorios/r.pdf"]
    assert storage.list_keys("fotos/") == ["fotos/a.jpg"]
    assert [k for k, _ in storage.list_objects("rel")] == ["relatorios/r.pdf"]
    storage.delete("fotos/a.jpg")
    storage.delete("fotos/a.jpg")  # idempotente
    assert not storage.exists("fotos/a.jpg")
    with pytest.raises(ObjectNotFoundError):
        storage.download("fotos/a.jpg")


@pytest.mark.parametrize("key", ["../fora.txt", "a/../../fora.txt", "..", "", "  ", "a/../.."])
def test_traversal_e_chave_invalida_recusados(storage, key):
    with pytest.raises(ValueError):
        storage.upload(key, b"x", "text/plain")
    with pytest.raises(ValueError):
        storage.exists(key)


def test_upload_valida_conteudo_e_tamanho(storage):
    with pytest.raises(ValueError):
        storage.upload("a.jpg", b"", "image/jpeg")
    with pytest.raises(ValueError):
        storage.upload("a.jpg", b"12345", "image/jpeg", max_size_bytes=4)


def test_url_assinada_valida_baixa(storage, client):
    storage.upload("relatorios/r.pdf", b"%PDF-1", "application/pdf")
    url = storage.generate_presigned_url("relatorios/r.pdf", 60)
    assert url.startswith("/api/v1/arquivos/")
    r = client.get(url)
    assert r.status_code == 200
    assert r.content == b"%PDF-1"
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("inline")


def test_url_absoluta_pelo_contexto_do_request(storage):
    tok = request_base_url.set("https://abc.trycloudflare.com")
    try:
        assert storage.generate_presigned_url("a.jpg", 60).startswith(
            "https://abc.trycloudflare.com/api/v1/arquivos/"
        )
    finally:
        request_base_url.reset(tok)


def test_middleware_usa_forwarded_headers(client):
    visto = {}

    @app.get("/__teste_base_url", include_in_schema=False)
    def _rota():
        visto["base"] = request_base_url.get()
        return {}

    client.get(
        "/__teste_base_url",
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "t.trycloudflare.com"},
    )
    assert visto["base"] == "https://t.trycloudflare.com"


def test_token_adulterado_vencido_e_inexistente(storage, client):
    storage.upload("a.jpg", b"x", "image/jpeg")
    token = storage.generate_presigned_url("a.jpg", 60).rsplit("/", 1)[1]
    corpo, mac = token.split(".")
    assert client.get(f"/api/v1/arquivos/{corpo}.{'A' * len(mac)}").status_code == 403
    outro = assinar_token("outro.jpg", 60).split(".")[0]
    assert client.get(f"/api/v1/arquivos/{outro}.{mac}").status_code == 403
    assert client.get("/api/v1/arquivos/lixo").status_code == 403
    assert client.get(f"/api/v1/arquivos/{assinar_token('a.jpg', -1)}").status_code == 403
    assert client.get(f"/api/v1/arquivos/{assinar_token('nao-existe.jpg', 60)}").status_code == 404
    assert client.get(f"/api/v1/arquivos/{assinar_token('../x.jpg', 60)}").status_code == 404
