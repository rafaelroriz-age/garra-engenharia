"""Modelos SQLAlchemy 2 (async) do domínio — 14 entidades do diagrama ER (BL-04),
mais `PromptIA` (BL-36) e `RelatorioConteudo` (V1-01).

Ver `00_docs/arquitetura.md` Seção 3. Importar deste pacote garante que todas as
classes sejam registradas na `Base.metadata` antes do uso pelo Alembic ou pelos
testes de integração.
"""
from app.models.base import Base
from app.models.contrato import Contrato
from app.models.contrato_executor import ContratoExecutor
from app.models.contrato_nbr import ContratoNbr
from app.models.edificacao import Edificacao
from app.models.foto import Foto
from app.models.inspecao import Inspecao
from app.models.localizacao import Localizacao
from app.models.ocorrencia import Ocorrencia
from app.models.prompt_ia import PromptIA
from app.models.relatorio import Relatorio
from app.models.relatorio_conteudo import RelatorioConteudo
from app.models.responsavel import Responsavel
from app.models.sistema_predial import SistemaPredial
from app.models.subsistema import Subsistema
from app.models.tipo_anomalia import TipoAnomalia
from app.models.tipo_falha import TipoFalha
from app.models.tipo_servico import TipoServico
from app.models.usuario import Usuario
from app.models.visita import Visita
from app.models.visita_mao_obra import VisitaMaoObra
from app.models.visita_medicao import VisitaMedicao

__all__ = [
    "Base",
    "Contrato",
    "ContratoExecutor",
    "ContratoNbr",
    "Edificacao",
    "Foto",
    "Inspecao",
    "Localizacao",
    "Ocorrencia",
    "PromptIA",
    "Relatorio",
    "RelatorioConteudo",
    "Responsavel",
    "SistemaPredial",
    "Subsistema",
    "TipoAnomalia",
    "TipoFalha",
    "TipoServico",
    "Usuario",
    "Visita",
    "VisitaMaoObra",
    "VisitaMedicao",
]
