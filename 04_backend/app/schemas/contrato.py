"""Schemas Pydantic v2 de `Contrato` (request/response), sem lógica de negócio."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.tipo_servico import TipoServico
from app.schemas.contrato_executor import ContratoExecutorRead
from app.schemas.contrato_nbr import ContratoNbrRead
from app.schemas.inspecao import InspecaoRead


class ContratoBase(BaseModel):
    # `use_enum_values`: o enum valida e normaliza ("ltip" -> "LTIP"); o modelo grava o texto.
    model_config = ConfigDict(use_enum_values=True)

    edificacao_id: uuid.UUID
    fiscal_id: uuid.UUID
    contratante_id: uuid.UUID | None = None
    numero: str
    tipo_servico: TipoServico
    objeto: str | None = None
    data_inicio: date | None = None
    prazo_dias: int | None = None
    art_fiscalizacao: str | None = None
    observacoes_gerais: str | None = None
    status: str


class ContratoCreate(ContratoBase):
    pass


class ContratoRead(ContratoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    # Leitura tolerante: valor fora do enum gravado antes de V1-01 (ex.: "FISCALIZAÇÃO DE OBRA")
    # sai como texto em vez de derrubar a listagem com 500.
    tipo_servico: TipoServico | str
    id: uuid.UUID
    created_at: datetime


class ContratoExecutorNested(BaseModel):
    """Empresa executora dentro do payload de `Contrato` (sem `contrato_id`, atribuído pelo backend).

    `art_execucao` é obrigatória (RN-09): toda empresa executora do payload
    de criação/atualização de Contrato é considerada "aplicável" para fins de
    exigência de ART de Execução.
    """

    responsavel_legal_id: uuid.UUID
    rte_id: uuid.UUID | None = None
    razao_social: str
    cnpj: str
    endereco: str | None = None
    art_execucao: str

    @field_validator("art_execucao", "cnpj")
    @classmethod
    def _nao_vazio(cls, valor: str) -> str:
        if not valor or not valor.strip():
            raise ValueError("Campo não pode ser vazio.")
        return valor


class ContratoNbrNested(BaseModel):
    """NBR aplicável dentro do payload de `Contrato` (sem `contrato_id`)."""

    codigo_nbr: str
    descricao: str | None = None


class ContratoCreatePayload(ContratoBase):
    """Payload de `POST /contratos` — Contrato + N executoras + N NBRs (RN-06, RF-12).

    `art_fiscalizacao` é sempre obrigatória (RN-09) — sobrescreve o campo
    opcional herdado de `ContratoBase`. `status` tem default `"em_andamento"`
    pois o cliente normalmente não define o status inicial manualmente.
    """

    art_fiscalizacao: str = Field(..., min_length=1)
    status: str = "em_andamento"
    executores: list[ContratoExecutorNested] = Field(..., min_length=1)
    nbrs: list[ContratoNbrNested] = []


class ContratoUpdatePayload(ContratoCreatePayload):
    """Payload de `PUT /contratos/{id}` — substitui Contrato + executoras + NBRs."""


class ContratoDetalhe(ContratoRead):
    """Detalhe completo do Contrato: executoras, NBRs e a Inspeção originada (RN-06, RN-09)."""

    executores: list[ContratoExecutorRead] = []
    nbrs: list[ContratoNbrRead] = []
    inspecao: InspecaoRead | None = None
