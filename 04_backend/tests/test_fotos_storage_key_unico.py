"""Unicidade de `fotos.storage_key` (R-15): API devolve 409 e o banco rejeita (IntegrityError).

Requer PostgreSQL e MinIO reais (`05_infra/docker-compose.yml`), como `tests/test_fotos.py`.
"""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Foto
from tests.test_fotos import (  # noqa: F401 - fixtures reutilizadas
    _cleanup_foto,
    _imagem_png_bytes,
    auth_headers,
    client,
    ocorrencia,
    visita,
)


def test_segundo_vinculo_da_mesma_chave_retorna_409(auth_headers, ocorrencia, visita):
    upload = client.post(
        "/api/v1/fotos/upload",
        files={"arquivo": ("foto.png", _imagem_png_bytes(), "image/png")},
        headers=auth_headers,
    ).json()
    payload = {"storage_key": upload["storage_key"], "origem": "upload_manual"}

    primeiro = client.post(f"/api/v1/ocorrencias/{ocorrencia.id}/fotos", json=payload, headers=auth_headers)
    assert primeiro.status_code == 201

    segundo = client.post(f"/api/v1/visitas/{visita.id}/fotos", json=payload, headers=auth_headers)
    assert segundo.status_code == 409
    assert segundo.headers["content-type"].startswith("application/problem+json")

    _cleanup_foto(uuid.UUID(primeiro.json()["id"]))


@pytest.mark.asyncio
async def test_banco_rejeita_storage_key_duplicada(db_session):
    chave = f"fotos/{uuid.uuid4()}.png"
    db_session.add(Foto(storage_key=chave, origem="upload_manual"))
    await db_session.commit()
    try:
        db_session.add(Foto(storage_key=chave, origem="upload_manual"))
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()
    finally:
        await db_session.execute(Foto.__table__.delete().where(Foto.storage_key == chave))
        await db_session.commit()
