"""Service Layer do Portal do Cliente (BL-32/BL-33, RF-13, RN-14, DEC-18).

Todo acesso é escopado pelo `Responsavel` vinculado ao usuário autenticado
(`Responsavel.usuario_id`), nunca por um id recebido do cliente da requisição:
o `edificacao_id`/`relatorio_id` da URL é sempre validado contra os Contratos
em que esse Responsavel é o contratante antes de qualquer leitura de dados
(OWASP A01, ver `00_docs/arquitetura.md` Seção 10.1).
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models import Contrato, Edificacao, Foto, Inspecao, Ocorrencia, Relatorio, Visita
from app.schemas.dashboard import DashboardEdificacaoRead
from app.schemas.portal import (
    PortalAcompanhamentoRead,
    PortalContagemGrauRisco,
    PortalContratoAcompanhamento,
    PortalDownloadRead,
    PortalOcorrenciaResumo,
    PortalRelatorioRead,
    PortalVisitaResumo,
)
from app.services import edificacao_service
from app.services.storage import StorageClient
from app.services.storage.s3_client import DEFAULT_PRESIGNED_URL_EXPIRES_IN_SECONDS

_FORMATOS = {"pdf": "pdf_key", "docx": "docx_key"}


async def listar_edificacoes(db: AsyncSession, responsavel_id: uuid.UUID) -> list[Edificacao]:
    result = await db.execute(
        select(Edificacao)
        .join(Contrato, Contrato.edificacao_id == Edificacao.id)
        .where(Contrato.contratante_id == responsavel_id)
        .distinct()
        .order_by(Edificacao.nome)
    )
    return list(result.scalars().all())


async def _assert_edificacao_no_escopo(
    db: AsyncSession, responsavel_id: uuid.UUID, edificacao_id: uuid.UUID
) -> None:
    """Bloqueia acesso a edificação de outro contratante com o mesmo 404 de inexistente.

    Responder 404 (e não 403) evita revelar a existência de edificações de terceiros.
    """
    result = await db.execute(
        select(Contrato.id)
        .where(Contrato.contratante_id == responsavel_id, Contrato.edificacao_id == edificacao_id)
        .limit(1)
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError(
            f"Edificação '{edificacao_id}' não encontrada para o contratante autenticado.",
            type_suffix="edificacao-nao-encontrada",
        )


async def obter_dashboard(
    db: AsyncSession, responsavel_id: uuid.UUID, edificacao_id: uuid.UUID
) -> DashboardEdificacaoRead:
    await _assert_edificacao_no_escopo(db, responsavel_id, edificacao_id)
    return await edificacao_service.obter_dashboard(db, edificacao_id)


async def obter_acompanhamento(
    db: AsyncSession, responsavel_id: uuid.UUID, edificacao_id: uuid.UUID
) -> PortalAcompanhamentoRead:
    await _assert_edificacao_no_escopo(db, responsavel_id, edificacao_id)

    edificacao = await edificacao_service.obter_por_id(db, edificacao_id)

    result = await db.execute(
        select(Contrato)
        .where(Contrato.contratante_id == responsavel_id, Contrato.edificacao_id == edificacao_id)
        .options(selectinload(Contrato.inspecao))
        .order_by(Contrato.created_at.desc())
    )
    contratos = list(result.scalars().all())

    inspecao_ids = [c.inspecao.id for c in contratos if c.inspecao is not None]
    visitas_por_inspecao = await _carregar_visitas(db, inspecao_ids)
    ocorrencias_por_inspecao = await _carregar_ocorrencias(db, inspecao_ids)

    return PortalAcompanhamentoRead(
        edificacao_id=edificacao.id,
        edificacao_nome=edificacao.nome,
        contratos=[
            _montar_contrato_acompanhamento(
                contrato,
                visitas_por_inspecao.get(contrato.inspecao.id, []) if contrato.inspecao else [],
                ocorrencias_por_inspecao.get(contrato.inspecao.id, []) if contrato.inspecao else [],
            )
            for contrato in contratos
        ],
    )


async def _carregar_visitas(
    db: AsyncSession, inspecao_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[PortalVisitaResumo]]:
    if not inspecao_ids:
        return {}

    fotos_subq = (
        select(Foto.visita_id, func.count(Foto.id).label("total"))
        .where(Foto.visita_id.is_not(None))
        .group_by(Foto.visita_id)
        .subquery()
    )
    result = await db.execute(
        select(Visita, func.coalesce(fotos_subq.c.total, 0))
        .outerjoin(fotos_subq, fotos_subq.c.visita_id == Visita.id)
        .where(Visita.inspecao_id.in_(inspecao_ids))
        .order_by(Visita.seq_numero)
    )

    agrupado: dict[uuid.UUID, list[PortalVisitaResumo]] = {}
    for visita, total_fotos in result.all():
        agrupado.setdefault(visita.inspecao_id, []).append(
            PortalVisitaResumo(
                id=visita.id,
                seq_numero=visita.seq_numero,
                data=visita.data,
                servicos_executados=visita.servicos_executados,
                total_fotos=int(total_fotos),
            )
        )
    return agrupado


async def _carregar_ocorrencias(
    db: AsyncSession, inspecao_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[PortalOcorrenciaResumo]]:
    if not inspecao_ids:
        return {}

    result = await db.execute(
        select(Ocorrencia)
        .where(Ocorrencia.inspecao_id.in_(inspecao_ids))
        .options(selectinload(Ocorrencia.sistema), selectinload(Ocorrencia.subsistema))
        .order_by(Ocorrencia.seq_numero)
    )

    agrupado: dict[uuid.UUID, list[PortalOcorrenciaResumo]] = {}
    for ocorrencia in result.scalars().all():
        agrupado.setdefault(ocorrencia.inspecao_id, []).append(
            PortalOcorrenciaResumo(
                id=ocorrencia.id,
                seq_numero=ocorrencia.seq_numero,
                sistema_nome=ocorrencia.sistema.nome if ocorrencia.sistema else None,
                subsistema_nome=ocorrencia.subsistema.nome if ocorrencia.subsistema else None,
                localizacao=ocorrencia.localizacao,
                situacao=ocorrencia.situacao,
                grau_risco=ocorrencia.grau_risco,
                prioridade=ocorrencia.prioridade,
                descricao=ocorrencia.descricao,
            )
        )
    return agrupado


def _montar_contrato_acompanhamento(
    contrato: Contrato,
    visitas: list[PortalVisitaResumo],
    ocorrencias: list[PortalOcorrenciaResumo],
) -> PortalContratoAcompanhamento:
    contagem = PortalContagemGrauRisco(
        minimo=sum(1 for o in ocorrencias if o.grau_risco == "MINIMO"),
        medio=sum(1 for o in ocorrencias if o.grau_risco == "MEDIO"),
        critico=sum(1 for o in ocorrencias if o.grau_risco == "CRITICO"),
    )
    return PortalContratoAcompanhamento(
        contrato_id=contrato.id,
        numero=contrato.numero,
        tipo_servico=contrato.tipo_servico,
        status=contrato.status,
        data_inicio=contrato.data_inicio,
        inspecao_id=contrato.inspecao.id if contrato.inspecao else None,
        inspecao_status=contrato.inspecao.status if contrato.inspecao else None,
        total_visitas=len(visitas),
        total_ocorrencias=len(ocorrencias),
        ocorrencias_por_grau_risco=contagem,
        visitas=visitas,
        ocorrencias=ocorrencias,
    )


async def listar_relatorios(
    db: AsyncSession, responsavel_id: uuid.UUID
) -> list[PortalRelatorioRead]:
    result = await db.execute(
        select(Relatorio, Contrato, Edificacao)
        .join(Inspecao, Relatorio.inspecao_id == Inspecao.id)
        .join(Contrato, Inspecao.contrato_id == Contrato.id)
        .join(Edificacao, Contrato.edificacao_id == Edificacao.id)
        .where(Contrato.contratante_id == responsavel_id)
        .order_by(Relatorio.emitido_em.desc().nullslast(), Relatorio.versao)
    )
    return [
        PortalRelatorioRead(
            id=relatorio.id,
            versao=relatorio.versao,
            tipo=relatorio.tipo,
            status=relatorio.status,
            emitido_em=relatorio.emitido_em,
            tem_pdf=bool(relatorio.pdf_key),
            tem_docx=bool(relatorio.docx_key),
            inspecao_id=relatorio.inspecao_id,
            contrato_id=contrato.id,
            contrato_numero=contrato.numero,
            edificacao_id=edificacao.id,
            edificacao_nome=edificacao.nome,
        )
        for relatorio, contrato, edificacao in result.all()
    ]


def campo_do_formato(formato: str) -> str:
    """Coluna de `Relatorio` com a chave do arquivo (`pdf_key`/`docx_key`), ou 404."""
    campo_key = _FORMATOS.get(formato)
    if campo_key is None:
        raise NotFoundError(
            f"Formato '{formato}' não suportado.", type_suffix="formato-nao-suportado"
        )
    return campo_key


def url_assinada_do_relatorio(
    relatorio: Relatorio, campo_key: str, formato: str, storage: StorageClient
) -> PortalDownloadRead:
    """URL pré-assinada do arquivo do relatório já autorizado pelo chamador (portal ou equipe, V1-02)."""
    storage_key = getattr(relatorio, campo_key)
    if not storage_key:
        raise NotFoundError(
            f"Relatório '{relatorio.id}' não possui arquivo {formato.upper()} disponível.",
            type_suffix="arquivo-nao-disponivel",
        )

    url = storage.generate_presigned_url(storage_key, DEFAULT_PRESIGNED_URL_EXPIRES_IN_SECONDS)
    return PortalDownloadRead(
        relatorio_id=relatorio.id,
        formato=formato,
        url=url,
        expira_em_segundos=DEFAULT_PRESIGNED_URL_EXPIRES_IN_SECONDS,
    )


async def gerar_url_download(
    db: AsyncSession,
    responsavel_id: uuid.UUID,
    relatorio_id: uuid.UUID,
    formato: str,
    storage: StorageClient,
) -> PortalDownloadRead:
    campo_key = campo_do_formato(formato)

    result = await db.execute(
        select(Relatorio)
        .join(Inspecao, Relatorio.inspecao_id == Inspecao.id)
        .join(Contrato, Inspecao.contrato_id == Contrato.id)
        .where(Relatorio.id == relatorio_id, Contrato.contratante_id == responsavel_id)
    )
    relatorio = result.scalar_one_or_none()
    if relatorio is None:
        raise NotFoundError(
            f"Relatório '{relatorio_id}' não encontrado para o contratante autenticado.",
            type_suffix="relatorio-nao-encontrado",
        )

    return url_assinada_do_relatorio(relatorio, campo_key, formato, storage)
