"""Schemas Pydantic v2 de `Ocorrencia` (request/response), sem lógica de negócio.

Os campos de classificação (`situacao`, `classificacao`, `tipo_anomalia`,
`tipo_falha`, `grau_risco`) são texto livre nesta etapa (BL-04); validações de
RN-04/RN-05 entram nas tarefas de CRUD (BL-14 em diante).
"""
import uuid
from datetime import datetime

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
    seq_numero: int | None = None


class OcorrenciaCreate(OcorrenciaBase):
    pass


class OcorrenciaRead(OcorrenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Somente leitura: a autoria vem do usuário autenticado, nunca do payload (RN-18).
    criado_por_id: uuid.UUID | None = None
    # RN-04/DEC-29 (BL-15): sugestão derivada do Grau de Risco e rastreio da
    # sobrescrita explícita — calculadas no backend, nunca aceitas do payload.
    prioridade_sugerida: int | None = None
    prioridade_ajustada_por_id: uuid.UUID | None = None
    prioridade_ajustada_em: datetime | None = None
