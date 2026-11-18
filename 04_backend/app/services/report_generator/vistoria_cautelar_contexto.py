"""Monta o contexto da Vistoria Cautelar (consumido por `vistoria_cautelar_pipeline`) a partir do banco (V1-04).

Camada de montagem apenas: não gera arquivos nem baixa imagens. Padrão de
`rfo_contexto.py`; contrato do contexto em `00_docs/backlog-auto/vistoria-cautelar-pipeline.md`
e mapeamento em `00_docs/backlog-auto/v1-vistoria-cautelar-contexto.md`.

Fontes:
- `responsavel` ← fiscal do contrato (nome, CREA, contato, título, qualificações, assinatura);
- `obra.descricao` ← `contrato.objeto`; `edificacao.nome`; tabela 4.2 ← `Edificacao`;
- textos, datas, local, parecer, metodologia corretiva por ocorrência e fundamentação por
  sistema ← `RelatorioConteudo` (V1-01), já mesclado com os textos padrão;
- tabela 10.2, sistemas (cap. 9) e figuras (cap. 8) ← ocorrências da inspeção e suas fotos.
"""
from __future__ import annotations

import re
import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError
from app.models import Contrato, Foto, Inspecao, Ocorrencia, Responsavel
from app.models.tipo_servico import TipoServico
from app.services import relatorio_conteudo_service
from app.services.report_generator.contexto_comum import cidade_emissao
from app.services.report_generator.legenda_foto import legenda_para_relatorio

TIPO_VISTORIA_CAUTELAR = TipoServico.VISTORIA_CAUTELAR.value
VAZIO = "—"

# DEC-47 (2): o laudo não sai sem identificação técnica do signatário (fiscal) nem sem o
# parecer do item 10.1. `responsavel.nome` é NOT NULL no banco, mas entra na checagem
# para o validador valer também para contextos montados fora do banco.
CAMPOS_OBRIGATORIOS_VISTORIA_CAUTELAR: tuple[tuple[str, str], ...] = (
    ("responsavel", "nome"),
    ("responsavel", "crea"),
    ("complementos", "parecer_tecnico"),
)

# "Goiânia-GO", "Goiânia - GO", "Goiânia/GO" num dos segmentos (separados por vírgula) do endereço.
_CIDADE_UF_RE = re.compile(r"^\s*([^\d,/-]+?)\s*[-/]\s*([A-Za-z]{2})\s*$")


def _vazio(valor: Any) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


def validar_contexto_vistoria_cautelar(contexto: dict[str, Any]) -> list[str]:
    """Caminhos obrigatórios ausentes (`complementos.parecer_tecnico`); vazia = emitível."""
    return [
        f"{secao}.{campo}"
        for secao, campo in CAMPOS_OBRIGATORIOS_VISTORIA_CAUTELAR
        if _vazio((contexto.get(secao) or {}).get(campo))
    ]


def extrair_fotos_vistoria_cautelar(contexto: dict[str, Any]) -> set[str]:
    """`storage_key` que o template embute: figuras, assinatura e arte da capa."""
    chaves = {f["storage_key"] for f in contexto.get("figuras") or [] if f.get("storage_key")}
    for campo in ("assinatura_storage_key", "capa_fundo_storage_key"):
        if contexto.get(campo):
            chaves.add(contexto[campo])
    return chaves


def cidade_do_endereco(endereco: str | None) -> str | None:
    """Cidade-UF do endereço livre (`..., Goiânia-GO, 74000-000` → `Goiânia-GO`); None se não achar."""
    for segmento in reversed((endereco or "").split(",")):
        achou = _CIDADE_UF_RE.match(segmento)
        if achou:
            return f"{achou.group(1).strip()}-{achou.group(2).upper()}"
    return None


def _data_br(valor: str) -> str:
    return date.fromisoformat(valor[:10]).strftime("%d/%m/%Y")


def _datas_das_vistorias(datas: list[str]) -> list[str]:
    if not datas:
        return []
    formatadas = [_data_br(d) for d in datas]
    if len(formatadas) == 1:
        return [f"A vistoria foi realizada em {formatadas[0]}."]
    return [f"As vistorias foram realizadas em {', '.join(formatadas[:-1])} e {formatadas[-1]}."]


def _area(valor: float | None) -> str | None:
    if valor is None:
        return None
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} m²"


def _responsavel_ctx(fiscal: Responsavel) -> dict[str, Any]:
    return {
        "nome": fiscal.nome,
        "titulo_profissional": fiscal.titulo_profissional,
        "crea": fiscal.crea,
        "email": fiscal.email,
        "telefone": fiscal.telefone,
        "qualificacoes": [str(q) for q in fiscal.qualificacoes or [] if not _vazio(q)],
    }


def _tabela_identificacao(edificacao: Any) -> list[dict[str, Any]]:
    linhas = (
        ("Endereço", edificacao.endereco),
        ("CEP", edificacao.cep),
        ("Tipologia", edificacao.tipologia),
        ("Sistema construtivo", edificacao.sistema_construtivo),
        ("Pavimentos", edificacao.descricao_pavimentos),
        ("Área total construída", _area(edificacao.area_total_m2)),
    )
    return [{"aspecto_tecnico": aspecto, "descricao_detalhada": valor} for aspecto, valor in linhas]


