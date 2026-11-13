"""RAG da legenda IA por busca textual do PostgreSQL (BL-34, IA-05; plano-deepseek item 6).

«Fine-tuning por contexto» sem embeddings (a DeepSeek não tem API de embeddings) e sem novo provedor:

(a) até `k` legendas **aprovadas** pelo auditor de outras fotos, com o mesmo tipo de anomalia e/ou
    sistema, ranqueadas por afinidade (tipo e sistema iguais) e depois por `ts_rank` (FTS
    `portuguese`) + similaridade trigram (`pg_trgm`) com a legenda bruta. A própria foto e as
    legendas em rascunho ficam de fora. Viram few-shots (pares user/assistant) no adapter.
(b) até 2 trechos de referência de `trechos_conhecimento_ia` (relatórios históricos anonimizados),
    ranqueados por afinidade de sistema/tipo/grau + `ts_rank` + `word_similarity`. Vão dentro do
    bloco «DADOS DA OCORRÊNCIA» como material de apoio (SEG-IA-08: dado não confiável).
(c) as NBRs do contrato já vêm no `ContextoLegenda` (`montar_contexto`).

O texto recuperado passa por `anonimizar` (as legendas podem ser de outro cliente) e por um corte de
tamanho total (`MAX_CARACTERES`). Tempo alvo < 50 ms (medido em `ResultadoRecuperacao.ms`).
"""
import logging
import time
import uuid
from dataclasses import dataclass, replace

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Integer, String

from app.services.legenda_ia.anonimizacao import anonimizar
from app.services.legenda_ia.contexto import ContextoLegenda, ExemploLegenda, ReferenciaLegenda

logger = logging.getLogger(__name__)

MAX_CARACTERES = 2_500
MAX_REFERENCIAS = 2
_MAX_CONSULTA = 300
# Margem de candidatos: alguns podem sair no corte de tamanho.
_FOLGA = 3

# Consulta OR (qualquer termo) a partir do texto livre: plainto_tsquery usa AND, que quase nunca casa.
_TSQ = "replace(plainto_tsquery('portuguese', CAST(:consulta AS text))::text, '&', '|')::tsquery"

_SQL_EXEMPLOS = text(
    f"""
    WITH q AS (SELECT {_TSQ} AS tsq)
    SELECT f.id, f.legenda, f.legenda_bruta, f.nivel_certeza_ia, o.tipo_anomalia, s.nome AS sistema,
           o.grau_risco
    FROM fotos f
    JOIN ocorrencias o ON o.id = f.ocorrencia_id
    JOIN sistemas_prediais s ON s.id = o.sistema_id
    CROSS JOIN q
    WHERE f.status_validacao_ia = 'aprovada'
      AND f.legenda IS NOT NULL AND btrim(f.legenda) <> ''
      AND (CAST(:foto_id AS uuid) IS NULL OR f.id <> CAST(:foto_id AS uuid))
      AND (lower(o.tipo_anomalia) = lower(CAST(:tipo AS text)) OR s.nome = CAST(:sistema AS text))
    ORDER BY
      (CASE WHEN lower(o.tipo_anomalia) = lower(CAST(:tipo AS text)) THEN 1 ELSE 0 END
       + CASE WHEN s.nome = CAST(:sistema AS text) THEN 1 ELSE 0 END) DESC,
      ts_rank(to_tsvector('portuguese'::regconfig, f.legenda), q.tsq)
       + similarity(f.legenda, CAST(:bruta AS text)) DESC,
      f.aprovado_em DESC NULLS LAST
    LIMIT :limite
    """
).bindparams(
    bindparam("consulta", type_=String), bindparam("foto_id", type_=UUID(as_uuid=True)),
    bindparam("tipo", type_=String), bindparam("sistema", type_=String), bindparam("bruta", type_=String),
    bindparam("limite", type_=Integer),
)

_SQL_TRECHOS = text(
    f"""
    WITH q AS (SELECT {_TSQ} AS tsq),
    candidatos AS (
      -- Pré-seleção barata (FTS + afinidade); o trigrama só roda sobre estes.
      SELECT t.id, t.texto,
             (CASE WHEN t.sistema = CAST(:sistema AS text) THEN 0.6 ELSE 0 END
              + CASE WHEN CAST(:tipo AS text) <> '' AND t.tipo_anomalia ILIKE '%' || CAST(:tipo AS text) || '%'
                     THEN 0.3 ELSE 0 END
              + CASE WHEN t.grau_risco = CAST(:grau AS text) THEN 0.2 ELSE 0 END
              + ts_rank(t.tsv, q.tsq)) AS base
      FROM trechos_conhecimento_ia t CROSS JOIN q
      WHERE (t.tsv @@ q.tsq OR t.sistema = CAST(:sistema AS text))
        AND NOT (t.fonte = ANY(CAST(:excluir_fontes AS text[])))
      ORDER BY base DESC
      LIMIT 30
    )
    SELECT id, texto FROM candidatos
    ORDER BY base + word_similarity(CAST(:bruta AS text), texto) DESC, id
    LIMIT :limite
    """
).bindparams(
    bindparam("consulta", type_=String), bindparam("sistema", type_=String), bindparam("tipo", type_=String),
    bindparam("grau", type_=String), bindparam("bruta", type_=String), bindparam("limite", type_=Integer),
    bindparam("excluir_fontes", type_=ARRAY(String)),
)


