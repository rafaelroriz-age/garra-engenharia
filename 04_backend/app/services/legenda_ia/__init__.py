"""Contrato do cliente de legenda por IA (BL-37, DEC-37 DP-6), independente do provedor (B-04)."""
import hashlib
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.core.errors import DomainError


@dataclass(frozen=True)
class LegendaIAResultado:
    legenda_sugerida: str
    alertas: list[str] = field(default_factory=list)
    pendencias: list[str] = field(default_factory=list)


@runtime_checkable
class LegendaIAClient(Protocol):
    async def gerar_legenda(
        self, imagem: bytes, prompt: str, legenda_bruta: str | None = None
    ) -> LegendaIAResultado: ...


class FakeLegendaIAClient:
    """Cliente determinístico para testes: a saída depende só das entradas."""

    def __init__(self) -> None:
        self.chamadas = 0

    async def gerar_legenda(
        self, imagem: bytes, prompt: str, legenda_bruta: str | None = None
    ) -> LegendaIAResultado:
        self.chamadas += 1
        digest = hashlib.sha256(imagem + prompt.encode()).hexdigest()[:8]
        base = legenda_bruta.strip() if legenda_bruta else "Imagem sem descrição"
        return LegendaIAResultado(
            legenda_sugerida=f"{base} [{digest}]",
            alertas=[],
            pendencias=[] if legenda_bruta else ["legenda bruta ausente"],
        )


def get_legenda_ia_client() -> LegendaIAClient:
    """Dependência FastAPI do cliente de IA (DEC-37 DP-6).

    Enquanto o provedor de LLM não for escolhido (B-04) não há adapter concreto: a rota
    responde 503 (RFC 7807). Os testes sobrescrevem esta dependência com `FakeLegendaIAClient`;
    o adapter real (BL-34) passará a ser devolvido aqui.
    """
    raise DomainError(
        "Nenhum provedor de IA está configurado para gerar legendas (decisão B-04 pendente).",
        type_suffix="legenda-ia-indisponivel",
        title="Legenda por IA indisponível",
        status_code=503,
    )
