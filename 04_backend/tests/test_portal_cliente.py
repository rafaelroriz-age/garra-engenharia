"""Testes do Portal do Cliente — dashboard, acompanhamento e documentos (BL-32/BL-33)."""
import uuid
from datetime import UTC, date, datetime

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    Contrato,
    Edificacao,
    Inspecao,
    Ocorrencia,
    Relatorio,
    Responsavel,
    SistemaPredial,
    Usuario,
    Visita,
)

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def cenario_portal():
    """Contratante com 1 edificação/contrato/inspeção completos + edificação de outro cliente."""
    sufixo = uuid.uuid4().hex[:8]
    async with _TestSessionLocal() as session:
        usuario_cliente = Usuario(
            nome="Cliente Portal",
            email=f"cliente-portal-{sufixo}@garra.com",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role="cliente",
        )
        usuario_outro = Usuario(
            nome="Outro Cliente",
            email=f"outro-portal-{sufixo}@garra.com",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role="cliente",
        )
        session.add_all([usuario_cliente, usuario_outro])
        await session.commit()

        contratante = Responsavel(nome="Contratante Portal", tipo="sindico", usuario_id=usuario_cliente.id)
        outro_contratante = Responsavel(nome="Outro Contratante", tipo="sindico", usuario_id=usuario_outro.id)
        session.add_all([contratante, outro_contratante])
        await session.commit()

        edificacao = Edificacao(nome=f"Ed. Portal {sufixo}", endereco="Rua do Portal")
        outra_edificacao = Edificacao(nome=f"Ed. Outro {sufixo}", endereco="Rua de Outro")
        session.add_all([edificacao, outra_edificacao])
        await session.commit()

        contrato = Contrato(
            edificacao_id=edificacao.id,
            fiscal_id=contratante.id,
            contratante_id=contratante.id,
            numero=f"CT-PORTAL-{sufixo}",
            tipo_servico="ltip",
            status="em_andamento",
            data_inicio=date(2026, 1, 10),
        )
        contrato_outro = Contrato(
            edificacao_id=outra_edificacao.id,
            fiscal_id=outro_contratante.id,
            contratante_id=outro_contratante.id,
            numero=f"CT-OUTRO-{sufixo}",
            tipo_servico="ltip",
            status="em_andamento",
        )
        session.add_all([contrato, contrato_outro])
        await session.commit()

        inspecao = Inspecao(contrato_id=contrato.id, tipo="ltip", status="em_andamento")
        session.add(inspecao)
        await session.commit()

        sistema = SistemaPredial(nome=f"Sistema Portal {sufixo}", ordem=1)
        session.add(sistema)
        await session.commit()

        session.add_all(
            [
                Visita(
                    inspecao_id=inspecao.id,
                    data=date(2026, 1, 15),
                    servicos_executados="Vistoria de cobertura",
                    seq_numero=1,
                ),
                Ocorrencia(
                    inspecao_id=inspecao.id,
                    sistema_id=sistema.id,
                    situacao="NAO_CONFORME",
                    classificacao="anomalia",
                    grau_risco="CRITICO",
                    prioridade=5,
                    descricao="Infiltração na platibanda",
                    seq_numero=1,
                ),
                Relatorio(
                    inspecao_id=inspecao.id,
                    versao="V01",
                    tipo="ltip",
                    status="emitido",
                    pdf_key=f"relatorios/{sufixo}.pdf",
                    emitido_em=datetime(2026, 2, 1, tzinfo=UTC),
                ),
            ]
        )
        await session.commit()

        yield {
            "usuario": usuario_cliente,
            "edificacao_id": edificacao.id,
            "outra_edificacao_id": outra_edificacao.id,
        }

        await session.execute(delete(Relatorio).where(Relatorio.inspecao_id == inspecao.id))
        await session.execute(delete(Ocorrencia).where(Ocorrencia.inspecao_id == inspecao.id))
        await session.execute(delete(Visita).where(Visita.inspecao_id == inspecao.id))
        await session.execute(delete(SistemaPredial).where(SistemaPredial.id == sistema.id))
        await session.execute(delete(Inspecao).where(Inspecao.id == inspecao.id))
        await session.execute(delete(Contrato).where(Contrato.id.in_([contrato.id, contrato_outro.id])))
        await session.execute(
            delete(Edificacao).where(Edificacao.id.in_([edificacao.id, outra_edificacao.id]))
        )
        await session.execute(
            delete(Responsavel).where(Responsavel.id.in_([contratante.id, outro_contratante.id]))
        )
        await session.execute(
            delete(Usuario).where(Usuario.id.in_([usuario_cliente.id, usuario_outro.id]))
        )
        await session.commit()


