"""Monta o contexto do RFIP (consumido por `rfip_pipeline`) a partir do banco (V1-03).

`responsavel` = fiscal do contrato (com `titulo_profissional`); ocorrências e fotos pelo
`contexto_comum`; `incluir_resumo` vem do `RelatorioConteudo` (padrão: verdadeiro).
O RFIP não tem textos corridos; a ficha mostra a 1ª foto de cada ocorrência.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tipo_servico import TipoServico
from app.services import relatorio_conteudo_service
from app.services.report_generator import contexto_comum as comum

TIPO_RFIP = TipoServico.RFIP.value

# O rodapé do template imprime nome e CREA do responsável; os demais campos têm '—' como fallback.
CAMPOS_OBRIGATORIOS_RFIP: tuple[tuple[str, str], ...] = (
    ("responsavel", "nome"),
    ("responsavel", "crea"),
)


def validar_contexto_rfip(contexto: dict[str, Any]) -> list[str]:
    """Caminhos obrigatórios ausentes (`responsavel.crea`); vazia = emitível."""
    return comum.validar_obrigatorios(contexto, CAMPOS_OBRIGATORIOS_RFIP)


def extrair_fotos_rfip(contexto: dict[str, Any]) -> set[str]:
    return comum.primeiras_fotos(contexto)


async def montar_contexto_rfip(db: AsyncSession, inspecao_id: uuid.UUID) -> dict[str, Any]:
    """Retorna o dicionário aceito por `rfip_pipeline.normalizar_contexto`.

    404 se a inspeção não existe; 409 se não é `RFIP`. Ocorrências por `seq_numero`, fotos por `ordem`.
    """
    inspecao = await comum.carregar_inspecao(db, inspecao_id, TipoServico.RFIP)
    dados = (await relatorio_conteudo_service.obter(db, inspecao_id, TipoServico.RFIP)).dados
    return {
        "inspecao": comum.inspecao_ctx(inspecao),
        "responsavel": comum.fiscal_ctx(inspecao.contrato.fiscal),
        "incluir_resumo": bool(dados.get("incluir_resumo", True)),
        "ocorrencias": comum.ocorrencias_ctx(inspecao),
    }
