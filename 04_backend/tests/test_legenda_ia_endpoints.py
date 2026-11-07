"""Testes dos endpoints de legenda por IA (BL-34; DEC-37 DP-3, DP-4, DP-5, DP-6; RN-16, RN-17, RN-18).

- `POST /fotos/{id}/legenda-ia/gerar` escreve só os campos de sugestão e nunca `legenda` (DP-4).
- `PUT /fotos/{id}` aprova com usuário e instante vindos do token, nunca do payload (DP-3), e
  distingue `legenda: null` de campo ausente (DP-5).
- O cliente de IA é injetado (`get_legenda_ia_client`); sem provedor configurado a rota responde
  503 (DP-6, B-04). Aqui ele é sobrescrito pelo `FakeLegendaIAClient`.

Requer PostgreSQL e MinIO de `05_infra/docker-compose.yml`. Cada teste usa um nome de prompt
único (o nome usado pelo serviço é trocado por `monkeypatch`) e remove o que criou.
"""
import hashlib
import io
import uuid
from asyncio import run as run_async
from datetime import UTC, date, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from PIL import Image
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
    Foto,
    Inspecao,
    Ocorrencia,
    PromptIA,
    Responsavel,
    SistemaPredial,
    Usuario,
    Visita,
)
from app.services import foto_service, prompt_ia_service
from app.services.legenda_ia import FakeLegendaIAClient, get_legenda_ia_client
from app.services.storage import get_storage_client

_settings = get_settings()
_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_Session = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def _override_get_db():
    async with _Session() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)

PROMPT_CONTEUDO = "Você é um engenheiro diagnóstico. Descreva a foto em linguagem técnica."


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color="blue").save(buffer, format="PNG")
    return buffer.getvalue()


def _headers(usuario_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario_id))}"}


# --- Fixtures ---------------------------------------------------------------------------------


@pytest_asyncio.fixture
async def usuarios():
    ids: dict[str, uuid.UUID] = {}
    async with _Session() as session:
        for role in ("auditor", "auxiliar", "cliente"):
            usuario = Usuario(
                nome=f"{role} BL-34",
                email=f"bl34-{role}-{uuid.uuid4()}@garra-engenharia.com.br",
                senha_hash=hash_password("senha-forte-123"),
                ativo=True,
                role=role,
            )
            session.add(usuario)
            await session.flush()
            ids[role] = usuario.id
        await session.commit()
    yield ids
    async with _Session() as session:
        await session.execute(delete(Usuario).where(Usuario.id.in_(ids.values())))
        await session.commit()


@pytest_asyncio.fixture
async def nome_prompt(monkeypatch):
    """Nome de prompt exclusivo do teste; apagado depois das fotos que o referenciam (RESTRICT)."""
    nome = f"teste-bl34-{uuid.uuid4().hex[:12]}"
    monkeypatch.setattr(foto_service, "PROMPT_LEGENDA_IA_NOME", nome)
    yield nome
    async with _Session() as session:
        await session.execute(delete(PromptIA).where(PromptIA.nome == nome))
        await session.commit()


@pytest_asyncio.fixture
async def prompt_ativo(nome_prompt):
    async with _Session() as session:
        prompt = await prompt_ia_service.criar_versao(session, nome=nome_prompt, conteudo=PROMPT_CONTEUDO)
        prompt = await prompt_ia_service.ativar(session, prompt.id)
        return prompt


@pytest.fixture
def fake_ia():
    fake = FakeLegendaIAClient()
    app.dependency_overrides[get_legenda_ia_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_legenda_ia_client, None)


@pytest_asyncio.fixture
async def vinculos():
    """Visita e Ocorrência de uma inspeção RFO, para vincular as fotos do teste."""
    async with _Session() as session:
        edificacao = Edificacao(nome=f"Ed. BL-34 {uuid.uuid4()}", endereco="Rua da IA, 34")
        fiscal = Responsavel(nome="Eng. Fiscal BL-34", tipo="fiscal", crea="343434-GO")
        sistema = SistemaPredial(nome=f"Sistema BL-34 {uuid.uuid4()}", ordem=934)
        session.add_all([edificacao, fiscal, sistema])
        await session.flush()
        contrato = Contrato(
            edificacao_id=edificacao.id, fiscal_id=fiscal.id, numero=f"CT-BL34-{uuid.uuid4()}",
            tipo_servico="Fiscalização de obra", status="em_andamento", art_fiscalizacao="ART-034",
        )
        session.add(contrato)
        await session.flush()
        inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="em_andamento")
        session.add(inspecao)
        await session.flush()
        visita = Visita(inspecao_id=inspecao.id, data=date(2026, 7, 1), servicos_executados="Estrutura", seq_numero=1)
        ocorrencia = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=sistema.id, situacao="Não Conforme",
            classificacao="Anomalia", seq_numero=1,
        )
        session.add_all([visita, ocorrencia])
        await session.commit()
        objetos = [ocorrencia, visita, inspecao, contrato, sistema, fiscal, edificacao]
    yield {"visita": visita.id, "ocorrencia": ocorrencia.id}
    async with _Session() as session:
        for obj in objetos:
            await session.delete(await session.get(type(obj), obj.id))
            await session.commit()


