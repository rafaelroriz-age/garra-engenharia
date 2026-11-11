"""Cliente de legenda por IA: contrato, proteções e dependência FastAPI (BL-37, DEC-37, DEC-42).

Não há provedor escolhido (B-04): `obter_cliente_provedor` responde 503. O adapter real entra
nela, e não em `get_legenda_ia_client`, que é o ponto que aplica o limite de taxa e o saneamento.
"""
from fastapi import Depends

from app.api.deps import limitar_geracao_legenda_ia
from app.core.config import get_settings
from app.core.errors import DomainError
from app.services.legenda_ia.contrato import (
    FakeLegendaIAClient,
    LegendaIAClient,
    LegendaIAResultado,
)
from app.services.legenda_ia.saneamento import (
    ClienteLegendaIAProtegido,
    construir_limites_saida,
)

__all__ = [
    "ClienteLegendaIAProtegido",
    "FakeLegendaIAClient",
    "LegendaIAClient",
    "LegendaIAResultado",
    "get_legenda_ia_client",
    "obter_cliente_provedor",
]


def obter_cliente_provedor() -> LegendaIAClient:
    """Cliente do provedor de LLM (DEC-37 DP-6).

    Enquanto o provedor não for escolhido (B-04) não há adapter concreto: a rota responde 503
    (RFC 7807). O adapter real (BL-34) passará a ser devolvido aqui.
    """
    raise DomainError(
        "Nenhum provedor de IA está configurado para gerar legendas (decisão B-04 pendente).",
        type_suffix="legenda-ia-indisponivel",
        title="Legenda por IA indisponível",
        status_code=503,
    )


async def get_legenda_ia_client(
    provedor: LegendaIAClient = Depends(obter_cliente_provedor),
    _limite: None = Depends(limitar_geracao_legenda_ia),
) -> LegendaIAClient:
    """Dependência da rota `gerar`: limite de taxa + cliente que delimita e saneia (DEC-42 C e D).

    `provedor` vem antes de `_limite` para o 503 sem provedor não gastar cota. Sobrescrever esta
    função em testes deixa as proteções de fora; para mantê-las, sobrescreva
    `obter_cliente_provedor`.
    """
    return ClienteLegendaIAProtegido(provedor, construir_limites_saida(get_settings()))
