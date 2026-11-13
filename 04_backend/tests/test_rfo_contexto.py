"""Testes da montagem do contexto do RFO a partir do banco (BL-13).

Os testes com banco exigem o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433).
"""
import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest
import pytest_asyncio
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import delete

from app.core.errors import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import (
    Contrato,
    ContratoExecutor,
    ContratoNbr,
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    Responsavel,
    SistemaPredial,
    Visita,
    VisitaMaoObra,
    VisitaMedicao,
)
from app.models.usuario import Usuario
from app.services.report_generator import rfo_pipeline
from app.services.report_generator.rfo_contexto import montar_contexto_rfo


async def _criar_inspecao(db, tipo: str = "RFO"):
    edificacao = Edificacao(nome=f"Ed. BL-13 {uuid.uuid4()}", endereco="Rua RFO, 10", tipologia="residencial")
    fiscal = Responsavel(nome="Eng. Fiscal", tipo="fiscal", crea="111-GO", email="fiscal@example.com")
    legal = Responsavel(nome="Resp. Legal", tipo="responsavel_legal", cpf_cnpj="000")
    sistema = SistemaPredial(nome=f"Sistema BL-13 {uuid.uuid4()}", ordem=999)
    db.add_all([edificacao, fiscal, legal, sistema])
    await db.commit()
    contrato = Contrato(
        edificacao_id=edificacao.id,
        fiscal_id=fiscal.id,
        numero=f"CT-BL13-{uuid.uuid4()}",
        tipo_servico="Fiscalização",
        status="em_andamento",
        objeto="Impermeabilização",
        data_inicio=date(2026, 1, 5),
        prazo_dias=50,
        art_fiscalizacao="ART-1",
    )
    db.add(contrato)
    await db.commit()
    db.add_all(
        [
            ContratoExecutor(
                contrato_id=contrato.id, responsavel_legal_id=legal.id, razao_social="Executora X",
                cnpj="00.000.000/0001-00", art_execucao="ART-9",
            ),
            ContratoNbr(contrato_id=contrato.id, codigo_nbr="NBR 9575", descricao="Impermeabilização"),
        ]
    )
    insp = Inspecao(contrato_id=contrato.id, tipo=tipo, status="em_andamento")
    db.add(insp)
    await db.commit()
    return SimpleNamespace(inspecao=insp, contrato=contrato, edificacao=edificacao, fiscal=fiscal, legal=legal, sistema=sistema)


async def _limpar(db, d) -> None:
    from sqlalchemy import delete, select

    visitas = (await db.execute(select(Visita.id).where(Visita.inspecao_id == d.inspecao.id))).scalars().all()
    ocs = (await db.execute(select(Ocorrencia.id).where(Ocorrencia.inspecao_id == d.inspecao.id))).scalars().all()
    await db.execute(delete(Foto).where(Foto.visita_id.in_(visitas) | Foto.ocorrencia_id.in_(ocs)))
    await db.execute(delete(VisitaMaoObra).where(VisitaMaoObra.visita_id.in_(visitas)))
    await db.execute(delete(VisitaMedicao).where(VisitaMedicao.visita_id.in_(visitas)))
    await db.execute(delete(Ocorrencia).where(Ocorrencia.inspecao_id == d.inspecao.id))
    await db.execute(delete(Visita).where(Visita.inspecao_id == d.inspecao.id))
    await db.execute(delete(Inspecao).where(Inspecao.id == d.inspecao.id))
    await db.execute(delete(ContratoExecutor).where(ContratoExecutor.contrato_id == d.contrato.id))
    await db.execute(delete(ContratoNbr).where(ContratoNbr.contrato_id == d.contrato.id))
    await db.execute(delete(Contrato).where(Contrato.id == d.contrato.id))
    await db.execute(delete(Responsavel).where(Responsavel.id.in_([d.fiscal.id, d.legal.id])))
    await db.execute(delete(Edificacao).where(Edificacao.id == d.edificacao.id))
    await db.execute(delete(SistemaPredial).where(SistemaPredial.id == d.sistema.id))
    await db.commit()


@pytest_asyncio.fixture
async def rfo_vazio(db_session):
    d = await _criar_inspecao(db_session)
    yield d
    await _limpar(db_session, d)


