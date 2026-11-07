"""Schemas Pydantic v2 de `VisitaMedicao` (request/response), sem lógica de negócio."""
import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# RF-03/DEC-29/DEC-38 (C): unidade é livre por item, mas aparada e não vazia; descrição idem;
# quantidade medida ≥ 0 e finita (NaN/Infinity rejeitados).
TextoMedicao = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
UnidadeMedicao = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
QuantidadeMedida = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class VisitaMedicaoBase(BaseModel):
    visita_id: uuid.UUID
    descricao: str
    quantidade: float
    unidade: str


class VisitaMedicaoCreate(VisitaMedicaoBase):
    pass


class VisitaMedicaoRead(VisitaMedicaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class VisitaMedicaoCreatePayload(BaseModel):
    """Payload de `POST /visitas/{id}/medicoes` e `PUT /visitas/{id}/medicoes/{item_id}`.

    `visita_id` vem do path (BL-10). O `PUT` do item substitui o registro inteiro (todos os
    campos são obrigatórios), então não há campo omitido a preservar.
    """

    model_config = ConfigDict(extra="forbid")

    descricao: TextoMedicao
    quantidade: QuantidadeMedida
    unidade: UnidadeMedicao
