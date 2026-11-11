"""Schemas Pydantic v2 de `Foto` (request/response), sem lógica de negócio."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# DEC-39 (C): domínio fechado de `origem` e tetos de `ordem`/`legenda`.
OrigemFoto = Literal["upload_manual", "lightshot", "clipboard"]
LEGENDA_MAX_LENGTH = 500
# Anotação/transcrição do auditor enviada à IA (BL-34); teto defensivo, a coluna é TEXT.
LEGENDA_BRUTA_MAX_LENGTH = 5000
# Base64 de MAX_UPLOAD_SIZE_BYTES (25 MB) = ceil(25 MiB / 3) * 4 = 34_952_536 caracteres.
IMAGEM_BASE64_MAX_LENGTH = 34_952_536
# DEC-37 (DP-1) / RF-15: espelham os CHECKs de `fotos` (app/models/foto.py).
StatusValidacaoIA = Literal["rascunho", "aprovada"]
NivelCertezaIA = Literal["constatacao_direta", "indicio_tecnico", "hipotese_tecnica", "causa_comprovada"]


class FotoBase(BaseModel):
    ocorrencia_id: uuid.UUID | None = None
    visita_id: uuid.UUID | None = None
    storage_key: str
    url_publica: str | None = None
    legenda: str | None = None
    origem: str
    ordem: int | None = None


class FotoCreate(FotoBase):
    pass


class LegendaIARead(BaseModel):
    """Campos de legenda assistida por IA (BL-36; RF-15, RN-16, RN-17; DEC-37).

    Somente leitura: são gravados pelo servidor (geração e aprovação), nunca pelo payload.
    `legenda_ia_sugerida` é a minuta da IA; a legenda final continua em `FotoBase.legenda`.
    Todos `None` = foto sem sugestão de IA.
    """

    legenda_bruta: str | None = None
    legenda_ia_sugerida: str | None = None
    nivel_certeza_ia: NivelCertezaIA | None = None
    status_validacao_ia: StatusValidacaoIA | None = None
    alertas_ia: list[str] | None = None
    pendencias_ia: list[str] | None = None
    prompt_ia_id: uuid.UUID | None = None
    prompt_conteudo_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    legenda_ia_gerada_em: datetime | None = None
    aprovado_por_id: uuid.UUID | None = None
    aprovado_em: datetime | None = None


class FotoRead(LegendaIARead, FotoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    # Somente leitura: a autoria vem do usuário autenticado, nunca do payload (RN-18).
    criado_por_id: uuid.UUID | None = None


class FotoUploadResponse(BaseModel):
    """Resposta de `POST /fotos/upload` e `POST /fotos/upload-clipboard` (BL-11).

    Apenas envia o arquivo ao storage e devolve a chave + URL pré-assinada —
    ainda não cria o registro `Foto` (isso é feito ao vincular a uma
    Ocorrência ou Visita, ver `FotoVincularPayload`).
    """

    storage_key: str
    url: str


class FotoUploadClipboardPayload(BaseModel):
    """Payload de `POST /fotos/upload-clipboard` — imagem em base64 (Opção A, clipboard paste)."""

    imagem_base64: str = Field(max_length=IMAGEM_BASE64_MAX_LENGTH)


class FotoVincularPayload(BaseModel):
    """Payload de `POST /ocorrencias/{id}/fotos` e `POST /visitas/{id}/fotos` (BL-11).

    Vincula um objeto já enviado ao storage (via `/fotos/upload` ou
    `/fotos/upload-clipboard`) a uma Ocorrência ou Visita, criando o registro `Foto`.
    """

    storage_key: str = Field(max_length=255)
    legenda: str | None = Field(default=None, max_length=LEGENDA_MAX_LENGTH)
    ordem: int | None = Field(default=None, ge=0)
    origem: OrigemFoto


class FotoDescartarUploadPayload(BaseModel):
    """Payload de `DELETE /fotos/upload` — descarta upload que nunca foi vinculado (DEC-39 D)."""

    storage_key: str = Field(max_length=255)


class FotoUpdatePayload(BaseModel):
    """Payload de `PUT /fotos/{id}` — atualiza legenda e/ou ordem e, opcionalmente, aprova a
    sugestão de IA (DEC-37 DP-3). Campo ausente preserva; `legenda: null` limpa (DP-5).

    `aprovado_por_id`, `aprovado_em` e `status_validacao_ia` não fazem parte do payload: se
    enviados, são ignorados; o servidor os grava a partir do token na aprovação.
    """

    legenda: str | None = Field(default=None, max_length=LEGENDA_MAX_LENGTH)
    ordem: int | None = Field(default=None, ge=0)
    # True aprova a sugestão: grava `legenda` (enviada ou, se ausente, a própria sugestão).
    aprovar_legenda_ia: bool = False


class LegendaIAGerarPayload(BaseModel):
    """Payload de `POST /fotos/{id}/legenda-ia/gerar` (BL-34, DEC-37 DP-4).

    `legenda_bruta` ausente reaproveita a já gravada na foto; enviada, substitui a gravada.
    """

    legenda_bruta: str | None = Field(default=None, max_length=LEGENDA_BRUTA_MAX_LENGTH)