@pytest_asyncio.fixture
async def rfo_completo(db_session):
    d = await _criar_inspecao(db_session)
    # Inseridas fora de ordem para provar a ordenação por seq_numero / ordem.
    v2 = Visita(inspecao_id=d.inspecao.id, data=date(2026, 1, 7), servicos_executados="Manta\nPrimer", seq_numero=2)
    v1 = Visita(inspecao_id=d.inspecao.id, data=date(2026, 1, 6), servicos_executados="Escarificação", observacoes="Sem placa", seq_numero=1)
    db_session.add_all([v2, v1])
    await db_session.commit()
    db_session.add_all(
        [
            VisitaMaoObra(visita_id=v1.id, funcao="Pedreiro", quantidade=2),
            VisitaMedicao(visita_id=v1.id, descricao="Área", quantidade=120.5, unidade="m²"),
            Foto(visita_id=v1.id, storage_key="k/b.jpg", legenda="Segunda", origem="upload", ordem=2),
            Foto(visita_id=v1.id, storage_key="k/a.jpg", legenda="Primeira", origem="upload", ordem=1),
        ]
    )
    ocs = [
        Ocorrencia(inspecao_id=d.inspecao.id, sistema_id=d.sistema.id, situacao="aberta", classificacao="anomalia", seq_numero=n)
        for n in (3, 1, 2)
    ]
    db_session.add_all(ocs)
    await db_session.commit()
    db_session.add(Foto(ocorrencia_id=ocs[0].id, storage_key="k/oc.jpg", origem="upload", ordem=1))
    await db_session.commit()
    yield d
    await _limpar(db_session, d)


async def test_cenario_completo(db_session, rfo_completo):
    ctx = await montar_contexto_rfo(db_session, rfo_completo.inspecao.id)

    assert ctx["contrato"]["numero"] == rfo_completo.contrato.numero
    assert ctx["contrato"]["data_inicio"] == "05/01/2026"
    assert ctx["edificacao"]["endereco"] == "Rua RFO, 10"
    assert ctx["fiscal"]["crea"] == "111-GO"
    assert ctx["executores"][0]["razao_social"] == "Executora X"
    assert ctx["executores"][0]["responsavel_legal"]["nome"] == "Resp. Legal"
    assert ctx["nbrs"][0]["codigo_nbr"] == "NBR 9575"

    assert [v["seq_numero"] for v in ctx["visitas"]] == [1, 2]
    v1 = ctx["visitas"][0]
    assert v1["mao_obra"] == [{"funcao": "Pedreiro", "quantidade": 2}]
    assert v1["medicoes"] == [{"descricao": "Área", "quantidade": 120.5, "unidade": "m²"}]
    assert [f["storage_key"] for f in v1["fotos"]] == ["k/a.jpg", "k/b.jpg"]
    assert ctx["visitas"][1]["fotos"] == []

    assert [o["seq_numero"] for o in ctx["ocorrencias"]] == [1, 2, 3]
    assert [len(o["fotos"]) for o in ctx["ocorrencias"]] == [0, 0, 1] or sum(len(o["fotos"]) for o in ctx["ocorrencias"]) == 1


async def test_inspecao_sem_visitas(db_session, rfo_vazio):
    ctx = await montar_contexto_rfo(db_session, rfo_vazio.inspecao.id)
    assert ctx["visitas"] == []
    assert ctx["ocorrencias"] == []


async def test_inspecao_inexistente_levanta_404(db_session):
    with pytest.raises(NotFoundError) as exc:
        await montar_contexto_rfo(db_session, uuid.uuid4())
    assert exc.value.status_code == 404


async def test_inspecao_nao_rfo_levanta_409(db_session):
    d = await _criar_inspecao(db_session, tipo="LTIP")
    try:
        with pytest.raises(ConflictError) as exc:
            await montar_contexto_rfo(db_session, d.inspecao.id)
        assert exc.value.status_code == 409
    finally:
        await _limpar(db_session, d)