@pytest_asyncio.fixture
async def criar_foto(vinculos, nome_prompt, usuarios):
    """Fábrica de fotos com objeto real no MinIO. Depende de `nome_prompt` e `usuarios` para
    que as fotos sejam apagadas antes do prompt e dos usuários que elas referenciam."""
    storage = get_storage_client()
    criadas: list[tuple[uuid.UUID, str]] = []

    async def _criar(vinculo: str = "visita", legenda: str | None = "Legenda manual") -> uuid.UUID:
        key = f"fotos/{uuid.uuid4()}.png"
        storage.upload(key, _png(), content_type="image/png")
        async with _Session() as session:
            foto = Foto(storage_key=key, legenda=legenda, origem="upload_manual", **{f"{vinculo}_id": vinculos[vinculo]})
            session.add(foto)
            await session.commit()
            criadas.append((foto.id, key))
            return foto.id

    yield _criar
    async with _Session() as session:
        await session.execute(delete(Foto).where(Foto.id.in_([fid for fid, _ in criadas])))
        await session.commit()
    for _, key in criadas:
        storage.delete(key)


def _nova_foto(criar_foto, **kwargs) -> uuid.UUID:
    return run_async(criar_foto(**kwargs))


def _gerar(foto_id, usuario_id, json=None):
    return client.post(f"/api/v1/fotos/{foto_id}/legenda-ia/gerar", json=json, headers=_headers(usuario_id))


def _put(foto_id, usuario_id, json):
    return client.put(f"/api/v1/fotos/{foto_id}", json=json, headers=_headers(usuario_id))


# --- Geração (DP-4) ---------------------------------------------------------------------------


def test_gerar_escreve_apenas_campos_de_sugestao(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    antes = datetime.now(UTC)

    response = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "trinca na viga do 2º pavimento"})

    assert response.status_code == 200, response.text
    corpo = response.json()
    assert corpo["legenda"] == "Legenda manual"  # nunca alterada pela geração
    assert corpo["legenda_bruta"] == "trinca na viga do 2º pavimento"
    assert corpo["legenda_ia_sugerida"].startswith("trinca na viga do 2º pavimento [")
    assert corpo["status_validacao_ia"] == "rascunho"
    assert corpo["alertas_ia"] == []
    assert corpo["pendencias_ia"] == []
    assert corpo["prompt_ia_id"] == str(prompt_ativo.id)
    assert corpo["prompt_conteudo_hash"] == hashlib.sha256(PROMPT_CONTEUDO.encode()).hexdigest()
    assert datetime.fromisoformat(corpo["legenda_ia_gerada_em"]) >= antes - timedelta(seconds=5)
    assert corpo["aprovado_por_id"] is None and corpo["aprovado_em"] is None
    assert fake_ia.chamadas == 1


def test_gerar_sem_legenda_bruta_preserva_a_existente(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    primeira = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "umidade no forro"}).json()

    response = _gerar(foto_id, usuarios["auditor"])  # sem corpo: reaproveita a legenda bruta gravada

    assert response.status_code == 200, response.text
    corpo = response.json()
    assert corpo["legenda_bruta"] == "umidade no forro"
    assert corpo["legenda_ia_sugerida"] == primeira["legenda_ia_sugerida"]  # Fake determinístico
    assert corpo["legenda"] == "Legenda manual"


def test_gerar_foto_inexistente_404(usuarios, prompt_ativo, fake_ia):
    response = _gerar(uuid.uuid4(), usuarios["auditor"], {"legenda_bruta": "x"})

    assert response.status_code == 404
    assert response.json()["type"].endswith("/foto-nao-encontrada")
    assert fake_ia.chamadas == 0


def test_gerar_sem_prompt_ativo_retorna_erro_de_dominio(usuarios, nome_prompt, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)

    response = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "x"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["type"].endswith("/prompt-ia-sem-versao-ativa")
    assert fake_ia.chamadas == 0


def test_gerar_sem_cliente_configurado_retorna_503(usuarios, prompt_ativo, criar_foto):
    foto_id = _nova_foto(criar_foto)

    response = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "x"})

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    corpo = response.json()
    assert corpo["status"] == 503
    assert corpo["type"].endswith("/legenda-ia-indisponivel")


# --- Aprovação (DP-3) e PUT com campo ausente vs null (DP-5) ---------------------------------


