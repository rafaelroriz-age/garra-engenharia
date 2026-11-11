"""Schemas Pydantic v2 do conteúdo narrativo do relatório (V1-01).

`ConteudoDados` é o contrato de `relatorio_conteudos.dados` (documentado em
`00_docs/backlog-auto/v1-fundacao-dados.md`). Todos os campos são opcionais: o
que não vier usa o padrão do tipo (textos) ou o valor calculado na emissão.
Tetos por texto, por lista e no total impedem payload gigante (OWASP A04).
"""
import json
import uuid
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.tipo_servico import TipoServico

TEXTO_MAX = 20_000  # caracteres por parágrafo/texto
CAMPO_CURTO_MAX = 200  # local de emissão, unidade
PARAGRAFOS_MAX = 200  # parágrafos por chave de texto
CHAVES_TEXTO_MAX = 100  # chaves em `textos`
MAPA_MAX_ITENS = 1_000  # entradas em metodologia_corretiva / fundamentacao_tecnica
DATAS_VISTORIAS_MAX = 60
DADOS_MAX_CARACTERES = 500_000  # JSON serializado de `dados`, no total

Texto = Annotated[str, StringConstraints(max_length=TEXTO_MAX)]
CampoCurto = Annotated[str, StringConstraints(strip_whitespace=True, max_length=CAMPO_CURTO_MAX)]
ChaveTexto = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,79}$")]
Paragrafos = Annotated[list[Texto], Field(max_length=PARAGRAFOS_MAX)]


def em_paragrafos(valor: str | list[str]) -> list[str]:
    """Texto livre (um parágrafo por linha não vazia) ou lista -> lista de parágrafos."""
    if isinstance(valor, str):
        return [linha.strip() for linha in valor.splitlines() if linha.strip()]
    return list(valor)


class ConteudoDados(BaseModel):
    """Campos aceitos em `dados`. Chave desconhecida -> 422 (`extra="forbid"`)."""

    model_config = ConfigDict(extra="forbid")

    textos: dict[ChaveTexto, Paragrafos | Texto] | None = Field(None, max_length=CHAVES_TEXTO_MAX)
    data_emissao: date | None = None
    local_emissao: CampoCurto | None = None
    parecer: Texto | None = None
    unidade: CampoCurto | None = None
    datas_vistorias: list[date] | None = Field(None, max_length=DATAS_VISTORIAS_MAX)
    incluir_resumo: bool | None = None
    metodologia_corretiva: dict[uuid.UUID, Texto] | None = Field(None, max_length=MAPA_MAX_ITENS)
    fundamentacao_tecnica: dict[uuid.UUID, Paragrafos] | None = Field(None, max_length=MAPA_MAX_ITENS)

    @field_validator("textos")
    @classmethod
    def _textos_em_paragrafos(cls, valor: dict[str, Any] | None) -> dict[str, list[str]] | None:
        if valor is None:
            return None
        return {chave: em_paragrafos(texto) for chave, texto in valor.items()}

    @model_validator(mode="after")
    def _teto_total(self) -> "ConteudoDados":
        total = len(json.dumps(self.model_dump(mode="json", exclude_none=True), ensure_ascii=False))
        if total > DADOS_MAX_CARACTERES:
            raise ValueError(
                f"Conteúdo do relatório muito grande: {total} caracteres (máximo {DADOS_MAX_CARACTERES})."
            )
        return self


class RelatorioConteudoUpdate(BaseModel):
    """Payload de `PUT /inspecoes/{id}/conteudo/{tipo}`: substitui o conteúdo salvo."""

    model_config = ConfigDict(extra="forbid")

    dados: ConteudoDados


class RelatorioConteudoRead(BaseModel):
    """Resposta de GET/PUT: padrões do tipo mesclados (deep merge) com o que foi salvo."""

    inspecao_id: uuid.UUID
    tipo: TipoServico
    dados: dict[str, Any]
    salvo: bool = Field(description="Há conteúdo salvo para esta inspeção e tipo (senão, só padrões).")
    atualizado_em: datetime | None = None
    atualizado_por_id: uuid.UUID | None = None
