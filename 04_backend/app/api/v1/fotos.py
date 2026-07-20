"""Endpoints de Foto (BL-11, RF-05, `00_docs/arquitetura.md` Seção 4 e Seção 6).

- `POST /fotos/upload` — upload manual (multipart, Opção B).
- `POST /fotos/upload-clipboard` — upload via clipboard paste em base64 (Opção A).
- `POST /ocorrencias/{id}/fotos` — vincula foto (já enviada ao storage) a uma Ocorrência.
- `POST /visitas/{id}/fotos` — vincula foto a uma Visita.
- `PUT /fotos/{id}` — atualiza legenda/ordem.
- `DELETE /fotos/{id}` — remove vínculo e objeto do storage.

Todos protegidos por `get_current_user` (BL-06). Mitigações OWASP: A08
(reprocessamento Pillow de toda imagem antes de persistir, ver
`app.services.image_processing`) e A10 (nunca aceita URL fornecida pelo
cliente — apenas multipart ou base64 processados localmente).
"""
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Foto, Usuario
from app.schemas.foto import (
    FotoRead,
    FotoUpdatePayload,
    FotoUploadClipboardPayload,
    FotoUploadResponse,
    FotoVincularPayload,
)
from app.services import foto_service
from app.services.storage import get_storage_client
from app.services.storage.base import StorageClient

router = APIRouter(prefix="/api/v1", tags=["fotos"])


@router.post("/fotos/upload", response_model=FotoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_foto(
    arquivo: UploadFile = File(...),
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(get_current_user),
) -> FotoUploadResponse:
    """Upload manual de arquivo de imagem (multipart/form-data) — Opção B (Seção 6)."""
    conteudo = await arquivo.read()
    storage_key, url = await foto_service.upload_arquivo(conteudo, storage)
    return FotoUploadResponse(storage_key=storage_key, url=url)


@router.post(
    "/fotos/upload-clipboard", response_model=FotoUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_foto_clipboard(
    dados: FotoUploadClipboardPayload,
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(get_current_user),
) -> FotoUploadResponse:
    """Upload via clipboard paste (base64) — Opção A (Seção 6), integração Lightshot."""
    storage_key, url = await foto_service.upload_clipboard(dados.imagem_base64, storage)
    return FotoUploadResponse(storage_key=storage_key, url=url)


@router.post(
    "/ocorrencias/{ocorrencia_id}/fotos", response_model=FotoRead, status_code=status.HTTP_201_CREATED
)
async def vincular_foto_a_ocorrencia(
    ocorrencia_id: uuid.UUID,
    dados: FotoVincularPayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> Foto:
    """Vincula uma foto (já enviada via `/fotos/upload*`) a uma Ocorrência, com legenda (RN-03, RN-11)."""
    return await foto_service.vincular_a_ocorrencia(
        db,
        ocorrencia_id,
        storage_key=dados.storage_key,
        legenda=dados.legenda,
        ordem=dados.ordem,
        origem=dados.origem,
    )


@router.post("/visitas/{visita_id}/fotos", response_model=FotoRead, status_code=status.HTTP_201_CREATED)
async def vincular_foto_a_visita(
    visita_id: uuid.UUID,
    dados: FotoVincularPayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> Foto:
    """Vincula uma foto (já enviada via `/fotos/upload*`) a uma Visita de fiscalização."""
    return await foto_service.vincular_a_visita(
        db,
        visita_id,
        storage_key=dados.storage_key,
        legenda=dados.legenda,
        ordem=dados.ordem,
        origem=dados.origem,
    )


@router.put("/fotos/{foto_id}", response_model=FotoRead)
async def atualizar_foto(
    foto_id: uuid.UUID,
    dados: FotoUpdatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> Foto:
    """Atualiza a legenda e/ou a ordem de uma foto."""
    return await foto_service.atualizar(db, foto_id, legenda=dados.legenda, ordem=dados.ordem)


@router.delete("/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_foto(
    foto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(get_current_user),
) -> None:
    """Remove o vínculo (registro `Foto`) e o objeto correspondente no storage."""
    await foto_service.remover(db, foto_id, storage)
