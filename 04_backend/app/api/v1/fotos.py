"""Endpoints de Foto (BL-11, RF-05, `00_docs/arquitetura.md` Seção 4 e Seção 6).

- `POST /fotos/upload` — upload manual (multipart, Opção B).
- `POST /fotos/upload-clipboard` — upload via clipboard paste em base64 (Opção A).
- `POST /ocorrencias/{id}/fotos` — vincula foto (já enviada ao storage) a uma Ocorrência.
- `POST /visitas/{id}/fotos` — vincula foto a uma Visita.
- `PUT /fotos/{id}` — atualiza legenda/ordem e aprova a sugestão de IA (DEC-37 DP-3/DP-5).
- `POST /fotos/{id}/legenda-ia/gerar` — sugestão de legenda por IA em rascunho (BL-34, DP-4).
- `DELETE /fotos/{id}` — remove vínculo e objeto do storage.
- `DELETE /fotos/upload` — descarta upload nunca vinculado (DEC-39 D).

Dados de campo: liberados à equipe (`auditor`/`auxiliar`), com autoria gravada
em `Foto.criado_por_id` (RN-18, DEC-27). Mitigações OWASP: A08
(reprocessamento Pillow de toda imagem antes de persistir, ver
`app.services.image_processing`) e A10 (nunca aceita URL fornecida pelo
cliente — apenas multipart ou base64 processados localmente).
"""
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_equipe
from app.core.database import get_db
from app.models import Foto, Usuario
from app.schemas.foto import (
    FotoDescartarUploadPayload,
    FotoRead,
    FotoUpdatePayload,
    FotoUploadClipboardPayload,
    FotoUploadResponse,
    FotoVincularPayload,
    LegendaIAGerarPayload,
)
from app.services import foto_service
from app.services.legenda_ia import LegendaIAClient, get_legenda_ia_client
from app.services.storage import get_storage_client
from app.services.storage.base import StorageClient
from app.services.storage.s3_client import MAX_UPLOAD_SIZE_BYTES

router = APIRouter(prefix="/api/v1", tags=["fotos"])


@router.post("/fotos/upload", response_model=FotoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_foto(
    arquivo: UploadFile = File(...),
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(require_equipe),
) -> FotoUploadResponse:
    """Upload manual de arquivo de imagem (multipart/form-data) — Opção B (Seção 6)."""
    # Lê no máximo limite+1 bytes: o excesso é recusado em `_validar_tamanho` sem carregar o arquivo todo.
    conteudo = await arquivo.read(MAX_UPLOAD_SIZE_BYTES + 1)
    storage_key, url = await foto_service.upload_arquivo(conteudo, storage)
    return FotoUploadResponse(storage_key=storage_key, url=url)


@router.post(
    "/fotos/upload-clipboard", response_model=FotoUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_foto_clipboard(
    dados: FotoUploadClipboardPayload,
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(require_equipe),
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
    storage: StorageClient = Depends(get_storage_client),
    usuario: Usuario = Depends(require_equipe),
) -> Foto:
    """Vincula uma foto (já enviada via `/fotos/upload*`) a uma Ocorrência, com legenda (RN-03, RN-11)."""
    return await foto_service.vincular_a_ocorrencia(
        db,
        ocorrencia_id,
        storage,
        storage_key=dados.storage_key,
        legenda=dados.legenda,
        ordem=dados.ordem,
        origem=dados.origem,
        criado_por_id=usuario.id,
    )


@router.post("/visitas/{visita_id}/fotos", response_model=FotoRead, status_code=status.HTTP_201_CREATED)
async def vincular_foto_a_visita(
    visita_id: uuid.UUID,
    dados: FotoVincularPayload,
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    usuario: Usuario = Depends(require_equipe),
) -> Foto:
    """Vincula uma foto (já enviada via `/fotos/upload*`) a uma Visita de fiscalização."""
    return await foto_service.vincular_a_visita(
        db,
        visita_id,
        storage,
        storage_key=dados.storage_key,
        legenda=dados.legenda,
        ordem=dados.ordem,
        origem=dados.origem,
        criado_por_id=usuario.id,
    )


@router.put("/fotos/{foto_id}", response_model=FotoRead)
async def atualizar_foto(
    foto_id: uuid.UUID,
    dados: FotoUpdatePayload,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_equipe),
) -> Foto:
    """Atualiza a legenda e/ou a ordem de uma foto; com `aprovar_legenda_ia`, aprova a sugestão de IA."""
    # Só os campos enviados no corpo: `legenda: null` explícito limpa a legenda (DEC-39 C, DEC-37 DP-5).
    campos = {nome: getattr(dados, nome) for nome in dados.model_fields_set}
    return await foto_service.atualizar(db, foto_id, campos, usuario=usuario)


@router.post("/fotos/{foto_id}/legenda-ia/gerar", response_model=FotoRead)
async def gerar_legenda_ia(
    foto_id: uuid.UUID,
    dados: LegendaIAGerarPayload | None = None,
    usuario: Usuario = Depends(require_equipe),
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    cliente: LegendaIAClient = Depends(get_legenda_ia_client),
) -> Foto:
    """Gera a sugestão de legenda por IA em `rascunho`, sem alterar `legenda` (BL-34, DEC-37 DP-4).

    `usuario` é declarado antes de `cliente` para que 401/403 venham antes do 503 sem provedor.
    """
    campos = {nome: getattr(dados, nome) for nome in dados.model_fields_set} if dados else {}
    return await foto_service.gerar_legenda_ia(db, foto_id, storage, cliente, campos)


@router.delete("/fotos/upload", status_code=status.HTTP_204_NO_CONTENT)
async def descartar_upload(
    dados: FotoDescartarUploadPayload,
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(require_equipe),
) -> None:
    """Descarta um upload ainda não vinculado (ex.: o editor de anotação gerou nova versão).

    Declarada antes de `/fotos/{foto_id}` para não ser interpretada como UUID.
    """
    await foto_service.descartar_upload(db, dados.storage_key, storage)


@router.delete("/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_foto(
    foto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    _usuario: Usuario = Depends(require_equipe),
) -> None:
    """Remove o vínculo (registro `Foto`) e o objeto correspondente no storage."""
    await foto_service.remover(db, foto_id, storage)