def test_aprovar_usa_usuario_do_token_e_ignora_campos_do_payload(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    sugestao = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "fissura"}).json()["legenda_ia_sugerida"]
    antes = datetime.now(UTC)

    response = _put(foto_id, usuarios["auditor"], {
        "aprovar_legenda_ia": True,
        "aprovado_por_id": str(uuid.uuid4()),
        "aprovado_em": "2000-01-01T00:00:00Z",
        "status_validacao_ia": "rascunho",
        "legenda_ia_sugerida": "forjada",
    })

    assert response.status_code == 200, response.text
    corpo = response.json()
    assert corpo["status_validacao_ia"] == "aprovada"
    assert corpo["aprovado_por_id"] == str(usuarios["auditor"])
    assert datetime.fromisoformat(corpo["aprovado_em"]) >= antes - timedelta(seconds=5)
    assert corpo["legenda"] == sugestao  # aprovação sem `legenda` aceita a sugestão como está
    assert corpo["legenda_ia_sugerida"] == sugestao  # a minuta da IA é preservada (RN-17)


def test_aprovar_com_legenda_editada(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    sugestao = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "fissura"}).json()["legenda_ia_sugerida"]

    response = _put(foto_id, usuarios["auditor"], {"aprovar_legenda_ia": True, "legenda": "Fissura revisada"})

    assert response.status_code == 200, response.text
    corpo = response.json()
    assert corpo["legenda"] == "Fissura revisada"
    assert corpo["legenda_ia_sugerida"] == sugestao
    assert corpo["status_validacao_ia"] == "aprovada"


def test_aprovar_sem_sugestao_ou_com_legenda_vazia_e_recusado(usuarios, prompt_ativo, fake_ia, criar_foto):
    sem_sugestao = _nova_foto(criar_foto)
    response = _put(sem_sugestao, usuarios["auditor"], {"aprovar_legenda_ia": True})
    assert response.status_code == 422
    assert response.json()["type"].endswith("/legenda-ia-sem-sugestao")

    com_sugestao = _nova_foto(criar_foto)
    _gerar(com_sugestao, usuarios["auditor"], {"legenda_bruta": "fissura"})
    response = _put(com_sugestao, usuarios["auditor"], {"aprovar_legenda_ia": True, "legenda": None})
    assert response.status_code == 422
    assert response.json()["type"].endswith("/legenda-aprovada-vazia")


def test_put_legenda_null_limpa_e_campo_ausente_preserva(usuarios, criar_foto):
    foto_id = _nova_foto(criar_foto)

    preserva = _put(foto_id, usuarios["auditor"], {"ordem": 2})
    assert preserva.status_code == 200, preserva.text
    assert preserva.json()["legenda"] == "Legenda manual"
    assert preserva.json()["ordem"] == 2

    limpa = _put(foto_id, usuarios["auditor"], {"legenda": None})
    assert limpa.status_code == 200
    assert limpa.json()["legenda"] is None
    assert limpa.json()["ordem"] == 2


def test_edicao_manual_sem_sugestao_mantem_campos_de_ia_nulos(usuarios, criar_foto):
    foto_id = _nova_foto(criar_foto)

    response = _put(foto_id, usuarios["auditor"], {"legenda": "Nova legenda manual"})

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["legenda"] == "Nova legenda manual"
    for campo in ("status_validacao_ia", "legenda_ia_sugerida", "aprovado_por_id", "aprovado_em", "prompt_ia_id"):
        assert corpo[campo] is None


# --- Perfis (RN-18/DEC-27) --------------------------------------------------------------------


@pytest.mark.parametrize("vinculo", ["visita", "ocorrencia"])
def test_auxiliar_gera_mas_nao_aprova(vinculo, usuarios, prompt_ativo, fake_ia, criar_foto):
    """DEC-42 A: o auxiliar gera/edita rascunho; só o auditor aprova (RN-16, RN-18)."""
    foto_id = _nova_foto(criar_foto, vinculo=vinculo)

    gerada = _gerar(foto_id, usuarios["auxiliar"], {"legenda_bruta": "desplacamento de reboco"})
    assert gerada.status_code == 200, gerada.text

    recusada = _put(foto_id, usuarios["auxiliar"], {"aprovar_legenda_ia": True})
    assert recusada.status_code == 403, recusada.text
    assert recusada.json()["type"].endswith("/acesso-negado")

    aprovada = _put(foto_id, usuarios["auditor"], {"aprovar_legenda_ia": True})
    assert aprovada.status_code == 200, aprovada.text
    assert aprovada.json()["aprovado_por_id"] == str(usuarios["auditor"])


def test_usuario_sem_permissao_recebe_403(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)

    gerar = _gerar(foto_id, usuarios["cliente"], {"legenda_bruta": "x"})
    aprovar = _put(foto_id, usuarios["cliente"], {"aprovar_legenda_ia": True})

    assert gerar.status_code == 403
    assert aprovar.status_code == 403
    assert fake_ia.chamadas == 0


def test_sem_token_recebe_401_antes_do_503():
    # Sem override do cliente: a autenticação é resolvida antes da dependência de IA.
    response = client.post(f"/api/v1/fotos/{uuid.uuid4()}/legenda-ia/gerar", json={})

    assert response.status_code == 401
