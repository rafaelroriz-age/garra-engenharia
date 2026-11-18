"""Telemetria de custo e cache local da legenda por IA (BL-34, R-10; plano-deepseek item 5).

- `chave_cache`: sha256 do JSON canônico (prompt + modelo + contexto), estável entre execuções.
- `buscar_em_cache`: último resultado de sucesso da API dentro do TTL (`LEGENDA_IA_CACHE_TTL_H`).
- `registrar`: grava uma linha em `chamadas_ia` (sem chave de API, prompt ou contexto enviados).
- `custo`: USD estimado a partir de `uso` e dos preços por 1M de tokens da configuração.
"""
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import ChamadaIA
from app.services.legenda_ia.contexto import ContextoLegenda
from app.services.legenda_ia.contrato import LegendaIAResultado

_UM_MILHAO = Decimal(1_000_000)
_SEIS_CASAS = Decimal("0.000001")


@dataclass(frozen=True)
class Precos:
    """Preços em USD por 1M de tokens; `None` = desconhecido (custo fica null)."""

    entrada_cache_hit: float | None = None
    entrada_cache_miss: float | None = None
    saida: float | None = None

    @classmethod
    def de_settings(cls, settings: Settings) -> "Precos":
        return cls(
            entrada_cache_hit=settings.deepseek_preco_entrada_cache_hit_usd,
            entrada_cache_miss=settings.deepseek_preco_entrada_cache_miss_usd,
            saida=settings.deepseek_preco_saida_usd,
        )


def tem_resposta():
    """Filtro SQL: a linha tem legenda de verdade. Cobre SQL NULL e JSON `null` (o ORM grava `None` em JSONB como 'null')."""
    return func.coalesce(func.jsonb_typeof(ChamadaIA.resposta), "null") != "null"


def chave_cache(prompt_hash: str, modelo: str, contexto: ContextoLegenda, extra: str = "") -> str:
    """sha256 do JSON canônico de (prompt, modelo, contexto). `extra` separa variantes (ex.: modo/imagem)."""
    corpo = {"prompt": prompt_hash, "modelo": modelo, "contexto": json.loads(contexto.canonico()), "extra": extra}
    canonico = json.dumps(corpo, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def custo(uso: dict[str, int] | None, precos: Precos) -> Decimal | None:
    """Custo estimado em USD (6 casas) ou None sem `uso` ou sem os preços necessários."""
    if not uso or precos.entrada_cache_hit is None or precos.entrada_cache_miss is None or precos.saida is None:
        return None
    hit = uso.get("prompt_cache_hit_tokens", 0)
    miss = uso.get("prompt_cache_miss_tokens")
    if miss is None:
        miss = max(uso.get("prompt_tokens", 0) - hit, 0)
    saida = uso.get("completion_tokens", 0)
    total = (
        Decimal(hit) * Decimal(str(precos.entrada_cache_hit))
        + Decimal(miss) * Decimal(str(precos.entrada_cache_miss))
        + Decimal(saida) * Decimal(str(precos.saida))
    ) / _UM_MILHAO
    return total.quantize(_SEIS_CASAS)


def _resposta(resultado: LegendaIAResultado) -> dict:
    return {
        "legenda_sugerida": resultado.legenda_sugerida,
        "alertas": list(resultado.alertas),
        "pendencias": list(resultado.pendencias),
        "nivel_certeza": resultado.nivel_certeza,
        "modo": resultado.modo,
        "modelo": resultado.modelo,
    }


def _resultado(resposta: dict) -> LegendaIAResultado:
    return LegendaIAResultado(
        legenda_sugerida=resposta["legenda_sugerida"],
        alertas=list(resposta.get("alertas") or []),
        pendencias=list(resposta.get("pendencias") or []),
        nivel_certeza=resposta.get("nivel_certeza"),
        modo=resposta.get("modo"),
        modelo=resposta.get("modelo"),
        uso=None,
    )


async def buscar_em_cache(db: AsyncSession, chave: str, ttl_h: int) -> LegendaIAResultado | None:
    """Resultado de sucesso vindo da API com a mesma chave, criado dentro do TTL; `ttl_h<=0` desliga o cache."""
    if ttl_h <= 0:
        return None
    limite = datetime.now(UTC) - timedelta(hours=ttl_h)
    linha = (
        await db.execute(
            select(ChamadaIA)
            .where(
                ChamadaIA.chave_cache == chave,
                ChamadaIA.sucesso.is_(True),
                ChamadaIA.origem == "api",
                tem_resposta(),
                ChamadaIA.criado_em >= limite,
            )
            .order_by(ChamadaIA.criado_em.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if linha is None or linha.resposta is None:  # resposta nula nunca é acerto (DEC-52)
        return None
    return _resultado(linha.resposta)


async def registrar(
    db: AsyncSession,
    *,
    chave: str,
    origem: str,
    sucesso: bool,
    provedor: str,
    modelo: str | None,
    latencia_ms: int,
    usuario_id: uuid.UUID | None = None,
    foto_id: uuid.UUID | None = None,
    modo: str | None = None,
    prompt_ia_id: uuid.UUID | None = None,
    prompt_conteudo_hash: str | None = None,
    erro_tipo: str | None = None,
    uso: dict[str, int] | None = None,
    precos: Precos | None = None,
    resultado: LegendaIAResultado | None = None,
    commit: bool = True,
) -> ChamadaIA:
    """Grava a chamada. `resultado` (saneado) só é guardado em sucesso vindo da API (serve de cache)."""
    uso = uso or {}
    hit = uso.get("prompt_cache_hit_tokens", 0)
    miss = uso.get("prompt_cache_miss_tokens", 0)
    linha = ChamadaIA(
        usuario_id=usuario_id,
        foto_id=foto_id,
        finalidade="legenda_foto",
        provedor=provedor,
        modelo=modelo,
        modo=modo,
        prompt_ia_id=prompt_ia_id,
        prompt_conteudo_hash=prompt_conteudo_hash,
        chave_cache=chave,
        origem=origem,
        sucesso=sucesso,
        erro_tipo=erro_tipo,
        tokens_prompt=uso.get("prompt_tokens", hit + miss),
        tokens_cache_hit=hit,
        tokens_cache_miss=miss,
        tokens_saida=uso.get("completion_tokens", 0),
        custo_estimado_usd=custo(uso or None, precos or Precos()) if origem == "api" else None,
        latencia_ms=latencia_ms,
        resposta=_resposta(resultado) if (resultado is not None and sucesso and origem == "api") else None,
    )
    db.add(linha)
    if commit:
        await db.commit()
    else:
        await db.flush()
    return linha