@dataclass(frozen=True)
class ResultadoRecuperacao:
    exemplos: tuple[ExemploLegenda, ...] = ()
    referencias: tuple[ReferenciaLegenda, ...] = ()
    ms: float = 0.0

    def aplicar(self, contexto: ContextoLegenda) -> ContextoLegenda:
        return replace(contexto, exemplos=self.exemplos, referencias=self.referencias)


def texto_consulta(contexto: ContextoLegenda) -> str:
    """Texto livre da busca: legenda bruta + descrição (ou, sem elas, tipo de anomalia e sistema)."""
    partes = [contexto.legenda_bruta, contexto.descricao] if (contexto.legenda_bruta or contexto.descricao) else [
        contexto.tipo_anomalia, (contexto.sistema or "").replace("_", " "), contexto.subsistema
    ]
    return " ".join(p for p in partes if p)[:_MAX_CONSULTA]


def _custo(exemplo: ExemploLegenda) -> int:
    return len(exemplo.legenda) + len(exemplo.legenda_bruta or "")


async def buscar(
    db: AsyncSession,
    contexto: ContextoLegenda,
    k: int,
    *,
    excluir_foto_id: uuid.UUID | None = None,
    max_caracteres: int = MAX_CARACTERES,
    excluir_fontes: tuple[str, ...] = (),
) -> ResultadoRecuperacao:
    """Few-shots (a) e referências (b) para o contexto, dentro de `max_caracteres` no total.

    `excluir_fontes` tira trechos de arquivos específicos (ex.: na avaliação, o relatório de onde
    saiu o golden set, para a referência não conter a própria resposta).
    """
    inicio = time.perf_counter()
    consulta = texto_consulta(contexto)
    bruta = contexto.legenda_bruta or consulta
    orcamento = max_caracteres

    exemplos: list[ExemploLegenda] = []
    if k > 0 and (contexto.tipo_anomalia or contexto.sistema):
        linhas = (
            await db.execute(
                _SQL_EXEMPLOS.bindparams(
                    consulta=consulta, foto_id=excluir_foto_id, tipo=contexto.tipo_anomalia or "",
                    sistema=contexto.sistema or "", bruta=bruta, limite=k + _FOLGA,
                )
            )
        ).all()
        for linha in linhas:
            exemplo = ExemploLegenda(
                id=str(linha.id),
                legenda=anonimizar(linha.legenda),
                legenda_bruta=anonimizar(linha.legenda_bruta) if linha.legenda_bruta else None,
                tipo_anomalia=linha.tipo_anomalia,
                sistema=linha.sistema,
                grau_risco=linha.grau_risco,
                nivel_certeza=linha.nivel_certeza_ia,
            )
            if len(exemplos) < k and _custo(exemplo) <= orcamento:
                exemplos.append(exemplo)
                orcamento -= _custo(exemplo)

    referencias: list[ReferenciaLegenda] = []
    if consulta or contexto.sistema:
        linhas = (
            await db.execute(
                _SQL_TRECHOS.bindparams(
                    consulta=consulta, sistema=contexto.sistema or "", tipo=contexto.tipo_anomalia or "",
                    grau=contexto.grau_risco or "", bruta=bruta, limite=MAX_REFERENCIAS + _FOLGA,
                    excluir_fontes=list(excluir_fontes),
                )
            )
        ).all()
        for linha in linhas:
            if len(referencias) == MAX_REFERENCIAS or orcamento < 150:
                break
            trecho = anonimizar(linha.texto)[:orcamento]
            referencias.append(ReferenciaLegenda(id=str(linha.id), texto=trecho))
            orcamento -= len(trecho)

    ms = (time.perf_counter() - inicio) * 1000
    logger.info("RAG legenda IA: %d exemplo(s), %d referência(s) em %.1f ms", len(exemplos), len(referencias), ms)
    return ResultadoRecuperacao(tuple(exemplos), tuple(referencias), ms)
