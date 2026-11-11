"""Monta o contexto do RFO (consumido por `rfo_pipeline`) a partir do banco (BL-13).

Camada de montagem apenas: não gera arquivos nem baixa imagens. Cada foto sai
com `storage_key` (e `url_publica`); o binário continua a cargo do
`url_fetcher`/`foto_fetcher` do chamador. RF-03..RF-06, RN-01, RN-02.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError
from app.models import Contrato, ContratoExecutor, Foto, Inspecao, Ocorrencia, Visita

TIPO_RFO = "RFO"
LEGENDA_APROVADA = "aprovada"


def _data_br(valor: date | None) -> str | None:
    return valor.strftime("%d/%m/%Y") if valor else None


def legenda_aprovada(foto: Any) -> bool:
    """DEC-37/DP-9: só legenda aprovada entra no relatório.

    O modelo `Foto` ainda não tem campo de status da legenda (lacuna registrada
    em 00_docs/backlog-auto/rfo-contexto-banco.md). Enquanto ele não existir,
    a legenda (humana) é considerada aprovada; havendo `legenda_status`, só
    `"aprovada"` passa.
    """
    return getattr(foto, "legenda_status", LEGENDA_APROVADA) == LEGENDA_APROVADA


def _foto_ctx(foto: Foto) -> dict[str, Any]:
    legenda = foto.legenda if legenda_aprovada(foto) and foto.legenda else None
    return {
        "id": str(foto.id),
        "storage_key": foto.storage_key,
        "url_publica": foto.url_publica,
        "legenda": legenda,
        "ordem": foto.ordem,
    }


def _fotos_ordenadas(fotos: list[Foto]) -> list[dict[str, Any]]:
    # `ordem` pode ser nulo: nulos ao final, desempate por created_at/id estável.
    ordenadas = sorted(fotos, key=lambda f: (f.ordem is None, f.ordem or 0, str(f.id)))
    return [_foto_ctx(f) for f in ordenadas]


def _executor_ctx(executor: ContratoExecutor) -> dict[str, Any]:
    legal, rte = executor.responsavel_legal, executor.rte
    return {
        "razao_social": executor.razao_social,
        "cnpj": executor.cnpj,
        "endereco": executor.endereco,
        "art_execucao": executor.art_execucao,
        "responsavel_legal": {"nome": legal.nome, "cpf_cnpj": legal.cpf_cnpj, "crea": legal.crea} if legal else None,
        "rte": {"nome": rte.nome, "crea": rte.crea} if rte else None,
    }


def _visita_ctx(visita: Visita) -> dict[str, Any]:
    return {
        "id": str(visita.id),
        "seq_numero": visita.seq_numero,
        "data": _data_br(visita.data),
        "servicos_executados": visita.servicos_executados,
        "observacoes": visita.observacoes,
        "mao_obra": [{"funcao": m.funcao, "quantidade": m.quantidade} for m in sorted(visita.mao_obra, key=lambda m: (m.funcao, str(m.id)))],
        "medicoes": [
            {"descricao": m.descricao, "quantidade": m.quantidade, "unidade": m.unidade}
            for m in sorted(visita.medicoes, key=lambda m: (m.descricao, str(m.id)))
        ],
        "fotos": _fotos_ordenadas(visita.fotos),
    }


def _ocorrencia_ctx(oc: Ocorrencia) -> dict[str, Any]:
    return {
        "id": str(oc.id),
        "seq_numero": oc.seq_numero,
        "sistema": oc.sistema.nome if oc.sistema else None,
        "subsistema": oc.subsistema.nome if oc.subsistema else None,
        "localizacao": oc.localizacao,
        "situacao": oc.situacao,
        "classificacao": oc.classificacao,
        "tipo_anomalia": oc.tipo_anomalia,
        "tipo_falha": oc.tipo_falha,
        "grau_risco": oc.grau_risco,
        "prioridade": oc.prioridade,
        "descricao": oc.descricao,
        "fotos": _fotos_ordenadas(oc.fotos),
    }


async def montar_contexto_rfo(db: AsyncSession, inspecao_id: uuid.UUID) -> dict[str, Any]:
    """Retorna o dicionário aceito por `rfo_pipeline.normalizar_contexto`.

    404 (`NotFoundError`) se a inspeção não existe; 409 (`ConflictError`) se
    `tipo != 'RFO'`. Visitas e ocorrências saem por `seq_numero`, fotos por `ordem`.
    """
    resultado = await db.execute(
        select(Inspecao)
        .options(
            selectinload(Inspecao.contrato).selectinload(Contrato.edificacao),
            selectinload(Inspecao.contrato).selectinload(Contrato.fiscal),
            selectinload(Inspecao.contrato)
            .selectinload(Contrato.executores)
            .options(selectinload(ContratoExecutor.responsavel_legal), selectinload(ContratoExecutor.rte)),
            selectinload(Inspecao.contrato).selectinload(Contrato.nbrs),
            selectinload(Inspecao.visitas).selectinload(Visita.mao_obra),
            selectinload(Inspecao.visitas).selectinload(Visita.medicoes),
            selectinload(Inspecao.visitas).selectinload(Visita.fotos),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.fotos),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.sistema),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.subsistema),
        )
        .where(Inspecao.id == inspecao_id)
    )
    inspecao = resultado.scalar_one_or_none()
    if inspecao is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    if inspecao.tipo != TIPO_RFO:
        raise ConflictError(
            f"Inspeção '{inspecao_id}' é do tipo '{inspecao.tipo}'; o RFO só é gerado para inspeções do tipo 'RFO'.",
            type_suffix="inspecao-nao-rfo",
        )

    contrato = inspecao.contrato
    edificacao = contrato.edificacao
    fiscal = contrato.fiscal
    return {
        "inspecao": {"id": str(inspecao.id), "tipo": inspecao.tipo, "status": inspecao.status},
        "contrato": {
            "numero": contrato.numero,
            "tipo_servico": contrato.tipo_servico,
            "objeto": contrato.objeto,
            "data_inicio": _data_br(contrato.data_inicio),
            "prazo_dias": contrato.prazo_dias,
            "art_fiscalizacao": contrato.art_fiscalizacao,
            "observacoes_gerais": contrato.observacoes_gerais,
        },
        "edificacao": {
            "nome": edificacao.nome,
            "endereco": edificacao.endereco,
            "cep": edificacao.cep,
            "tipologia": edificacao.tipologia,
            "sistema_construtivo": edificacao.sistema_construtivo,
            "descricao_pavimentos": edificacao.descricao_pavimentos,
            "area_total_m2": edificacao.area_total_m2,
        },
        "fiscal": {"nome": fiscal.nome, "crea": fiscal.crea, "email": fiscal.email, "telefone": fiscal.telefone},
        "executores": [_executor_ctx(e) for e in sorted(contrato.executores, key=lambda e: e.razao_social)],
        "nbrs": [
            {"codigo_nbr": n.codigo_nbr, "descricao": n.descricao}
            for n in sorted(contrato.nbrs, key=lambda n: n.codigo_nbr)
        ],
        "visitas": [_visita_ctx(v) for v in sorted(inspecao.visitas, key=lambda v: v.seq_numero)],
        "ocorrencias": [_ocorrencia_ctx(o) for o in sorted(inspecao.ocorrencias, key=lambda o: o.seq_numero)],
    }
