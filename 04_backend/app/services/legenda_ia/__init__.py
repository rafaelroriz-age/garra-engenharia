"""Contrato do cliente de legenda por IA (BL-37, DEC-37 DP-6), independente do provedor (B-04)."""
import hashlib
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


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