def _fotos_ordenadas(fotos: list[Foto]) -> list[Foto]:
    return sorted(fotos, key=lambda f: (f.ordem is None, f.ordem or 0, str(f.id)))


def _sistemas(ocorrencias: list[Ocorrencia], fundamentacao: dict[str, Any]) -> list[dict[str, Any]]:
    """Capítulo 9: um item por sistema com ocorrência (ordem de `SistemaPredial.ordem`)."""
    por_sistema: dict[uuid.UUID, list[Ocorrencia]] = {}
    for oc in ocorrencias:
        por_sistema.setdefault(oc.sistema_id, []).append(oc)
    grupos = sorted(por_sistema.values(), key=lambda ocs: (ocs[0].sistema.ordem, ocs[0].sistema.nome))
    return [
        {
            "nome": ocs[0].sistema.nome,
            "constatacoes": [oc.descricao.strip() for oc in ocs if not _vazio(oc.descricao)],
            "fundamentacao_tecnica": list(fundamentacao.get(str(ocs[0].sistema_id)) or []),
        }
        for ocs in grupos
    ]


async def _carregar_inspecao(db: AsyncSession, inspecao_id: uuid.UUID) -> Inspecao:
    resultado = await db.execute(
        select(Inspecao)
        .options(
            selectinload(Inspecao.contrato).selectinload(Contrato.edificacao),
            selectinload(Inspecao.contrato).selectinload(Contrato.fiscal),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.fotos),
            selectinload(Inspecao.ocorrencias).selectinload(Ocorrencia.sistema),
        )
        .where(Inspecao.id == inspecao_id)
    )
    inspecao = resultado.scalar_one_or_none()
    if inspecao is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    if TipoServico.normalizar(inspecao.tipo) is not TipoServico.VISTORIA_CAUTELAR:
        raise ConflictError(
            f"Inspeção '{inspecao_id}' é do tipo '{inspecao.tipo}'; a Vistoria Cautelar só é gerada "
            f"para inspeções do tipo '{TIPO_VISTORIA_CAUTELAR}'.",
            type_suffix=f"inspecao-nao-{TIPO_VISTORIA_CAUTELAR.lower()}",
        )
    return inspecao


async def montar_contexto_vistoria_cautelar(db: AsyncSession, inspecao_id: uuid.UUID) -> dict[str, Any]:
    """Retorna o dicionário aceito por `vistoria_cautelar_pipeline.normalizar_contexto`.

    404 se a inspeção não existe; 409 se não é `VISTORIA_CAUTELAR`. Ocorrências saem por
    `seq_numero`, fotos por `ordem`, sistemas por `SistemaPredial.ordem`.
    """
    inspecao = await _carregar_inspecao(db, inspecao_id)
    dados = (await relatorio_conteudo_service.obter(db, inspecao_id, TipoServico.VISTORIA_CAUTELAR)).dados

    contrato = inspecao.contrato
    edificacao = contrato.edificacao
    fiscal = contrato.fiscal
    ocorrencias = sorted(inspecao.ocorrencias, key=lambda o: o.seq_numero)

    conteudo: dict[str, Any] = dict(dados.get("textos") or {})
    if not conteudo.get("datas_das_vistorias"):
        conteudo["datas_das_vistorias"] = _datas_das_vistorias(dados.get("datas_vistorias") or [])

    metodologia = dados.get("metodologia_corretiva") or {}
    plano = [
        {
            "item": str(oc.seq_numero),
            "localizacao": oc.localizacao,
            "descricao_da_pendencia": oc.descricao,
            "metodologia_corretiva_indicada": metodologia.get(str(oc.id)) or VAZIO,
        }
        for oc in ocorrencias
    ]

    figuras: list[dict[str, Any]] = []
    for oc in ocorrencias:
        for foto in _fotos_ordenadas(oc.fotos):
            # DEC-37 DP-9: só `legenda` entra; a sugestão de IA nunca, qualquer status.
            figuras.append(
                {
                    "numero": len(figuras) + 1,
                    "legenda": legenda_para_relatorio(foto) or None,
                    "storage_key": foto.storage_key,
                }
            )

    contexto: dict[str, Any] = {
        "inspecao": {"id": str(inspecao.id), "tipo": inspecao.tipo, "status": inspecao.status},
        "responsavel": _responsavel_ctx(fiscal),
        "obra": {"descricao": contrato.objeto},
        "edificacao": {"nome": edificacao.nome},
        "data_emissao": dados.get("data_emissao") or date.today().isoformat(),
        "local_emissao": dados.get("local_emissao") or cidade_emissao(edificacao, cidade_do_endereco),
        "conteudo": conteudo,
        "complementos": {"parecer_tecnico": dados.get("parecer")},
        "tabelas": {
            "identificacao": _tabela_identificacao(edificacao),
            "plano_de_correcoes_remanescentes": plano,
        },
        "sistemas": _sistemas(ocorrencias, dados.get("fundamentacao_tecnica") or {}),
        "figuras": figuras,
    }
    if fiscal.assinatura_storage_key:
        contexto["assinatura_storage_key"] = fiscal.assinatura_storage_key
    return contexto