async def test_resultado_passa_por_normalizar_e_renderizar_html(db_session, rfo_completo):
    ctx = await montar_contexto_rfo(db_session, rfo_completo.inspecao.id)
    normalizado = rfo_pipeline.normalizar_contexto(ctx)
    for visita in normalizado["visitas"]:
        for foto in visita["fotos"]:
            foto["data_uri"] = "data:image/jpeg;base64,AAAA"  # binário vem do fetcher, não daqui
    env = Environment(loader=FileSystemLoader(str(rfo_pipeline.TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    html = env.get_template(rfo_pipeline.HTML_TEMPLATE_NAME).render(**normalizado)
    assert rfo_completo.contrato.numero in html
    assert "Escarificação" in html


@pytest_asyncio.fixture
async def usuario_auditor(db_session):
    obj = Usuario(
        nome="Auditor DEC-47",
        email=f"auditor-dec47-{uuid.uuid4()}@garra-engenharia.com.br",
        senha_hash=hash_password("senha-forte-123"),
        role="auditor",
    )
    db_session.add(obj)
    await db_session.commit()
    usuario_id = obj.id
    yield obj
    await db_session.rollback()
    await db_session.execute(delete(Usuario).where(Usuario.id == usuario_id))
    await db_session.commit()


@pytest_asyncio.fixture
async def rfo_legendas(db_session, usuario_auditor):
    """Uma visita com três fotos: legenda manual; IA em rascunho; IA aprovada (sem manual)."""
    d = await _criar_inspecao(db_session)
    visita = Visita(inspecao_id=d.inspecao.id, data=date(2026, 1, 6), servicos_executados="Teste", seq_numero=1)
    db_session.add(visita)
    await db_session.commit()
    agora = datetime.now(UTC)
    db_session.add_all(
        [
            # 1) legenda manual, sem sugestão de IA
            Foto(visita_id=visita.id, storage_key="k/manual.jpg", origem="upload", ordem=1, legenda="Manual humana"),
            # 2) IA ainda não aprovada (rascunho), sem legenda manual
            Foto(
                visita_id=visita.id, storage_key="k/ia-rascunho.jpg", origem="upload", ordem=2,
                legenda_ia_sugerida="Sugestão IA rascunho", status_validacao_ia="rascunho",
            ),
            # 3) IA aprovada, sem legenda manual: a sugestão ainda não é legenda do relatório
            Foto(
                visita_id=visita.id, storage_key="k/ia-aprovada.jpg", origem="upload", ordem=3,
                legenda_ia_sugerida="Sugestão IA aprovada", status_validacao_ia="aprovada",
                aprovado_por_id=usuario_auditor.id, aprovado_em=agora,
            ),
            # 4) IA em rascunho com legenda manual: a manual é a que sai
            Foto(
                visita_id=visita.id, storage_key="k/ambas.jpg", origem="upload", ordem=4,
                legenda="Manual prevalece", legenda_ia_sugerida="Sugestão ignorada", status_validacao_ia="rascunho",
            ),
        ]
    )
    await db_session.commit()
    yield d
    await _limpar(db_session, d)


async def test_legenda_no_contexto_usa_legenda_para_relatorio(db_session, rfo_legendas):
    ctx = await montar_contexto_rfo(db_session, rfo_legendas.inspecao.id)
    fotos = {f["storage_key"]: f["legenda"] for f in ctx["visitas"][0]["fotos"]}
    assert fotos["k/manual.jpg"] == "Manual humana"
    assert fotos["k/ia-rascunho.jpg"] is None  # IA não aprovada nunca vai ao relatório
    assert fotos["k/ia-aprovada.jpg"] is None  # nem IA aprovada: só `legenda` é impressa
    assert fotos["k/ambas.jpg"] == "Manual prevalece"


async def test_legenda_ia_nao_aparece_no_html_renderizado(db_session, rfo_legendas):
    ctx = await montar_contexto_rfo(db_session, rfo_legendas.inspecao.id)
    normalizado = rfo_pipeline.normalizar_contexto(ctx)
    for foto in normalizado["visitas"][0]["fotos"]:
        foto["data_uri"] = "data:image/jpeg;base64,AAAA"
    env = Environment(loader=FileSystemLoader(str(rfo_pipeline.TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    html = env.get_template(rfo_pipeline.HTML_TEMPLATE_NAME).render(**normalizado)
    assert "Manual humana" in html
    assert "Sugestão IA rascunho" not in html
    assert "Sugestão IA aprovada" not in html
    assert "Sugestão ignorada" not in html
