"""Endpoints de Ocorrência (BL-14, RF-04, RN-03, RN-05, RN-10).

- `GET /inspecoes/{id}/ocorrencias` — lista ocorrências da inspeção, com filtros opcionais.
- `POST /inspecoes/{id}/ocorrencias` — cria ocorrência para a inspeção.
- `GET /ocorrencias/{id}` — detalhe da ocorrência.
- `PUT /ocorrencias/{id}` — atualiza ocorrência.
- `DELETE /ocorrencias/{id}` — remove ocorrência.

Dados de campo: liberados à equipe (`auditor`/`auxiliar`), com autoria gravada
em `Ocorrencia.criado_por_id` (RN-18, DEC-27).
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_equipe
from app.core.database import get_db
from app.models import Ocorrencia, Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.ocorrencia import OcorrenciaCreate, OcorrenciaRead
from app.services import ocorrencia_service

router = APIRouter(prefix="/api/v1", tags=["ocorrencias"])


@router.get("/inspecoes/{inspecao_id}/ocorrencias", response_model=PaginatedResponse[OcorrenciaRead])
async def listar_ocorrencias_da_inspecao(
    inspecao_id: uuid.UUID,
    sistema_id: str | None = Query(None),
    grau_risco: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> PaginatedResponse:
    """Lista ocorrências da inspeção com filtros opcionais por sistema e grau de risco."""
    itens = await ocorrencia_service.listar_por_inspecao(
        db,
        inspecao_id=inspecao_id,
        sistema_id=sistema_id,
        grau_risco=grau_risco,
    )
    return PaginatedResponse(items=[OcorrenciaRead.model_validate(item) for item in itens], total=len(itens), page=1, page_size=len(itens) or 1)


@router.post("/inspecoes/{inspecao_id}/ocorrencias", response_model=OcorrenciaRead, status_code=status.HTTP_201_CREATED)
async def criar_ocorrencia(
    inspecao_id: uuid.UUID,
    dados: OcorrenciaCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_equipe),
) -> Ocorrencia:
    """Cria uma nova ocorrência vinculada a uma inspeção."""
    return await ocorrencia_service.criar(
        db, inspecao_id=inspecao_id, dados=dados, criado_por_id=usuario.id
    )


@router.get("/ocorrencias/{ocorrencia_id}", response_model=OcorrenciaRead)
async def obter_ocorrencia(
    ocorrencia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Ocorrencia:
    """Retorna uma ocorrência específica."""
    return await ocorrencia_service.obter_por_id(db, ocorrencia_id)


@router.put("/ocorrencias/{ocorrencia_id}", response_model=OcorrenciaRead)
async def atualizar_ocorrencia(
    ocorrencia_id: uuid.UUID,
    dados: OcorrenciaCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_equipe),
) -> Ocorrencia:
    """Atualiza uma ocorrência existente."""
    return await ocorrencia_service.atualizar(db, ocorrencia_id, dados, usuario_id=usuario.id)


@router.delete("/ocorrencias/{ocorrencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_ocorrencia(
    ocorrencia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> None:
    """Remove uma ocorrência existente."""
    await ocorrencia_service.remover(db, ocorrencia_id)
