"""Endpoints de Visita, Mão de Obra e Medição (BL-10, RF-03, RN-01, RN-02, DEC-38).

- `GET /visitas/{id}` — detalhe da visita (equipe, medições e fotos).
- `PUT /visitas/{id}` — atualização parcial (data, serviços executados, observações).
- `GET|POST /visitas/{id}/mao-obra` e `GET|PUT|DELETE /visitas/{id}/mao-obra/{item_id}`.
- `GET|POST /visitas/{id}/medicoes` e `GET|PUT|DELETE /visitas/{id}/medicoes/{item_id}`.

Dados de campo: liberados à equipe (`auditor`/`auxiliar`) — RN-18, DEC-27, BL-42.
"""
import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_equipe
from app.core.database import get_db
from app.models import Usuario, Visita, VisitaMaoObra, VisitaMedicao
from app.schemas.visita import VisitaComDetalhes, VisitaUpdatePayload
from app.schemas.visita_mao_obra import VisitaMaoObraCreatePayload, VisitaMaoObraRead
from app.schemas.visita_medicao import VisitaMedicaoCreatePayload, VisitaMedicaoRead
from app.services import visita_service

router = APIRouter(prefix="/api/v1/visitas", tags=["visitas"])


@router.get("/{visita_id}", response_model=VisitaComDetalhes)
async def obter_visita(
    visita_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Visita:
    """Detalhe da visita com equipe, medições e fotos vinculadas."""
    return await visita_service.obter_por_id(db, visita_id)


@router.put("/{visita_id}", response_model=VisitaComDetalhes)
async def atualizar_visita(
    visita_id: uuid.UUID,
    dados: VisitaUpdatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Visita:
    """Atualiza data, serviços executados e/ou observações; campo omitido é preservado."""
    return await visita_service.atualizar_visita(db, visita_id, dados)


# ---------------------------------------------------------------- Mão de obra

@router.get("/{visita_id}/mao-obra", response_model=list[VisitaMaoObraRead])
async def listar_mao_obra(
    visita_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> list[VisitaMaoObra]:
    return await visita_service.listar_mao_obra(db, visita_id)


@router.post(
    "/{visita_id}/mao-obra", response_model=VisitaMaoObraRead, status_code=status.HTTP_201_CREATED
)
async def adicionar_mao_obra(
    visita_id: uuid.UUID,
    dados: VisitaMaoObraCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMaoObra:
    """Adiciona um registro de mão de obra (função + quantidade) a uma visita."""
    return await visita_service.adicionar_mao_obra(db, visita_id, dados)


@router.get("/{visita_id}/mao-obra/{item_id}", response_model=VisitaMaoObraRead)
async def obter_mao_obra(
    visita_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMaoObra:
    return await visita_service.obter_mao_obra(db, visita_id, item_id)


@router.put("/{visita_id}/mao-obra/{item_id}", response_model=VisitaMaoObraRead)
async def atualizar_mao_obra(
    visita_id: uuid.UUID,
    item_id: uuid.UUID,
    dados: VisitaMaoObraCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMaoObra:
    """Substitui função e quantidade de um registro de mão de obra (ambos obrigatórios)."""
    return await visita_service.atualizar_mao_obra(db, visita_id, item_id, dados)


@router.delete("/{visita_id}/mao-obra/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_mao_obra(
    visita_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Response:
    await visita_service.remover_mao_obra(db, visita_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- Medições

@router.get("/{visita_id}/medicoes", response_model=list[VisitaMedicaoRead])
async def listar_medicoes(
    visita_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> list[VisitaMedicao]:
    return await visita_service.listar_medicoes(db, visita_id)


@router.post(
    "/{visita_id}/medicoes", response_model=VisitaMedicaoRead, status_code=status.HTTP_201_CREATED
)
async def adicionar_medicao(
    visita_id: uuid.UUID,
    dados: VisitaMedicaoCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMedicao:
    """Adiciona uma medição (descrição + quantidade + unidade) a uma visita."""
    return await visita_service.adicionar_medicao(db, visita_id, dados)


@router.get("/{visita_id}/medicoes/{item_id}", response_model=VisitaMedicaoRead)
async def obter_medicao(
    visita_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMedicao:
    return await visita_service.obter_medicao(db, visita_id, item_id)


@router.put("/{visita_id}/medicoes/{item_id}", response_model=VisitaMedicaoRead)
async def atualizar_medicao(
    visita_id: uuid.UUID,
    item_id: uuid.UUID,
    dados: VisitaMedicaoCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMedicao:
    """Substitui descrição, quantidade e unidade de uma medição (todos obrigatórios)."""
    return await visita_service.atualizar_medicao(db, visita_id, item_id, dados)


@router.delete("/{visita_id}/medicoes/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_medicao(
    visita_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Response:
    await visita_service.remover_medicao(db, visita_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
