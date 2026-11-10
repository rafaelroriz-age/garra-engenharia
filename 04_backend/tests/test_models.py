"""Testes de integração dos modelos SQLAlchemy (BL-04).

Cria um registro de cada entidade principal (`Edificacao`, `Contrato`,
`Inspecao`) e valida os relacionamentos entre elas e com as demais entidades
do diagrama ER (`00_docs/arquitetura.md` Seção 3). Roda contra o PostgreSQL
real do `05_infra/docker-compose.yml` — necessário pelo uso de `JSONB`,
específico do dialeto PostgreSQL. Cada teste remove os registros que criou.
"""
from datetime import date

import pytest_asyncio
from app.models import (
    Contrato,
    ContratoExecutor,
    ContratoNbr,
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    Relatorio,
    Responsavel,
    SistemaPredial,
    Subsistema,
    Visita,
    VisitaMaoObra,
    VisitaMedicao,
)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def edificacao(db_session: AsyncSession):
    obj = Edificacao(
        nome="Cond. Cortina D'Ampezzo",
        endereco="Rua Exemplo, 123",
        cep="12345-000",
        tipologia="Residencial",
        sistema_construtivo="Concreto armado",
        area_total_m2=5000.0,
        documentos_tecnicos={"projeto_estrutural": "analisado"},
    )
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    yield obj
    await db_session.delete(obj)
    await db_session.commit()


@pytest_asyncio.fixture
async def responsavel(db_session: AsyncSession):
    obj = Responsavel(nome="Eng. Fulano de Tal", tipo="fiscal", crea="123456-SP")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    yield obj
    await db_session.delete(obj)
    await db_session.commit()


@pytest_asyncio.fixture
async def contrato(db_session: AsyncSession, edificacao: Edificacao, responsavel: Responsavel):
    obj = Contrato(
        edificacao_id=edificacao.id,
        fiscal_id=responsavel.id,
        numero="CT-001/2026",
        tipo_servico="Fiscalização de obra",
        status="ativo",
    )
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    yield obj
    await db_session.delete(obj)
    await db_session.commit()


@pytest_asyncio.fixture
async def inspecao(db_session: AsyncSession, contrato: Contrato):
    obj = Inspecao(contrato_id=contrato.id, tipo="RFO", status="em_andamento")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    yield obj
    await db_session.delete(obj)
    await db_session.commit()


async def test_criar_edificacao_com_documentos_tecnicos(edificacao: Edificacao):
    assert edificacao.id is not None
    assert edificacao.documentos_tecnicos == {"projeto_estrutural": "analisado"}
    assert edificacao.created_at is not None


async def test_criar_contrato_vinculado_a_edificacao_e_fiscal(
    db_session: AsyncSession, contrato: Contrato, edificacao: Edificacao, responsavel: Responsavel
):
    await db_session.refresh(edificacao, attribute_names=["contratos"])
    assert contrato.edificacao_id == edificacao.id
    assert contrato.fiscal_id == responsavel.id
    assert contrato in edificacao.contratos


async def test_criar_inspecao_um_para_um_com_contrato(
    db_session: AsyncSession, inspecao: Inspecao, contrato: Contrato
):
    await db_session.refresh(contrato, attribute_names=["inspecao"])
    assert inspecao.contrato_id == contrato.id
    assert contrato.inspecao.id == inspecao.id


async def test_contrato_executor_com_responsavel_legal_e_rte_distintos(
    db_session: AsyncSession, contrato: Contrato
):
    responsavel_legal = Responsavel(nome="Empresa X Ltda - Sócio", tipo="responsavel_legal")
    rte = Responsavel(nome="Eng. RTE", tipo="rte", crea="654321-SP")
    db_session.add_all([responsavel_legal, rte])
    await db_session.commit()
    await db_session.refresh(responsavel_legal)
    await db_session.refresh(rte)

    executor = ContratoExecutor(
        contrato_id=contrato.id,
        responsavel_legal_id=responsavel_legal.id,
        rte_id=rte.id,
        razao_social="Empresa X Ltda",
        cnpj="12.345.678/0001-90",
        art_execucao="ART-999",
    )
    nbr = ContratoNbr(contrato_id=contrato.id, codigo_nbr="NBR 5674", descricao="Manutenção de edificações")
    db_session.add_all([executor, nbr])
    await db_session.commit()
    await db_session.refresh(executor)
    await db_session.refresh(nbr)

    await db_session.refresh(contrato, attribute_names=["executores", "nbrs"])
    assert executor in contrato.executores
    assert nbr in contrato.nbrs
    assert executor.responsavel_legal_id == responsavel_legal.id
    assert executor.rte_id == rte.id

    await db_session.delete(executor)
    await db_session.delete(nbr)
    await db_session.delete(responsavel_legal)
    await db_session.delete(rte)
    await db_session.commit()


