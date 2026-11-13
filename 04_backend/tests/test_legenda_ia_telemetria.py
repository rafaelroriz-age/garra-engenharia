"""Testes da telemetria de custo e do cache local da legenda IA (BL-34, R-10).

Custo e chave são puros. Cache, TTL, erro e endpoint usam o PostgreSQL de `05_infra` (a tabela
`chamadas_ia` exige a migration b8d4f2a6c1e7). Não usam MinIO: o modo é texto, então o storage
não é tocado. Cada teste remove o que criou.
"""
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.security import create_access_token
from app.main import app
from app.models import (
    ChamadaIA,
    Contrato,
    Edificacao,
    Foto,
    Inspecao,
    PromptIA,
    Responsavel,
    Usuario,
    Visita,
)
from app.services import foto_service, prompt_ia_service
from app.services.legenda_ia import ContextoLegenda, FakeLegendaIAClient
from app.services.legenda_ia import telemetria as tel
from app.services.legenda_ia.contrato import LegendaIAResultado

_settings = get_settings()
_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_Session = async_sessionmaker(bind=_engine, expire_on_commit=False)

# Só o token importa aqui; hash fixo evita o bug passlib x bcrypt do ambiente (ver T65).
_SENHA_HASH_FIXO = "$2b$12$" + "a" * 53

PRECOS = tel.Precos(entrada_cache_hit=0.02, entrada_cache_miss=0.28, saida=0.42)
USO = {
    "prompt_tokens": 1000,
    "prompt_cache_hit_tokens": 600,
    "prompt_cache_miss_tokens": 400,
    "completion_tokens": 200,
}


# --- Custo e chave (puros) --------------------------------------------------------------------


def test_custo_por_milhao_de_tokens():
    # (600*0.02 + 400*0.28 + 200*0.42) / 1e6 = (12 + 112 + 84) / 1e6
    assert tel.custo(USO, PRECOS) == Decimal("0.000208")


def test_custo_deriva_miss_de_prompt_tokens_quando_ausente():
    uso = {"prompt_tokens": 1000, "prompt_cache_hit_tokens": 600, "completion_tokens": 200}
    assert tel.custo(uso, PRECOS) == tel.custo(USO, PRECOS)


@pytest.mark.parametrize(
    "uso,precos",
    [
        (None, PRECOS),
        ({}, PRECOS),
        (USO, tel.Precos()),
        (USO, tel.Precos(entrada_cache_hit=0.02, entrada_cache_miss=0.28)),
    ],
)
def test_custo_nulo_sem_uso_ou_sem_precos(uso, precos):
    assert tel.custo(uso, precos) is None


def test_precos_vazios_na_config_viram_none():
    s = Settings(_env_file=None, deepseek_preco_saida_usd="", deepseek_preco_entrada_cache_hit_usd="0.5")
    assert s.deepseek_preco_saida_usd is None
    assert s.deepseek_preco_entrada_cache_hit_usd == 0.5
    assert tel.Precos.de_settings(s).entrada_cache_miss is None


def test_chave_cache_estavel_e_sensivel_a_cada_entrada():
    ctx = ContextoLegenda(legenda_bruta="fissura na viga", sistema="Estrutura")
    base = tel.chave_cache("h1", "deepseek-flash", ctx)
    assert base == tel.chave_cache("h1", "deepseek-flash", ContextoLegenda(legenda_bruta="fissura na viga", sistema="Estrutura"))
    assert len(base) == 64
    assert base != tel.chave_cache("h2", "deepseek-flash", ctx)
    assert base != tel.chave_cache("h1", "outro-modelo", ctx)
    assert base != tel.chave_cache("h1", "deepseek-flash", ContextoLegenda(legenda_bruta="fissura na laje", sistema="Estrutura"))
    assert base != tel.chave_cache("h1", "deepseek-flash", ctx, extra="imagem:x")


# --- Fixtures de banco ------------------------------------------------------------------------


class ClienteContador(FakeLegendaIAClient):
    """Fake que conta chamadas e devolve `uso`/`modelo` como o provedor real."""

    async def gerar_legenda(self, contexto, prompt, imagem=None):
        base = await super().gerar_legenda(contexto, prompt, imagem)
        return LegendaIAResultado(
            legenda_sugerida=base.legenda_sugerida, alertas=base.alertas, pendencias=base.pendencias,
            modo="texto", uso=dict(USO), modelo="deepseek-flash",
        )


