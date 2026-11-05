"""Schemas Pydantic v2 de `VisitaMaoObra` (request/response), sem lógica de negócio."""
import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# RN-02/DEC-38 (C): função aparada e não vazia; quantidade inteira 1..32767 (cabe com folga na
# coluna `Integer` e evita o 500 de overflow do int32 no PostgreSQL).
FuncaoMaoObra = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
QuantidadeProfissionais = Annotated[int, Field(ge=1, le=32767)]


class VisitaMaoObraBase(BaseModel):
    visita_id: uuid.UUID
    funcao: str
    quantidade: int


class VisitaMaoObraCreate(VisitaMaoObraBase):
    pass


class VisitaMaoObraRead(VisitaMaoObraBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class VisitaMaoObraCreatePayload(BaseModel):
    """Payload de `POST /visitas/{id}/mao-obra` e `PUT /visitas/{id}/mao-obra/{item_id}`.

    `visita_id` vem do path (BL-10). O `PUT` do item substitui o registro inteiro (são só dois
    campos, ambos obrigatórios), então não há campo omitido a preservar.
    """

    model_config = ConfigDict(extra="forbid")

    funcao: FuncaoMaoObra
    quantidade: QuantidadeProfissionais