async def test_visita_com_mao_de_obra_medicao_e_foto(db_session: AsyncSession, inspecao: Inspecao):
    visita = Visita(inspecao_id=inspecao.id, data=date(2026, 7, 17), seq_numero=1)
    db_session.add(visita)
    await db_session.commit()
    await db_session.refresh(visita)

    mao_obra = VisitaMaoObra(visita_id=visita.id, funcao="Pedreiro", quantidade=3)
    medicao = VisitaMedicao(visita_id=visita.id, descricao="Concreto lançado", quantidade=12.5, unidade="m3")
    foto = Foto(visita_id=visita.id, storage_key="fotos/visita-01.jpg", origem="upload")
    db_session.add_all([mao_obra, medicao, foto])
    await db_session.commit()
    await db_session.refresh(mao_obra)
    await db_session.refresh(medicao)
    await db_session.refresh(foto)

    await db_session.refresh(visita, attribute_names=["mao_obra", "medicoes", "fotos"])
    assert mao_obra in visita.mao_obra
    assert medicao in visita.medicoes
    assert foto in visita.fotos

    await db_session.delete(mao_obra)
    await db_session.delete(medicao)
    await db_session.delete(foto)
    await db_session.delete(visita)
    await db_session.commit()


async def test_ocorrencia_com_sistema_subsistema_foto_e_relatorio_da_inspecao(
    db_session: AsyncSession, inspecao: Inspecao
):
    sistema = SistemaPredial(nome="Elétrico", ordem=1)
    db_session.add(sistema)
    await db_session.commit()
    await db_session.refresh(sistema)

    subsistema = Subsistema(sistema_id=sistema.id, nome="Iluminação", ordem=1)
    db_session.add(subsistema)
    await db_session.commit()
    await db_session.refresh(subsistema)

    ocorrencia = Ocorrencia(
        inspecao_id=inspecao.id,
        sistema_id=sistema.id,
        subsistema_id=subsistema.id,
        situacao="Não Conforme",
        classificacao="Anomalia",
        seq_numero=1,
    )
    db_session.add(ocorrencia)
    await db_session.commit()
    await db_session.refresh(ocorrencia)

    foto = Foto(ocorrencia_id=ocorrencia.id, storage_key="fotos/ocorrencia-01.jpg", origem="upload")
    relatorio = Relatorio(inspecao_id=inspecao.id, versao="v1", tipo="RFO", status="rascunho")
    db_session.add_all([foto, relatorio])
    await db_session.commit()
    await db_session.refresh(foto)
    await db_session.refresh(relatorio)

    await db_session.refresh(sistema, attribute_names=["subsistemas", "ocorrencias"])
    await db_session.refresh(subsistema, attribute_names=["ocorrencias"])
    await db_session.refresh(ocorrencia, attribute_names=["fotos"])
    await db_session.refresh(inspecao, attribute_names=["ocorrencias", "relatorios"])

    assert subsistema in sistema.subsistemas
    assert ocorrencia in sistema.ocorrencias
    assert ocorrencia in subsistema.ocorrencias
    assert foto in ocorrencia.fotos
    assert ocorrencia in inspecao.ocorrencias
    assert relatorio in inspecao.relatorios

    await db_session.delete(foto)
    await db_session.delete(relatorio)
    await db_session.delete(ocorrencia)
    await db_session.delete(subsistema)
    await db_session.delete(sistema)
    await db_session.commit()
