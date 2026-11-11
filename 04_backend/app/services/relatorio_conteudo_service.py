"""Service Layer do conteúdo narrativo do relatório (`RelatorioConteudo`, V1-01).

- `textos_padrao(tipo)`: textos padrão do tipo, lidos de
  `report_generator/textos_padrao/<tipo>.json` (chaves exatas do pipeline).
- `obter(db, inspecao_id, tipo)`: padrões (com `{edificacao_nome}` e
  `{edificacao_endereco}` preenchidos) mesclados por deep merge com o que foi salvo.
- `salvar(db, inspecao_id, tipo, dados, usuario_id)`: grava (upsert) o conteúdo
  editado; chave de texto que o tipo não conhece vira 422.

Contrato de `dados`: `app/schemas/relatorio_conteudo.py` e
`00_docs/backlog-auto/v1-fundacao-dados.md`.
"""
import copy
import json
import uuid
from functools import cache
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import DomainError, NotFoundError
from app.models import Contrato, Inspecao, RelatorioConteudo
from app.models.tipo_servico import TipoServico
from app.schemas.relatorio_conteudo import ConteudoDados, RelatorioConteudoRead

TEXTOS_PADRAO_DIR = Path(__file__).resolve().parent / "report_generator" / "textos_padrao"

# Tipos com textos narrativos padrão. RFO e RFIP não têm seções de texto livre
# (só `data_emissao`, `local_emissao`, `incluir_resumo` etc.).
_ARQUIVOS_PADRAO: dict[TipoServico, str] = {
    TipoServico.LTIP: "ltip.json",
    TipoServico.VISTORIA_CAUTELAR: "vistoria_cautelar.json",
    TipoServico.VISTORIA_RESIDENCIAL: "vistoria_residencial.json",
}

# Placeholders aceitos nos textos padrão; valor ausente vira '—' (DEC-33).
PLACEHOLDERS = ("edificacao_nome", "edificacao_endereco")
VAZIO = "—"


@cache
def _carregar_padrao(tipo: TipoServico) -> dict[str, list[str]]:
    arquivo = _ARQUIVOS_PADRAO.get(tipo)
    if arquivo is None:
        return {}
    with (TEXTOS_PADRAO_DIR / arquivo).open(encoding="utf-8") as f:
        return json.load(f)


def textos_padrao(tipo: TipoServico) -> dict[str, list[str]]:
    """Cópia dos textos padrão do tipo (chave do pipeline -> parágrafos)."""
    return copy.deepcopy(_carregar_padrao(tipo))


def chaves_texto(tipo: TipoServico) -> frozenset[str]:
    """Chaves de `dados.textos` aceitas para o tipo."""
    return frozenset(_carregar_padrao(tipo))


def deep_merge(base: dict[str, Any], sobre: dict[str, Any]) -> dict[str, Any]:
    """Mescla `sobre` em `base` sem mutar nenhum dos dois.

    Dicionários são mesclados recursivamente; qualquer outro valor de `sobre`
    (lista, texto, número, inclusive lista vazia) substitui o de `base`.
    """
    resultado = copy.deepcopy(base)
    for chave, valor in sobre.items():
        if isinstance(valor, dict) and isinstance(resultado.get(chave), dict):
            resultado[chave] = deep_merge(resultado[chave], valor)
        else:
            resultado[chave] = copy.deepcopy(valor)
    return resultado


def preencher_placeholders(textos: dict[str, list[str]], valores: dict[str, str | None]) -> dict[str, list[str]]:
    """Substitui `{placeholder}` conhecido; chaves `{...}` desconhecidas ficam intactas."""
    trocas = {f"{{{nome}}}": (valores.get(nome) or VAZIO) for nome in PLACEHOLDERS}

    def trocar(texto: str) -> str:
        for marcador, valor in trocas.items():
            texto = texto.replace(marcador, valor)
        return texto

    return {chave: [trocar(p) for p in paragrafos] for chave, paragrafos in textos.items()}


async def _obter_inspecao(db: AsyncSession, inspecao_id: uuid.UUID) -> Inspecao:
    result = await db.execute(
        select(Inspecao)
        .options(selectinload(Inspecao.contrato).selectinload(Contrato.edificacao))
        .where(Inspecao.id == inspecao_id)
    )
    inspecao = result.scalar_one_or_none()
    if inspecao is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    return inspecao


def _padroes(tipo: TipoServico, inspecao: Inspecao) -> dict[str, Any]:
    edificacao = inspecao.contrato.edificacao if inspecao.contrato else None
    valores = {
        "edificacao_nome": edificacao.nome if edificacao else None,
        "edificacao_endereco": edificacao.endereco if edificacao else None,
    }
    return {"textos": preencher_placeholders(textos_padrao(tipo), valores)}


async def _salvo(db: AsyncSession, inspecao_id: uuid.UUID, tipo: TipoServico) -> RelatorioConteudo | None:
    result = await db.execute(
        select(RelatorioConteudo)
        .where(RelatorioConteudo.inspecao_id == inspecao_id, RelatorioConteudo.tipo == tipo.value)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def obter(db: AsyncSession, inspecao_id: uuid.UUID, tipo: TipoServico) -> RelatorioConteudoRead:
    """Conteúdo do relatório: padrões do tipo + o que foi salvo (deep merge). 404 sem inspeção."""
    inspecao = await _obter_inspecao(db, inspecao_id)
    salvo = await _salvo(db, inspecao_id, tipo)
    dados = _padroes(tipo, inspecao)
    if salvo is not None:
        dados = deep_merge(dados, salvo.dados or {})
    return RelatorioConteudoRead(
        inspecao_id=inspecao_id,
        tipo=tipo,
        dados=dados,
        salvo=salvo is not None,
        atualizado_em=salvo.atualizado_em if salvo else None,
        atualizado_por_id=salvo.atualizado_por_id if salvo else None,
    )


def _validar_chaves_texto(tipo: TipoServico, dados: ConteudoDados) -> None:
    desconhecidas = sorted(set(dados.textos or {}) - chaves_texto(tipo))
    if desconhecidas:
        raise DomainError(
            f"Chave(s) de texto não reconhecida(s) para {tipo.value}: {', '.join(desconhecidas)}.",
            type_suffix="conteudo-chave-texto-invalida",
            title="Conteúdo do relatório inválido",
            errors=[{"loc": ["body", "dados", "textos", chave], "msg": "chave desconhecida"} for chave in desconhecidas],
        )


async def salvar(
    db: AsyncSession,
    inspecao_id: uuid.UUID,
    tipo: TipoServico,
    dados: ConteudoDados,
    *,
    usuario_id: uuid.UUID | None,
) -> RelatorioConteudoRead:
    """Grava o conteúdo editado (substitui o anterior) e devolve o resultado mesclado."""
    await _obter_inspecao(db, inspecao_id)  # 404 antes de validar/gravar
    _validar_chaves_texto(tipo, dados)
    valor = dados.model_dump(mode="json", exclude_none=True)
    comando = insert(RelatorioConteudo).values(
        id=uuid.uuid4(),
        inspecao_id=inspecao_id,
        tipo=tipo.value,
        dados=valor,
        atualizado_por_id=usuario_id,
    )
    comando = comando.on_conflict_do_update(
        constraint="uq_relatorio_conteudos_inspecao_tipo",
        set_={"dados": valor, "atualizado_por_id": usuario_id, "atualizado_em": func.now()},
    )
    await db.execute(comando)
    await db.commit()
    return await obter(db, inspecao_id, tipo)
