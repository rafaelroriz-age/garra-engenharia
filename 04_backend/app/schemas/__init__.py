"""Schemas Pydantic v2 (request/response) das 14 entidades do diagrama ER (BL-04).

Sem lógica de negócio (validações RN-XX) — apenas os campos dos modelos SQLAlchemy.
Ver `00_docs/arquitetura.md` Seção 3.
"""
from app.schemas.contrato import ContratoBase, ContratoCreate, ContratoRead
from app.schemas.contrato_executor import (
    ContratoExecutorBase,
    ContratoExecutorCreate,
    ContratoExecutorRead,
)
from app.schemas.contrato_nbr import ContratoNbrBase, ContratoNbrCreate, ContratoNbrRead
from app.schemas.edificacao import EdificacaoBase, EdificacaoCreate, EdificacaoRead
from app.schemas.foto import FotoBase, FotoCreate, FotoRead
from app.schemas.inspecao import InspecaoBase, InspecaoCreate, InspecaoRead
from app.schemas.localizacao import LocalizacaoBase, LocalizacaoCreate, LocalizacaoRead
from app.schemas.ocorrencia import OcorrenciaBase, OcorrenciaCreate, OcorrenciaRead
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
from app.schemas.visita import VisitaBase, VisitaCreate, VisitaRead
from app.schemas.visita_mao_obra import (
    VisitaMaoObraBase,
    VisitaMaoObraCreate,
    VisitaMaoObraRead,
)
from app.schemas.visita_medicao import (
    VisitaMedicaoBase,
    VisitaMedicaoCreate,
    VisitaMedicaoRead,
)

__all__ = [
    "ContratoBase",
    "ContratoCreate",
    "ContratoRead",
    "ContratoExecutorBase",
    "ContratoExecutorCreate",
    "ContratoExecutorRead",
    "ContratoNbrBase",
    "ContratoNbrCreate",
    "ContratoNbrRead",
    "EdificacaoBase",
    "EdificacaoCreate",
    "EdificacaoRead",
    "FotoBase",
    "FotoCreate",
    "FotoRead",
    "InspecaoBase",
    "InspecaoCreate",
    "InspecaoRead",
    "OcorrenciaBase",
    "OcorrenciaCreate",
    "OcorrenciaRead",
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
    "LocalizacaoBase",
    "LocalizacaoCreate",
    "LocalizacaoRead",
    "VisitaBase",
    "VisitaCreate",
    "VisitaRead",
    "VisitaMaoObraBase",
    "VisitaMaoObraCreate",
    "VisitaMaoObraRead",
    "VisitaMedicaoBase",
    "VisitaMedicaoCreate",
    "VisitaMedicaoRead",
]
