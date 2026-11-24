"""Unicidade de (inspecao_id, tipo, versao) em `relatorios` (DEC-48 P3).

Roda contra o PostgreSQL real do `05_infra/docker-compose.yml`.
"""
import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contrato, Edificacao, Inspecao, Relatorio, Responsavel


@pytest_asyncio.fixture
async def inspecao(db_session: AsyncSession):
    ed = Edificacao(
        nome="Ed. Unicidade", endereco="Rua X, 1", cep="12345-000", tipologia="Residencial",
        sistema_construtivo="Concreto armado", area_total_m2=100.0, documentos_tecnicos={},
    )
    resp = Responsavel(nome="Eng. Teste", tipo="fiscal", crea="1-SP")
    db_session.add_all([ed, resp])
    await db_session.commit()
    ct = Contrato(edificacao_id=ed.id, fiscal_id=resp.id, numero="CT-UNQ/2026",
                  tipo_servico="Fiscalização", status="ativo")
    db_session.add(ct)
    await db_session.commit()
    insp = Inspecao(contrato_id=ct.id, tipo="RFO", status="em_andamento")
    db_session.add(insp)
    await db_session.commit()
    ids = (insp.id, ct.id, resp.id, ed.id)
    yield insp
    # Após o rollback os objetos expiram; `session.delete(obj)` tentaria lazy-load das
    # relações fora do greenlet (MissingGreenlet). Apaga por id, na ordem das FKs.
    await db_session.rollback()
    insp_id, ct_id, resp_id, ed_id = ids
    await db_session.execute(delete(Relatorio).where(Relatorio.inspecao_id == insp_id))
    await db_session.execute(delete(Inspecao).where(Inspecao.id == insp_id))
    await db_session.execute(delete(Contrato).where(Contrato.id == ct_id))
    await db_session.execute(delete(Responsavel).where(Responsavel.id == resp_id))
    await db_session.execute(delete(Edificacao).where(Edificacao.id == ed_id))
    await db_session.commit()


def _rel(insp, tipo="RFO", versao="V01"):
    return Relatorio(inspecao_id=insp.id, tipo=tipo, versao=versao, status="emitido")


async def test_duplicata_levanta_integrity_error(db_session: AsyncSession, inspecao):
    db_session.add(_rel(inspecao))
    await db_session.commit()
    db_session.add(_rel(inspecao))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_versoes_e_tipos_diferentes_coexistem(db_session: AsyncSession, inspecao):
    db_session.add_all([_rel(inspecao, "RFO", "V01"), _rel(inspecao, "RFO", "V02"),
                        _rel(inspecao, "LTIP", "V01")])
    await db_session.commit()


@pytest.mark.skip(reason="emitir_rfo (app/services/relatorio_service.py) não existe nesta "
                         "branch; habilitar após integrar o endpoint de emissão do RFO (DEC-48).")
async def test_emissao_sequencial_dupla_gera_v01_v02():
    """Duas chamadas seguidas de `emitir_rfo` (storage/gerador fake) devem gerar V01 e V02."""
