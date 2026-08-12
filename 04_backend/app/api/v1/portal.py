"""Portal do Cliente (BL-30/BL-32/BL-33, RF-13, RN-14, DEC-18).

Rotas somente leitura, exclusivas do perfil `cliente`. O escopo é sempre
resolvido a partir de `Responsavel.usuario_id = current_user.id` — nenhum
`edificacao_id`/`relatorio_id` da requisição é aceito sem validação de vínculo
(ver `app/services/portal_service.py`).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_cliente_responsavel, require_role
from app.core.database import get_db
from app.models import Edificacao
from app.schemas import EdificacaoRead
from app.schemas.dashboard import DashboardEdificacaoRead
from app.schemas.portal import (
    PortalAcompanhamentoRead,
    PortalDownloadRead,
    PortalRelatorioRead,
)
from app.services import portal_service
from app.services.storage import StorageClient, get_storage_client

router = APIRouter(
    prefix="/api/v1/portal",
    tags=["portal"],
    dependencies=[Depends(require_role("cliente"))],
)


@router.get("/edificacoes", response_model=list[EdificacaoRead], summary="Lista edificações do contratante")
async def listar_edificacoes_portal(
    responsavel=Depends(get_current_cliente_responsavel),
    db: AsyncSession = Depends(get_db),
) -> list[Edificacao]:
    """Retorna apenas as edificações vinculadas aos contratos do contratante logado."""
    return await portal_service.listar_edificacoes(db, responsavel.id)


@router.get(
    "/edificacoes/{edificacao_id}/dashboard",
    response_model=DashboardEdificacaoRead,
    summary="Dashboard de saúde da edificação (escopo do contratante)",
)
async def obter_dashboard_portal(
    edificacao_id: uuid.UUID,
    responsavel=Depends(get_current_cliente_responsavel),
    db: AsyncSession = Depends(get_db),
) -> DashboardEdificacaoRead:
    return await portal_service.obter_dashboard(db, responsavel.id, edificacao_id)


@router.get(
    "/edificacoes/{edificacao_id}/acompanhamento",
    response_model=PortalAcompanhamentoRead,
    summary="Acompanhamento da auditoria em andamento (visitas e ocorrências)",
)
async def obter_acompanhamento_portal(
    edificacao_id: uuid.UUID,
    responsavel=Depends(get_current_cliente_responsavel),
    db: AsyncSession = Depends(get_db),
) -> PortalAcompanhamentoRead:
    return await portal_service.obter_acompanhamento(db, responsavel.id, edificacao_id)


@router.get(
    "/relatorios",
    response_model=list[PortalRelatorioRead],
    summary="Relatórios/laudos emitidos para o contratante",
)
async def listar_relatorios_portal(
    responsavel=Depends(get_current_cliente_responsavel),
    db: AsyncSession = Depends(get_db),
) -> list[PortalRelatorioRead]:
    return await portal_service.listar_relatorios(db, responsavel.id)


@router.get(
    "/relatorios/{relatorio_id}/download/{formato}",
    response_model=PortalDownloadRead,
    summary="URL pré-assinada de download do relatório (pdf|docx)",
)
async def baixar_relatorio_portal(
    relatorio_id: uuid.UUID,
    formato: str,
    responsavel=Depends(get_current_cliente_responsavel),
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
) -> PortalDownloadRead:
    return await portal_service.gerar_url_download(
        db, responsavel.id, relatorio_id, formato.lower(), storage
    )
