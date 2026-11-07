"""Schemas Pydantic v2 (request/response) das 14 entidades do diagrama ER (BL-04).

Sem lógica de negócio (validações RN-XX) — apenas os campos dos modelos SQLAlchemy.
Ver `00_docs/arquitetura.md` Seção 3.
"""
from app.schemas.auth import LoginRequest, Token
from app.schemas.common import PaginatedResponse
from app.schemas.contrato import (
    ContratoBase,
    ContratoCreate,
    ContratoCreatePayload,
    ContratoDetalhe,
    ContratoExecutorNested,
    ContratoNbrNested,
    ContratoRead,
    ContratoUpdatePayload,
)
from app.schemas.contrato_executor import (
    ContratoExecutorBase,
    ContratoExecutorCreate,
    ContratoExecutorRead,
)
from app.schemas.contrato_nbr import ContratoNbrBase, ContratoNbrCreate, ContratoNbrRead
from app.schemas.edificacao import (
    EdificacaoBase,
    EdificacaoComContratos,
    EdificacaoCreate,
    EdificacaoRead,
    EdificacaoUpdate,
)
from app.schemas.foto import (
    FotoBase,
    FotoCreate,
    FotoRead,
    FotoUpdatePayload,
    FotoUploadClipboardPayload,
    FotoUploadResponse,
    FotoVincularPayload,
    LegendaIARead,
)
from app.schemas.inspecao import InspecaoBase, InspecaoCreate, InspecaoDetalhe, InspecaoRead
from app.schemas.localizacao import LocalizacaoBase, LocalizacaoCreate, LocalizacaoRead
from app.schemas.ocorrencia import OcorrenciaBase, OcorrenciaCreate, OcorrenciaRead
from app.schemas.prompt_ia import PromptIABase, PromptIACreate, PromptIARead
from app.schemas.relatorio import RelatorioBase, RelatorioCreate, RelatorioRead
from app.schemas.responsavel import ResponsavelBase, ResponsavelCreate, ResponsavelRead
from app.schemas.sistema_predial import (
    SistemaPredialBase,
    SistemaPredialComSubsistemas,
    SistemaPredialCreate,
    SistemaPredialRead,
)
from app.schemas.subsistema import SubsistemaBase, SubsistemaCreate, SubsistemaRead
from app.schemas.tipo_anomalia import TipoAnomaliaBase, TipoAnomaliaCreate, TipoAnomaliaRead
from app.schemas.tipo_falha import TipoFalhaBase, TipoFalhaCreate, TipoFalhaRead
from app.schemas.usuario import UsuarioBase, UsuarioCreate, UsuarioRead
from app.schemas.visita import (
    VisitaBase,
    VisitaComDetalhes,
    VisitaCreate,
    VisitaCreatePayload,
    VisitaRead,
    VisitaUpdatePayload,
)
from app.schemas.visita_mao_obra import (
    VisitaMaoObraBase,
    VisitaMaoObraCreate,
    VisitaMaoObraCreatePayload,
    VisitaMaoObraRead,
)
from app.schemas.visita_medicao import (
    VisitaMedicaoBase,
    VisitaMedicaoCreate,
    VisitaMedicaoCreatePayload,
    VisitaMedicaoRead,
)

__all__ = [
    "ContratoBase",
    "ContratoCreate",
    "ContratoCreatePayload",
    "ContratoDetalhe",
    "ContratoExecutorBase",
    "ContratoExecutorCreate",
    "ContratoExecutorNested",
    "ContratoExecutorRead",
    "ContratoNbrBase",
    "ContratoNbrCreate",
    "ContratoNbrNested",
    "ContratoNbrRead",
    "ContratoRead",
    "ContratoUpdatePayload",
    "EdificacaoBase",
    "EdificacaoComContratos",
    "EdificacaoCreate",
    "EdificacaoRead",
    "EdificacaoUpdate",
    "FotoBase",
    "FotoCreate",
    "FotoRead",
    "FotoUpdatePayload",
    "FotoUploadClipboardPayload",
    "FotoUploadResponse",
    "FotoVincularPayload",
    "InspecaoBase",
    "InspecaoCreate",
    "InspecaoDetalhe",
    "InspecaoRead",
    "LegendaIARead",
    "LocalizacaoBase",
    "LocalizacaoCreate",
    "LocalizacaoRead",
    "LoginRequest",
    "OcorrenciaBase",
    "OcorrenciaCreate",
    "OcorrenciaRead",
    "PaginatedResponse",
    "PromptIABase",
    "PromptIACreate",
    "PromptIARead",
    "RelatorioBase",
    "RelatorioCreate",
    "RelatorioRead",
    "ResponsavelBase",
    "ResponsavelCreate",
    "ResponsavelRead",
    "SistemaPredialBase",
    "SistemaPredialComSubsistemas",
    "SistemaPredialCreate",
    "SistemaPredialRead",
    "SubsistemaBase",
    "SubsistemaCreate",
    "SubsistemaRead",
    "TipoAnomaliaBase",
    "TipoAnomaliaCreate",
    "TipoAnomaliaRead",
    "TipoFalhaBase",
    "TipoFalhaCreate",
    "TipoFalhaRead",
    "Token",
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioRead",
    "VisitaBase",
    "VisitaComDetalhes",
    "VisitaCreate",
    "VisitaCreatePayload",
    "VisitaMaoObraBase",
    "VisitaMaoObraCreate",
    "VisitaMaoObraCreatePayload",
    "VisitaMaoObraRead",
    "VisitaMedicaoBase",
    "VisitaMedicaoCreate",
    "VisitaMedicaoCreatePayload",
    "VisitaMedicaoRead",
    "VisitaRead",
    "VisitaUpdatePayload",
]
