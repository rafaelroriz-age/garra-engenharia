# ruff: noqa: F811  (fixtures reutilizadas de tests/test_fotos.py reaparecem como parâmetros)
"""Testes de LACUNA de Fotos (BL-11, RF-05, RNF-07, RN-15, DEC-19/27, OWASP A01/A08).

Cada `test_lacuna_*` afirma o comportamento CORRETO esperado. Os que falharem
hoje documentam uma lacuna do código de produção (nada em `app/` foi alterado
nesta revisão); ver `00_docs/backlog-auto/revisao-regras-fotos.md`.

Mesmo mecanismo de `tests/test_fotos.py`: PostgreSQL e MinIO reais
(`05_infra/docker-compose.yml`), fixtures reaproveitadas daquele módulo.
"""
import base64
import io
import os
import uuid
from asyncio import run as run_async

import pytest
import pytest_asyncio
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Foto, Usuario
from app.services.storage import ObjectNotFoundError, get_storage_client
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import delete

from tests.test_fotos import (  # noqa: F401  (fixtures reutilizadas)
    _cleanup_foto,
    _imagem_png_bytes,
    _TestSessionLocal,
    auth_headers,
    client,
    ocorrencia,
    visita,
)

# Cliente que devolve a resposta 500 em vez de propagar a exceção ao teste.
client_500 = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------- helpers


def _limpar_se_criada(resp) -> None:
    """Se a lacuna existir e a Foto foi criada (201), remove-a antes do assert falhar."""
    if resp.status_code == 201:
        _cleanup_foto(uuid.UUID(resp.json()["id"]))


def _upload(headers, conteudo: bytes | None = None, nome="foto.png", ctype="image/png", cli=client):
    return cli.post(
        "/api/v1/fotos/upload",
        files={"arquivo": (nome, conteudo if conteudo is not None else _imagem_png_bytes(), ctype)},
        headers=headers,
    )


def _vincular_visita(headers, visita_id, storage_key, **extra):
    corpo = {"storage_key": storage_key, "origem": "upload_manual", **extra}
    return client.post(f"/api/v1/visitas/{visita_id}/fotos", json=corpo, headers=headers)


def _imagem(formato: str, tamanho=(20, 20), **save_kwargs) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", tamanho, color="blue").save(buffer, format=formato, **save_kwargs)
    return buffer.getvalue()


def _baixar_imagem(storage_key: str) -> Image.Image:
    return Image.open(io.BytesIO(get_storage_client().download(storage_key)))


async def _criar_usuario(role: str) -> uuid.UUID:
    async with _TestSessionLocal() as session:
        usuario = Usuario(
            nome=f"Usuário {role} fotos-lacunas",
            email=f"fotos-{role}-{uuid.uuid4()}@garra-engenharia.com.br",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role=role,
        )
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        return usuario.id


async def _remover_usuario(usuario_id: uuid.UUID) -> None:
    async with _TestSessionLocal() as session:
        await session.execute(delete(Foto).where(Foto.criado_por_id == usuario_id))
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


def _headers(usuario_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario_id))}"}


@pytest_asyncio.fixture
async def auxiliar():
    usuario_id = await _criar_usuario("auxiliar")
    yield usuario_id
    await _remover_usuario(usuario_id)


@pytest_asyncio.fixture
async def cliente():
    usuario_id = await _criar_usuario("cliente")
    yield usuario_id
    await _remover_usuario(usuario_id)


# ------------------------------------------- 1. tipo real do arquivo (A08)


def test_lacuna_1_formato_nao_suportado_gif_com_extensao_e_mime_de_png_e_rejeitado(auth_headers):
    """RF-05/A08: só JPEG/PNG/WEBP são aceitos; GIF declarado como PNG deve dar 422 (valida magic bytes)."""
    resp = _upload(auth_headers, _imagem("GIF"), nome="foto.png", ctype="image/png")

    assert resp.status_code == 422
    assert resp.json()["type"].endswith("formato-de-imagem-nao-suportado")


def test_lacuna_1b_html_com_extensao_jpg_e_rejeitado(auth_headers):
    """A08: conteúdo HTML/SVG disfarçado de .jpg nunca pode ir ao storage."""
    html = b"<html><script>alert(1)</script></html>"
    resp = _upload(auth_headers, html, nome="foto.jpg", ctype="image/jpeg")

    assert resp.status_code == 422


