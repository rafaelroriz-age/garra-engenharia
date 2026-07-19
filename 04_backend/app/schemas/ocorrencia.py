"""Schemas Pydantic v2 de `Ocorrencia` (request/response), sem lógica de negócio.

Os campos de classificação (`situacao`, `classificacao`, `tipo_anomalia`,
`tipo_falha`, `grau_risco`) são texto livre nesta etapa (BL-04); validações de
RN-04/RN-05 entram nas tarefas de CRUD (BL-14 em diante).
"""
import uuid

from pydantic import BaseModel, ConfigDict


class OcorrenciaBase(BaseModel):
    inspecao_id: uuid.UUID
    sistema_id: uuid.UUID
    subsistema_id: uuid.UUID | None = None
    localizacao: str | None = None
    situacao: str
    classificacao: str
    tipo_anomalia: str | None = None
    tipo_falha: str | None = None
    grau_risco: str | None = None
    prioridade: int | None = None
    descricao: str | None = None
    gut_gravidade: float | None = None
    gut_urgencia: float | None = None
    gut_tendencia: float | None = None
    seq_numero: int


class OcorrenciaCreate(OcorrenciaBase):
    pass


class OcorrenciaRead(OcorrenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