class ClienteQuebrado:
    enviar_imagem = False

    async def gerar_legenda(self, contexto, prompt, imagem=None):
        raise DomainError("segredo-sk-123 no corpo", type_suffix="provedor-ia-indisponivel", status_code=502)


@pytest_asyncio.fixture
async def cenario(monkeypatch):
    nome = f"teste-bl34-tel-{uuid.uuid4().hex[:12]}"
    monkeypatch.setattr(foto_service, "PROMPT_LEGENDA_IA_NOME", nome)
    async with _Session() as s:
        usuario = Usuario(
            nome="Auditor tel", email=f"tel-{uuid.uuid4()}@garra-engenharia.com.br",
            senha_hash=_SENHA_HASH_FIXO, ativo=True, role="auditor",
        )
        edificacao = Edificacao(nome=f"Ed. tel {uuid.uuid4()}", endereco="Rua T, 1")
        fiscal = Responsavel(nome="Fiscal tel", tipo="fiscal", crea="111111-GO")
        s.add_all([usuario, edificacao, fiscal])
        await s.flush()
        contrato = Contrato(
            edificacao_id=edificacao.id, fiscal_id=fiscal.id, numero=f"CT-TEL-{uuid.uuid4()}",
            tipo_servico="Fiscalização de obra", status="em_andamento", art_fiscalizacao="ART-1",
        )
        s.add(contrato)
        await s.flush()
        inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="em_andamento")
        s.add(inspecao)
        await s.flush()
        visita = Visita(inspecao_id=inspecao.id, data=date(2026, 7, 1), servicos_executados="Estrutura", seq_numero=1)
        s.add(visita)
        await s.flush()
        prompt = await prompt_ia_service.criar_versao(s, nome=nome, conteudo="Prompt de teste da telemetria.")
        await prompt_ia_service.ativar(s, prompt.id)
        fotos = []
        for i in range(2):
            foto = Foto(storage_key=f"fotos/{uuid.uuid4()}.png", legenda=f"L{i}", origem="upload_manual",
                        visita_id=visita.id, legenda_bruta=f"mesma legenda bruta {nome}")
            s.add(foto)
            fotos.append(foto)
        await s.commit()
        ids = {"usuario": usuario.id, "fotos": [f.id for f in fotos]}
        objetos = [visita, inspecao, contrato, fiscal, edificacao]
    yield ids
    async with _Session() as s:
        await s.execute(delete(ChamadaIA).where(ChamadaIA.usuario_id == ids["usuario"]))
        await s.execute(delete(Foto).where(Foto.id.in_(ids["fotos"])))
        await s.execute(delete(PromptIA).where(PromptIA.nome == nome))
        await s.commit()
        for obj in objetos:
            await s.delete(await s.get(type(obj), obj.id))
            await s.commit()
        await s.execute(delete(Usuario).where(Usuario.id == ids["usuario"]))
        await s.commit()


async def _gerar(cenario, cliente, indice=0):
    async with _Session() as s:
        return await foto_service.gerar_legenda_ia(
            s, cenario["fotos"][indice], None, cliente, {}, usuario_id=cenario["usuario"]
        )


async def _chamadas(cenario):
    async with _Session() as s:
        return (
            await s.execute(
                select(ChamadaIA).where(ChamadaIA.usuario_id == cenario["usuario"]).order_by(ChamadaIA.criado_em)
            )
        ).scalars().all()


# --- Cache e registro -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_segunda_geracao_identica_vem_do_cache_sem_chamar_o_cliente(cenario):
    cliente = ClienteContador()
    primeira = await _gerar(cenario, cliente)
    segunda = await _gerar(cenario, cliente)

    assert cliente.chamadas == 1
    assert segunda.legenda_ia_sugerida == primeira.legenda_ia_sugerida
    assert segunda.status_validacao_ia == "rascunho"  # DEC-42: regerar continua voltando a rascunho
    api, cache = await _chamadas(cenario)
    assert (api.origem, cache.origem) == ("api", "cache_local")
    assert api.sucesso and cache.sucesso
    assert (api.tokens_prompt, api.tokens_cache_hit, api.tokens_cache_miss, api.tokens_saida) == (1000, 600, 400, 200)
    assert api.modelo == "deepseek-flash" and api.latencia_ms >= 0
    assert cache.tokens_prompt == 0 and cache.custo_estimado_usd is None
    assert api.chave_cache == cache.chave_cache
    assert api.custo_estimado_usd is None  # preços vazios na config padrão
    assert api.resposta["legenda_sugerida"] == primeira.legenda_ia_sugerida


