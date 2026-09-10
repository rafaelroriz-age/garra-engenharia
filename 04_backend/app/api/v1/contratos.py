"""Endpoints de Contrato (BL-09, RF-02, RF-12, RN-06, RN-09, `00_docs/arquitetura.md` Seção 4).

- `GET /contratos` — lista paginada, filtro por tipo, status e edificação.
- `POST /contratos` — cria contrato com executoras e NBRs em cascata (cria também a Inspeção 1:1).
- `GET /contratos/{id}` — detalhe completo (executoras, NBRs, inspeção).
- `PUT /contratos/{id}` — atualiza contrato substituindo executoras e NBRs.

Leitura liberada à equipe (`auditor`/`auxiliar`); escrita restrita ao `auditor`
(RN-18, DEC-27) — contrato é ato administrativo, não dado de campo.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor, require_equipe
from app.core.database import get_db
from app.models import Contrato, Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.contrato import (
    ContratoCreatePayload,
    ContratoDetalhe,
    ContratoRead,
    ContratoUpdatePayload,
)
from app.services import contrato_service

router = APIRouter(prefix="/api/v1/contratos", tags=["contratos"])


@router.get("", response_model=PaginatedResponse[ContratoRead])
async def listar_contratos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tipo_servico: str | None = Query(None),
    status_contrato: str | None = Query(None, alias="status"),
    edificacao_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> PaginatedResponse:
    """Lista contratos paginados, com filtro opcional por tipo de serviço, status e edificação."""
    items, total = await contrato_service.listar(
        db,
        page=page,
        page_size=page_size,
        tipo_servico=tipo_servico,
        status_contrato=status_contrato,
        edificacao_id=edificacao_id,
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ContratoDetalhe, status_code=status.HTTP_201_CREATED)
async def criar_contrato(
    dados: ContratoCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> Contrato:
    """Cria um contrato com N empresas executoras e N NBRs (RN-06, RF-12), e a Inspeção originada."""
    return await contrato_service.criar(db, dados)


@router.get("/{contrato_id}", response_model=ContratoDetalhe)
async def obter_contrato(
    contrato_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Contrato:
    """Detalhe completo do contrato, incluindo executoras, NBRs e inspeção."""
    return await contrato_service.obter_por_id(db, contrato_id)


@router.put("/{contrato_id}", response_model=ContratoDetalhe)
async def atualizar_contrato(
    contrato_id: uuid.UUID,
    dados: ContratoUpdatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> Contrato:
    """Atualiza um contrato, substituindo integralmente suas executoras e NBRs."""
    return await contrato_service.atualizar(db, contrato_id, dados)
