"""Contrato do cliente de legenda por IA (BL-37, DEC-37 DP-6), independente do provedor (B-04).

O adapter real recebe um `ContextoLegenda` cuja `legenda_bruta` já vem delimitada por
`saneamento.delimitar_legenda_bruta` (DEC-42 D): ele a envia na mensagem de usuário (junto do bloco
«DADOS DA OCORRÊNCIA»), nunca no `system` nem concatenada ao prompt versionado (SEG-IA-08).
A imagem só é passada (`imagem`) quando `enviar_imagem` do cliente é verdadeiro.
"""
import hashlib
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.services.legenda_ia.contexto import ContextoLegenda


@dataclass(frozen=True)
class LegendaIAResultado:
    legenda_sugerida: str
    alertas: list[str] = field(default_factory=list)
    pendencias: list[str] = field(default_factory=list)
    # Como o provedor foi chamado: 'texto' (sem imagem) ou 'imagem'; None para o fake.
    modo: str | None = None
    # Valor de `NIVEIS_CERTEZA_IA` (foto.py) ou None quando ausente/desconhecido (com alerta).
    nivel_certeza: str | None = None
    # Tokens da resposta, quando o provedor traz `usage`: prompt_tokens, prompt_cache_hit_tokens,
    # prompt_cache_miss_tokens, completion_tokens.
    uso: dict[str, int] | None = None
    modelo: str | None = None
    # Valor de `NIVEIS_CERTEZA_IA` (foto.py) ou None quando ausente/desconhecido (com alerta).
    nivel_certeza: str | None = None
    # Tokens da resposta, quando o provedor traz `usage`: prompt_tokens, prompt_cache_hit_tokens,
    # prompt_cache_miss_tokens, completion_tokens.
    uso: dict[str, int] | None = None
    modelo: str | None = None


@runtime_checkable
class LegendaIAClient(Protocol):
    async def gerar_legenda(
        self, contexto: ContextoLegenda, prompt: str, imagem: bytes | None = None
    ) -> LegendaIAResultado: ...


class FakeLegendaIAClient:
    """Cliente determinístico para testes: a saída depende só das entradas."""

    enviar_imagem = False

    def __init__(self) -> None:
        self.chamadas = 0

    async def gerar_legenda(
        self, contexto: ContextoLegenda, prompt: str, imagem: bytes | None = None
    ) -> LegendaIAResultado:
        self.chamadas += 1
        digest = hashlib.sha256((contexto.canonico() + prompt).encode() + (imagem or b"")).hexdigest()[:8]
        bruta = contexto.legenda_bruta
        base = bruta.strip() if bruta else "Imagem sem descrição"
        return LegendaIAResultado(
            legenda_sugerida=f"{base} [{digest}]",
            alertas=[],
            pendencias=[] if bruta else ["legenda bruta ausente"],
        )
