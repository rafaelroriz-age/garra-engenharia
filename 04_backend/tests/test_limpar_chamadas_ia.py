"""Testes do expurgo de `resposta` em `chamadas_ia` (DEC-52, BL-34, R-10).

TTL e resolução de flags são puros. Expurgo e cache usam o PostgreSQL de `05_infra` (a tabela
`chamadas_ia` exige a migration b8d4f2a6c1e7). Cada teste remove as linhas que criou.
"""
import argparse
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import ChamadaIA
from app.scripts import limpar_chamadas_ia as script
from app.services.legenda_ia import telemetria as tel

_settings = get_settings()
_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_Session = async_sessionmaker(bind=_engine, expire_on_commit=False)

# Relógio real: o cache (`buscar_em_cache`) compara com agora, então as datas dos testes partem daqui.
AGORA = datetime.now(UTC).replace(microsecond=0)
RESPOSTA = {
    "legenda_sugerida": "Fissura ativa na viga V3.",
    "alertas": [],
    "pendencias": [],
    "nivel_certeza": "alto",
    "modo": "texto",
    "modelo": "deepseek-flash",
}


def _chave() -> str:
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()


def _linha(criado_em: datetime, resposta: dict | None = RESPOSTA) -> ChamadaIA:
    return ChamadaIA(
        finalidade="legenda_foto",
        provedor="deepseek",
        modelo="deepseek-flash",
        modo="texto",
        chave_cache=_chave(),
        origem="api",
        sucesso=True,
        erro_tipo=None,
        tokens_prompt=1000,
        tokens_cache_hit=600,
        tokens_cache_miss=400,
        tokens_saida=200,
        custo_estimado_usd=Decimal("0.000208"),
        latencia_ms=1234,
        resposta=resposta,
        criado_em=criado_em,
    )


@pytest_asyncio.fixture
async def linhas():
    """Cria vencida (com resposta), recente (com resposta) e vencida já sem resposta; remove ao fim."""
    vencida = _linha(AGORA - timedelta(hours=800))
    recente = _linha(AGORA - timedelta(hours=10))
    sem_resposta = _linha(AGORA - timedelta(hours=900), resposta=None)
    async with _Session() as s:
        s.add_all([vencida, recente, sem_resposta])
        await s.commit()
    ids = [vencida.id, recente.id, sem_resposta.id]
    yield {"vencida": vencida.id, "recente": recente.id, "sem_resposta": sem_resposta.id}
    async with _Session() as s:
        await s.execute(delete(ChamadaIA).where(ChamadaIA.id.in_(ids)))
        await s.commit()


