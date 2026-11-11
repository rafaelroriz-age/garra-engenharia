"""Cliente de legenda por IA: contrato, proteções e dependência FastAPI (BL-37, DEC-37, DEC-42).

Provedor (B-04: DeepSeek) escolhido em `obter_cliente_provedor` por `LEGENDA_IA_PROVEDOR`, e não
em `get_legenda_ia_client`, que é o ponto que aplica o limite de taxa e o saneamento.
"""
from fastapi import Depends

from app.api.deps import limitar_geracao_legenda_ia
from app.core.config import get_settings
from app.core.errors import DomainError
from app.services.legenda_ia.contexto import ContextoLegenda, montar_contexto
from app.services.legenda_ia.contrato import (
    FakeLegendaIAClient,
    LegendaIAClient,
    LegendaIAResultado,
)
from app.services.legenda_ia.deepseek import DeepSeekLegendaIAClient
from app.services.legenda_ia.saneamento import (
    ClienteLegendaIAProtegido,
    construir_limites_saida,
)

__all__ = [
    "ClienteLegendaIAProtegido",
    "ContextoLegenda",
    "DeepSeekLegendaIAClient",
    "FakeLegendaIAClient",
    "LegendaIAClient",
    "LegendaIAResultado",
    "get_legenda_ia_client",
    "montar_contexto",
    "obter_cliente_provedor",
]


def obter_cliente_provedor() -> LegendaIAClient:
    """Cliente do provedor de LLM, escolhido por `LEGENDA_IA_PROVEDOR` (DEC-37 DP-6, B-04).

    `deepseek` com chave devolve o adapter real; `fake` só vale em desenvolvimento; `deepseek`
    sem chave (só possível fora de produção) ou `fake` em produção respondem 503 (RFC 7807).
    """
    settings = get_settings()
    if settings.legenda_ia_provedor == "deepseek":
        if settings.deepseek_api_key and settings.deepseek_api_key.get_secret_value().strip():
            return DeepSeekLegendaIAClient.de_settings(settings)
    elif settings.is_development:
        return FakeLegendaIAClient()
    raise DomainError(
        "Nenhum provedor de IA está configurado para gerar legendas "
        "(defina LEGENDA_IA_PROVEDOR=deepseek e DEEPSEEK_API_KEY).",
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