def test_dashboard_portal_retorna_agregado_da_edificacao_do_contratante(cenario_portal):
    token = create_access_token(subject=str(cenario_portal["usuario"].id))

    response = client.get(
        f"/api/v1/portal/edificacoes/{cenario_portal['edificacao_id']}/dashboard",
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["edificacao_id"] == str(cenario_portal["edificacao_id"])
    assert body["grau_risco_por_sistema"][0]["critico"] == 1


def test_dashboard_portal_de_outro_contratante_retorna_404(cenario_portal):
    token = create_access_token(subject=str(cenario_portal["usuario"].id))

    response = client.get(
        f"/api/v1/portal/edificacoes/{cenario_portal['outra_edificacao_id']}/dashboard",
        headers=_auth_header(token),
    )

    assert response.status_code == 404
    assert response.json()["type"].endswith("/edificacao-nao-encontrada")


def test_acompanhamento_portal_lista_visitas_e_ocorrencias(cenario_portal):
    token = create_access_token(subject=str(cenario_portal["usuario"].id))

    response = client.get(
        f"/api/v1/portal/edificacoes/{cenario_portal['edificacao_id']}/acompanhamento",
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    contratos = response.json()["contratos"]
    assert len(contratos) == 1
    assert contratos[0]["total_visitas"] == 1
    assert contratos[0]["total_ocorrencias"] == 1
    assert contratos[0]["ocorrencias_por_grau_risco"]["critico"] == 1
    assert contratos[0]["inspecao_status"] == "em_andamento"


def test_acompanhamento_portal_de_outro_contratante_retorna_404(cenario_portal):
    token = create_access_token(subject=str(cenario_portal["usuario"].id))

    response = client.get(
        f"/api/v1/portal/edificacoes/{cenario_portal['outra_edificacao_id']}/acompanhamento",
        headers=_auth_header(token),
    )

    assert response.status_code == 404


def test_listar_relatorios_portal_retorna_apenas_do_contratante(cenario_portal):
    token = create_access_token(subject=str(cenario_portal["usuario"].id))

    response = client.get("/api/v1/portal/relatorios", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["versao"] == "V01"
    assert body[0]["tem_pdf"] is True
    assert body[0]["tem_docx"] is False
    assert body[0]["edificacao_id"] == str(cenario_portal["edificacao_id"])


def test_download_docx_inexistente_retorna_404(cenario_portal):
    token = create_access_token(subject=str(cenario_portal["usuario"].id))
    relatorio_id = client.get("/api/v1/portal/relatorios", headers=_auth_header(token)).json()[0]["id"]

    response = client.get(
        f"/api/v1/portal/relatorios/{relatorio_id}/download/docx", headers=_auth_header(token)
    )

    assert response.status_code == 404
    assert response.json()["type"].endswith("/arquivo-nao-disponivel")


def test_download_de_relatorio_de_outro_contratante_retorna_404(cenario_portal):
    token = create_access_token(subject=str(cenario_portal["usuario"].id))

    response = client.get(
        f"/api/v1/portal/relatorios/{uuid.uuid4()}/download/pdf", headers=_auth_header(token)
    )

    assert response.status_code == 404
    assert response.json()["type"].endswith("/relatorio-nao-encontrado")