@pytest.mark.asyncio
async def test_custo_registrado_com_precos_configurados(cenario, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_PRECO_ENTRADA_CACHE_HIT_USD", "0.02")
    monkeypatch.setenv("DEEPSEEK_PRECO_ENTRADA_CACHE_MISS_USD", "0.28")
    monkeypatch.setenv("DEEPSEEK_PRECO_SAIDA_USD", "0.42")
    get_settings.cache_clear()
    try:
        await _gerar(cenario, ClienteContador())
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
    (api,) = await _chamadas(cenario)
    assert api.custo_estimado_usd == Decimal("0.000208")


@pytest.mark.asyncio
async def test_ttl_expirado_chama_de_novo(cenario):
    cliente = ClienteContador()
    await _gerar(cenario, cliente)
    async with _Session() as s:  # envelhece o registro além do TTL padrão (720 h)
        await s.execute(
            update(ChamadaIA).where(ChamadaIA.usuario_id == cenario["usuario"])
            .values(criado_em=datetime.now(UTC) - timedelta(hours=721))
        )
        await s.commit()
    await _gerar(cenario, cliente)
    assert cliente.chamadas == 2
    assert [c.origem for c in await _chamadas(cenario)] == ["api", "api"]


@pytest.mark.asyncio
async def test_contexto_diferente_nao_usa_o_cache(cenario):
    cliente = ClienteContador()
    await _gerar(cenario, cliente, 0)
    async with _Session() as s:
        await s.execute(update(Foto).where(Foto.id == cenario["fotos"][1]).values(legenda_bruta="outra legenda"))
        await s.commit()
    await _gerar(cenario, cliente, 1)
    assert cliente.chamadas == 2


@pytest.mark.asyncio
async def test_erro_do_provedor_e_registrado_sem_conteudo_e_relancado(cenario):
    with pytest.raises(DomainError):
        await _gerar(cenario, ClienteQuebrado())
    (linha,) = await _chamadas(cenario)
    assert linha.origem == "api" and linha.sucesso is False
    assert linha.erro_tipo == "provedor-ia-indisponivel"
    assert linha.resposta is None and linha.tokens_prompt == 0
    assert "segredo" not in repr(linha.__dict__)
    # Erro não vira cache: a próxima geração chama o cliente de novo.
    cliente = ClienteContador()
    await _gerar(cenario, cliente)
    assert cliente.chamadas == 1


# --- Endpoint ---------------------------------------------------------------------------------


async def _override_get_db():
    async with _Session() as session:
        yield session


def _headers(usuario_id):
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario_id))}"}


@pytest.mark.asyncio
async def test_endpoint_uso_agrega_por_dia_e_modelo_e_exige_auditor(cenario):
    await _gerar(cenario, ClienteContador())
    await _gerar(cenario, ClienteContador())  # cache_local
    async with _Session() as s:
        auxiliar = Usuario(
            nome="Aux tel", email=f"aux-tel-{uuid.uuid4()}@garra-engenharia.com.br",
            senha_hash=_SENHA_HASH_FIXO, ativo=True, role="auxiliar",
        )
        s.add(auxiliar)
        await s.commit()
    app.dependency_overrides[get_db] = _override_get_db
    try:
        client = TestClient(app)
        hoje = datetime.now(UTC).date().isoformat()
        negado = client.get("/api/v1/ia/uso", headers=_headers(auxiliar.id))
        ok = client.get(f"/api/v1/ia/uso?de={hoje}&ate={hoje}", headers=_headers(cenario["usuario"]))
        invalido = client.get("/api/v1/ia/uso?de=2026-02-01&ate=2026-01-01", headers=_headers(cenario["usuario"]))
        anonimo = client.get("/api/v1/ia/uso")
    finally:
        app.dependency_overrides.pop(get_db, None)
        async with _Session() as s:
            await s.execute(delete(Usuario).where(Usuario.id == auxiliar.id))
            await s.commit()
    assert negado.status_code == 403
    assert anonimo.status_code == 401
    assert invalido.status_code == 422
    assert ok.status_code == 200
    linha = next(d for d in ok.json()["dias"] if d["modelo"] == "deepseek-flash")
    assert linha["dia"] == hoje
    assert linha["chamadas"] >= 2 and linha["chamadas_cache_local"] >= 1 and linha["chamadas_api"] >= 1
    assert linha["tokens_cache_hit"] >= 600
    assert linha["pct_tokens_cache_hit"] == 60.0