async def _estado(ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    async with _Session() as s:
        rows = (await s.execute(select(ChamadaIA).where(ChamadaIA.id.in_(ids)))).scalars().all()
        return {
            r.id: {
                "resposta": r.resposta,
                "tokens_prompt": r.tokens_prompt,
                "tokens_cache_hit": r.tokens_cache_hit,
                "tokens_cache_miss": r.tokens_cache_miss,
                "tokens_saida": r.tokens_saida,
                "custo_estimado_usd": r.custo_estimado_usd,
                "latencia_ms": r.latencia_ms,
                "origem": r.origem,
                "sucesso": r.sucesso,
                "modelo": r.modelo,
                "chave_cache": r.chave_cache,
                "criado_em": r.criado_em,
            }
            for r in rows
        }


# --- Puros: resolução de TTL e flags ----------------------------------------------------------


def test_ttl_flag_tem_prioridade_sobre_config():
    assert script._ttl_efetivo(24, 720) == (24, None)
    assert script._ttl_efetivo(168, 0) == (168, None)


def test_ttl_config_zero_cai_no_padrao_720_com_aviso():
    ttl, aviso = script._ttl_efetivo(None, 0)
    assert ttl == 720
    assert aviso is not None and "720" in aviso


def test_ttl_config_positiva_sem_flag():
    assert script._ttl_efetivo(None, 336) == (336, None)


def test_ttl_horas_zero_ou_negativo_e_recusado():
    with pytest.raises(argparse.ArgumentTypeError):
        script._ttl_positivo("0")
    with pytest.raises(argparse.ArgumentTypeError):
        script._ttl_positivo("-5")
    assert script._ttl_positivo("1") == 1


# --- Expurgo no banco -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dry_run_nao_altera_nada(linhas):
    async with _Session() as s:
        previstas = await script.expurgar(s, 720, aplicar=False, agora=AGORA)
    assert previstas >= 1  # ao menos a vencida desta execução
    estado = await _estado(list(linhas.values()))
    assert estado[linhas["vencida"]]["resposta"] == RESPOSTA
    assert estado[linhas["recente"]]["resposta"] == RESPOSTA


@pytest.mark.asyncio
async def test_aplicar_anula_so_as_vencidas(linhas):
    async with _Session() as s:
        await script.expurgar(s, 720, aplicar=True, agora=AGORA)
    estado = await _estado(list(linhas.values()))
    assert estado[linhas["vencida"]]["resposta"] is None
    assert estado[linhas["recente"]]["resposta"] == RESPOSTA  # recente intacta
    assert estado[linhas["sem_resposta"]]["resposta"] is None
    # SQL NULL de verdade, não JSON null (o filtro de tem_resposta() depende disso)
    async with _Session() as s:
        sql_nulas = (
            await s.execute(
                select(ChamadaIA.id).where(ChamadaIA.id == linhas["vencida"], ChamadaIA.resposta.is_(None))
            )
        ).scalar_one_or_none()
    assert sql_nulas == linhas["vencida"]


@pytest.mark.asyncio
async def test_preserva_demais_colunas_e_nao_apaga_linhas(linhas):
    ids = list(linhas.values())
    antes = await _estado(ids)
    async with _Session() as s:
        await script.expurgar(s, 720, aplicar=True, agora=AGORA)
    depois = await _estado(ids)
    assert depois.keys() == antes.keys()  # nenhuma linha apagada
    for i in ids:
        for coluna in antes[i]:
            if coluna == "resposta":
                continue
            assert depois[i][coluna] == antes[i][coluna], coluna


@pytest.mark.asyncio
async def test_idempotente_segunda_execucao_nao_encontra_nada(linhas):
    async with _Session() as s:
        await script.expurgar(s, 720, aplicar=True, agora=AGORA)
    async with _Session() as s:
        segunda = await script.expurgar(s, 720, aplicar=True, agora=AGORA)
    assert segunda == 0


@pytest.mark.asyncio
async def test_cache_nao_devolve_resposta_expurgada(linhas):
    """Linha expurgada (ou sem resposta) é miss no cache local, mesmo dentro do TTL."""
    chave_vencida = (await _estado([linhas["vencida"]]))[linhas["vencida"]]["chave_cache"]
    async with _Session() as s:
        await script.expurgar(s, 720, aplicar=True, agora=AGORA)
    async with _Session() as s:
        # o cache usa agora real; a vencida (criada há 800 h) já está fora do TTL de 720 h
        assert await tel.buscar_em_cache(s, chave_vencida, 720) is None
        # a recente manteve resposta e continua acerto
        chave_recente = (await _estado([linhas["recente"]]))[linhas["recente"]]["chave_cache"]
        assert await tel.buscar_em_cache(s, chave_recente, 720) is not None
    # linha com resposta nula dentro do TTL também não é acerto
    async with _Session() as s:
        nula = _linha(datetime.now(UTC) - timedelta(hours=1), resposta=None)
        s.add(nula)
        await s.commit()
        chave_nula = nula.chave_cache
        nula_id = nula.id
    try:
        async with _Session() as s:
            assert await tel.buscar_em_cache(s, chave_nula, 720) is None
    finally:
        async with _Session() as s:
            await s.execute(delete(ChamadaIA).where(ChamadaIA.id == nula_id))
            await s.commit()
