"""Schemas Pydantic v2 de `Visita` (request/response), sem lógica de negócio."""
import uuid
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.foto import FotoRead
from app.schemas.visita_mao_obra import VisitaMaoObraRead
from app.schemas.visita_medicao import VisitaMedicaoRead


def _hoje_limite() -> date:
    """Maior data de visita aceita (DEC-38 B: a visita registra um dia JÁ acompanhado).

    Usa a data em UTC, que nunca fica atrás da data de Brasília (UTC-3): independe do fuso do
    servidor e não recusa a visita de hoje lançada à noite; tolera no máximo ~3 h de "amanhã".
    """
    return datetime.now(UTC).date()


def _validar_data(valor: date | None) -> date:
    if valor is None:
        raise ValueError("A data da visita é obrigatória (RN-02).")
    if valor > _hoje_limite():
        raise ValueError("A data da visita não pode ser futura (RN-01: dia de obra já acompanhado).")
    return valor


def _validar_servicos(valor: str | None) -> str:
    if valor is None or not valor.strip():
        raise ValueError("Serviços executados é obrigatório (RN-02).")
    return valor


class VisitaBase(BaseModel):
    inspecao_id: uuid.UUID
    data: date
    servicos_executados: str | None = None
    observacoes: str | None = None
    seq_numero: int


class VisitaCreate(VisitaBase):
    pass


class VisitaRead(VisitaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Somente leitura: a autoria vem do usuário autenticado, nunca do payload (RN-18).
    criado_por_id: uuid.UUID | None = None


class VisitaCreatePayload(BaseModel):
    """Payload de `POST /inspecoes/{id}/visitas` — `inspecao_id` vem do path e
    `seq_numero` é atribuído automaticamente pelo backend (RN-01, BL-10)."""

    model_config = ConfigDict(extra="forbid")

    data: date
    servicos_executados: str
    observacoes: str | None = None

    _data_valida = field_validator("data")(_validar_data)
    _servicos_obrigatorio = field_validator("servicos_executados")(_validar_servicos)


class VisitaUpdatePayload(BaseModel):
    """Payload de `PUT /visitas/{id}` — atualização PARCIAL dos campos próprios da visita (DEC-38 D).

    Campo omitido preserva o valor guardado (use `model_dump(exclude_unset=True)`); `observacoes:
    null` explícito limpa a observação. `data` e `servicos_executados` não aceitam `null`.
    Campos imutáveis (`seq_numero`, `inspecao_id`, `criado_por_id`) ou desconhecidos → 422.
    """

    model_config = ConfigDict(extra="forbid")

    data: date | None = None
    servicos_executados: str | None = None
    observacoes: str | None = None

    # Validadores "after" não rodam no default: só validam o que o cliente enviou.
    _data_valida = field_validator("data")(_validar_data)
    _servicos_obrigatorio = field_validator("servicos_executados")(_validar_servicos)


class VisitaComDetalhes(VisitaRead):
    """Visita com equipe, medições e fotos vinculadas (BL-10)."""

    mao_obra: list[VisitaMaoObraRead] = []
    medicoes: list[VisitaMedicaoRead] = []
    fotos: list[FotoRead] = []