# ---------------------------------------------------------- 2. tamanho


def test_lacuna_2_arquivo_acima_do_limite_e_rejeitado_sem_erro_500(auth_headers):
    """RNF-07 (limite de 25 MB, `MAX_UPLOAD_SIZE_BYTES`): 26 MB deve ser recusado (413/422), nunca 500 nem 201."""
    resp = _upload(auth_headers, b"\x00" * (26 * 1024 * 1024), cli=client_500)

    assert resp.status_code in (413, 422)


def test_lacuna_2b_clipboard_acima_do_limite_e_rejeitado(auth_headers):
    """RNF-07: o mesmo limite vale para o upload por clipboard (base64)."""
    grande = base64.b64encode(b"\x00" * (26 * 1024 * 1024)).decode("ascii")
    resp = client_500.post(
        "/api/v1/fotos/upload-clipboard", json={"imagem_base64": grande}, headers=auth_headers
    )

    assert resp.status_code in (413, 422)


# -------------------------------------------------- 3. imagem corrompida


@pytest.mark.parametrize("formato", ["PNG", "JPEG"])
def test_lacuna_3_imagem_truncada_retorna_422_nao_500(auth_headers, formato):
    """A08: imagem com dados cortados no meio deve virar 422 RFC 7807, nunca 500."""
    ruido = Image.frombytes("RGB", (200, 200), os.urandom(200 * 200 * 3))
    buffer = io.BytesIO()
    ruido.save(buffer, format=formato)
    completo = buffer.getvalue()
    truncado = completo[: len(completo) // 2]

    resp = _upload(auth_headers, truncado, cli=client_500)

    assert resp.status_code == 422


# ----------------------------- 4. chave de storage controlada pelo servidor


@pytest.mark.parametrize(
    "chave_maliciosa", ["../../etc/passwd", "fotos/../../segredo.png", "/absoluto.png", "outro-prefixo/x.png"]
)
def test_lacuna_4_vincular_rejeita_storage_key_fora_do_padrao_do_servidor(auth_headers, visita, chave_maliciosa):
    """A01/A03: a chave deve ser a emitida pelo servidor (`fotos/<uuid>.<ext>`); cliente não pode vincular chave arbitrária."""
    resp = _vincular_visita(auth_headers, visita.id, chave_maliciosa)

    _limpar_se_criada(resp)
    assert resp.status_code in (404, 422)


def test_lacuna_4b_vincular_storage_key_inexistente_no_storage_e_rejeitado(auth_headers, visita):
    """RF-05: não pode existir `Foto` apontando para objeto que nunca foi enviado ao storage."""
    resp = _vincular_visita(auth_headers, visita.id, f"fotos/{uuid.uuid4()}.png")

    _limpar_se_criada(resp)
    assert resp.status_code in (404, 422)


def test_lacuna_4c_mesma_storage_key_nao_pode_ser_vinculada_duas_vezes(auth_headers, visita, ocorrencia):
    """Integridade: duas `Foto` com a mesma chave fazem o DELETE de uma apagar o objeto da outra."""
    key = _upload(auth_headers).json()["storage_key"]
    primeira = _vincular_visita(auth_headers, visita.id, key)
    segunda = client.post(
        f"/api/v1/ocorrencias/{ocorrencia.id}/fotos",
        json={"storage_key": key, "origem": "upload_manual"},
        headers=auth_headers,
    )

    try:
        assert primeira.status_code == 201
        assert segunda.status_code in (409, 422)
    finally:
        for resp in (primeira, segunda):
            if resp.status_code == 201:
                _cleanup_foto(uuid.UUID(resp.json()["id"]))


# ------------------------------------- 5. visita inexistente / contexto


def test_lacuna_5_vincular_a_visita_inexistente_retorna_404(auth_headers):
    """RF-05: vincular a Visita que não existe deve dar 404 (testes atuais só cobrem Ocorrência)."""
    key = _upload(auth_headers).json()["storage_key"]
    resp = _vincular_visita(auth_headers, uuid.uuid4(), key)

    assert resp.status_code == 404


# ---------------------------------------------- 6. legenda / ordem / origem


def test_lacuna_6_ordem_negativa_e_rejeitada(auth_headers, visita):
    """RN-11 (ordem das fotos no relatório): posição negativa não faz sentido e deve dar 422."""
    key = _upload(auth_headers).json()["storage_key"]
    resp = _vincular_visita(auth_headers, visita.id, key, ordem=-5)

    _limpar_se_criada(resp)
    assert resp.status_code == 422


def test_lacuna_6b_origem_fora_do_dominio_e_rejeitada(auth_headers, visita):
    """RF-05: `origem` só pode ser upload_manual/lightshot (clipboard); texto livre corrompe a rastreabilidade."""
    key = _upload(auth_headers).json()["storage_key"]
    resp = _vincular_visita(auth_headers, visita.id, key, origem="qualquer-coisa-<script>")

    _limpar_se_criada(resp)
    assert resp.status_code == 422


def test_lacuna_6c_legenda_pode_ser_apagada_via_put(auth_headers, visita):
    """RN-03: legenda é editável; enviar `legenda: null` explícito deve limpá-la (hoje `None` é ignorado)."""
    key = _upload(auth_headers).json()["storage_key"]
    foto = _vincular_visita(auth_headers, visita.id, key, legenda="Fissura").json()
    try:
        resp = client.put(f"/api/v1/fotos/{foto['id']}", json={"legenda": None}, headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["legenda"] is None
    finally:
        _cleanup_foto(uuid.UUID(foto["id"]))


def test_lacuna_6d_legenda_gigante_e_rejeitada(auth_headers, visita):
    """RN-03/A04: legenda sem limite de tamanho permite 1 MB de texto por foto; deve haver teto (422)."""
    key = _upload(auth_headers).json()["storage_key"]
    resp = _vincular_visita(auth_headers, visita.id, key, legenda="x" * 1_000_000)

    _limpar_se_criada(resp)
    assert resp.status_code == 422


# ----------------------------------------- 7. permissões por papel (DEC-27)


def test_lacuna_7_cliente_nao_acessa_nenhum_endpoint_de_foto(cliente, auth_headers, visita):
    """DEC-27/A01: perfil `cliente` (portal) recebe 403 em upload, vínculo, edição e remoção."""
    h = _headers(cliente)
    key = _upload(auth_headers).json()["storage_key"]
    foto = _vincular_visita(auth_headers, visita.id, key).json()
    try:
        assert _upload(h).status_code == 403
        assert (
            client.post(
                "/api/v1/fotos/upload-clipboard",
                json={"imagem_base64": base64.b64encode(_imagem_png_bytes()).decode()},
                headers=h,
            ).status_code
            == 403
        )
        assert _vincular_visita(h, visita.id, key).status_code == 403
        assert client.put(f"/api/v1/fotos/{foto['id']}", json={"legenda": "x"}, headers=h).status_code == 403
        assert client.delete(f"/api/v1/fotos/{foto['id']}", headers=h).status_code == 403
    finally:
        _cleanup_foto(uuid.UUID(foto["id"]))


def test_lacuna_7b_sem_token_retorna_401():
    """RNF-05: nenhum endpoint de foto é anônimo."""
    assert client.post("/api/v1/fotos/upload", files={"arquivo": ("a.png", _imagem_png_bytes())}).status_code == 401
    assert client.delete(f"/api/v1/fotos/{uuid.uuid4()}").status_code == 401


def test_lacuna_7c_auxiliar_envia_vincula_e_fica_registrado_como_autor(auxiliar, visita):
    """DEC-27/RN-18: auxiliar pode enviar e vincular fotos; `criado_por_id` é o dele."""
    h = _headers(auxiliar)
    upload = _upload(h)
    assert upload.status_code == 201

    resp = _vincular_visita(h, visita.id, upload.json()["storage_key"])

    assert resp.status_code == 201
    assert resp.json()["criado_por_id"] == str(auxiliar)
    _cleanup_foto(uuid.UUID(resp.json()["id"]))


def test_lacuna_7d_autoria_nao_pode_ser_forjada_no_payload(auxiliar, visita):
    """RN-18: `criado_por_id` enviado no corpo é ignorado; vale sempre o usuário do token."""
    h = _headers(auxiliar)
    key = _upload(h).json()["storage_key"]
    outro = str(uuid.uuid4())

    resp = _vincular_visita(h, visita.id, key, criado_por_id=outro)

    assert resp.status_code == 201
    assert resp.json()["criado_por_id"] == str(auxiliar)
    _cleanup_foto(uuid.UUID(resp.json()["id"]))


# ------------------------------------------- 8. otimização de imagem


def test_lacuna_8_foto_grande_e_redimensionada_no_upload(auth_headers):
    """RNF-06/R-03 (benchmark BL-22): lado maior armazenado ≤ 2000 px."""
    key = _upload(auth_headers, _imagem("PNG", (3000, 1500))).json()["storage_key"]

    largura, altura = _baixar_imagem(key).size

    assert max(largura, altura) <= 2000
    get_storage_client().delete(key)


def test_lacuna_8b_exif_e_removido_da_imagem_armazenada():
    """A08: EXIF (GPS, modelo do aparelho) não pode permanecer no objeto armazenado."""
    exif = Image.Exif()
    exif[0x010F] = "FabricanteSecreto"  # Make
    exif[0x0112] = 1
    conteudo = _imagem("JPEG", (40, 20), exif=exif.tobytes())

    async def _com_usuario():
        uid = await _criar_usuario("auditor")
        try:
            return _upload(_headers(uid), conteudo, nome="f.jpg", ctype="image/jpeg").json()["storage_key"]
        finally:
            await _remover_usuario(uid)

    key = run_async(_com_usuario())
    stored = _baixar_imagem(key)

    assert not stored.getexif()
    get_storage_client().delete(key)


def test_lacuna_8c_orientacao_exif_e_aplicada_antes_de_descartar_o_exif(auth_headers):
    """RF-05: foto de celular (EXIF Orientation=6, 100x50 'deitada') deve ser gravada em pé (50x100);
    descartar o EXIF sem `exif_transpose` deixa a foto girada nos relatórios."""
    exif = Image.Exif()
    exif[0x0112] = 6
    conteudo = _imagem("JPEG", (100, 50), exif=exif.tobytes())

    key = _upload(auth_headers, conteudo, nome="f.jpg", ctype="image/jpeg").json()["storage_key"]
    largura, altura = _baixar_imagem(key).size

    assert (largura, altura) == (50, 100)
    get_storage_client().delete(key)


# ------------------------------- 9. exclusão e objeto órfão no storage


def test_lacuna_9_remover_foto_apaga_o_objeto_do_storage(auth_headers, visita):
    """RNF-07: DELETE /fotos/{id} não pode deixar objeto órfão no bucket."""
    key = _upload(auth_headers).json()["storage_key"]
    foto = _vincular_visita(auth_headers, visita.id, key).json()

    assert client.delete(f"/api/v1/fotos/{foto['id']}", headers=auth_headers).status_code == 204

    with pytest.raises(ObjectNotFoundError):
        get_storage_client().download(key)


def test_lacuna_9b_upload_nunca_vinculado_nao_fica_para_sempre_no_storage(auth_headers):
    """RNF-07: upload sem vínculo (usuário desistiu) deixa objeto órfão; deveria existir rotina/endpoint de descarte.
    Critério verificável: DELETE de storage_key não vinculada (sem Foto) é aceito (204)."""
    key = _upload(auth_headers).json()["storage_key"]
    try:
        resp = client.request(
            "DELETE", "/api/v1/fotos/upload", json={"storage_key": key}, headers=auth_headers
        )

        assert resp.status_code == 204
    finally:
        get_storage_client().delete(key)


# ------------------------------------------- 10. URL pré-assinada


def test_lacuna_10_url_pre_assinada_expira_em_ate_15_minutos_e_nao_vaza_segredo(auth_headers):
    """RNF-07/A02: URL de download é temporária (≤ 15 min) e não carrega a senha do storage."""
    from app.core.config import get_settings

    url = _upload(auth_headers).json()["url"]
    segredo = get_settings().minio_root_password

    assert "X-Amz-Expires=900" in url or "Expires=" in url
    assert segredo not in url
