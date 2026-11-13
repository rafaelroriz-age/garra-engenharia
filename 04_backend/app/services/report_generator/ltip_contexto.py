"""Monta o contexto do LTIP (consumido por `ltip_pipeline`) a partir do banco (V1-03).

Fontes: edificação, fiscal e contrato da inspeção; ocorrências (planas, com sistema/subsistema
e `ordem`) e fotos pelo `contexto_comum`; textos e `data_emissao` do `RelatorioConteudo` (V1-01,
já mesclado com os padrões). `objeto` padrão = `contrato.objeto`; `documentacao_analisada`
padrão = texto padrão + NBRs do contrato + documentos técnicos da edificação.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Inspecao
from app.models.tipo_servico import TipoServico
from app.services import relatorio_conteudo_service
from app.services.report_generator import contexto_comum as comum
from app.services.report_generator.ltip_pipeline import SECOES_TEXTO

TIPO_LTIP = TipoServico.LTIP.value

# Campos que `ltip_template.html.j2` imprime sem fallback (assinatura, capa, ART).
CAMPOS_OBRIGATORIOS_LTIP: tuple[tuple[str, str], ...] = (
    ("edificacao", "nome"),
    ("fiscal", "nome"),
    ("fiscal", "crea"),
    ("contrato", "art_fiscalizacao"),
)


def validar_contexto_ltip(contexto: dict[str, Any]) -> list[str]:
    """Caminhos obrigatórios ausentes (`fiscal.crea`); vazia = emitível."""
    return comum.validar_obrigatorios(contexto, CAMPOS_OBRIGATORIOS_LTIP)


def extrair_fotos_ltip(contexto: dict[str, Any]) -> set[str]:
    return comum.primeiras_fotos(contexto)


def _documentacao_analisada(base: list[str], inspecao: Inspecao) -> list[str]:
    paragrafos = list(base)
    nbrs = sorted(inspecao.contrato.nbrs, key=lambda n: n.codigo_nbr)
    if nbrs:
        itens = "; ".join(f"{n.codigo_nbr} ({n.descricao})" if n.descricao else n.codigo_nbr for n in nbrs)
        paragrafos.append(f"Normas técnicas consideradas: {itens}.")
    documentos = (inspecao.contrato.edificacao.documentos_tecnicos or {}).get("itens") or []
    nomes = [
        f"{d['nome']} ({d['tipo']})" if d.get("tipo") else str(d["nome"]) for d in documentos if d.get("nome")
    ]
    if nomes:
        paragrafos.append(f"Documentos técnicos da edificação analisados: {'; '.join(nomes)}.")
    return paragrafos


def _data_emissao(valor: Any) -> str:
    data = date.fromisoformat(str(valor)[:10]) if valor else date.today()
    return data.strftime("%d/%m/%Y")


async def montar_contexto_ltip(db: AsyncSession, inspecao_id: uuid.UUID) -> dict[str, Any]:
    """Retorna o dicionário aceito por `ltip_pipeline.normalizar_contexto`.

    404 se a inspeção não existe; 409 se não é `LTIP`. Ocorrências por `seq_numero`, fotos por `ordem`.
    """
    inspecao = await comum.carregar_inspecao(db, inspecao_id, TipoServico.LTIP)
    dados = (await relatorio_conteudo_service.obter(db, inspecao_id, TipoServico.LTIP)).dados
    # Só o que o auditor salvou de fato impede os padrões montados de `objeto` e `documentacao_analisada`.
    salvo = await relatorio_conteudo_service._salvo(db, inspecao_id, TipoServico.LTIP)
    textos_salvos = (salvo.dados or {}).get("textos") or {} if salvo else {}

    contrato = inspecao.contrato
    textos = {chave: list((dados.get("textos") or {}).get(chave) or []) for chave in SECOES_TEXTO}
    if "objeto" not in textos_salvos and not comum.vazio(contrato.objeto):
        textos["objeto"] = [contrato.objeto]
    if "documentacao_analisada" not in textos_salvos:
        textos["documentacao_analisada"] = _documentacao_analisada(textos["documentacao_analisada"], inspecao)

    contexto: dict[str, Any] = {
        "inspecao": comum.inspecao_ctx(inspecao),
        "edificacao": comum.edificacao_ctx(contrato.edificacao),
        "fiscal": comum.fiscal_ctx(contrato.fiscal),
        "contrato": comum.contrato_ctx(contrato),
        "data_emissao": _data_emissao(dados.get("data_emissao")),
        "ocorrencias": comum.ocorrencias_ctx(inspecao),
    }
    if dados.get("local_emissao"):
        contexto["local_emissao"] = dados["local_emissao"]
    for chave, paragrafos in textos.items():
        contexto[f"{chave}_paragrafos"] = paragrafos
    return contexto
