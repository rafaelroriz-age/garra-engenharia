"""`registrar()` grava SQL NULL (não JSON null) em `resposta` quando não há resposta (DEC-59 P1)."""

import hashlib
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import ChamadaIA
from app.services.legenda_ia import telemetria as tel
from app.services.legenda_ia.contrato import LegendaIAResultado

_engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
_Session = async_sessionmaker(bind=_engine, expire_on_commit=False)


def _chave() -> str:
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()


async def _registrar(chave: str, **kw) -> uuid.UUID:
    async with _Session() as s:
        linha = await tel.registrar(
            s,
            chave=chave,
            provedor="deepseek",
            modelo="m",
            latencia_ms=5,
            **{"origem": "api", "sucesso": False, **kw},
        )
        return linha.id


async def _tipo(id_: uuid.UUID) -> tuple[bool, str | None]:
    async with _Session() as s:
        r = (
            await s.execute(
                text("SELECT resposta IS NULL, jsonb_typeof(resposta) FROM chamadas_ia WHERE id = :i"),
                {"i": id_},
            )
        ).one()
        return r[0], r[1]


async def _apagar(*ids):
    async with _Session() as s:
        await s.execute(delete(ChamadaIA).where(ChamadaIA.id.in_(ids)))
        await s.commit()


def _resultado(legenda: str) -> LegendaIAResultado:
    return LegendaIAResultado(legenda_sugerida=legenda, alertas=[], pendencias=[], nivel_certeza="alto")


@pytest.mark.asyncio
async def test_registrar_sem_resposta_grava_sql_null():
    id_ = await _registrar(_chave(), erro_tipo="timeout")
    try:
        assert await _tipo(id_) == (True, None)
    finally:
        await _apagar(id_)


@pytest.mark.asyncio
async def test_registrar_cache_local_grava_sql_null():
    id_ = await _registrar(_chave(), origem="cache_local", sucesso=True, resultado=_resultado("x"))
    try:
        assert (await _tipo(id_))[0] is True
    finally:
        await _apagar(id_)


@pytest.mark.asyncio
async def test_registrar_sucesso_api_grava_json_objeto_e_cache_acerta():
    chave = _chave()
    id_ = await _registrar(chave, sucesso=True, resultado=_resultado("Fissura."))
    try:
        assert await _tipo(id_) == (False, "object")
        async with _Session() as s:
            assert (await tel.buscar_em_cache(s, chave, 720)).legenda_sugerida == "Fissura."
    finally:
        await _apagar(id_)


@pytest.mark.asyncio
async def test_cache_ignora_json_null_legado_e_sql_null():
    chave_json, chave_sql = _chave(), _chave()
    ids = []
    async with _Session() as s:
        for chave, valor in ((chave_json, "'null'::jsonb"), (chave_sql, "NULL")):
            i = uuid.uuid4()
            ids.append(i)
            await s.execute(
                text(
                    "INSERT INTO chamadas_ia (id, finalidade, provedor, chave_cache, origem, sucesso, "
                    "tokens_prompt, tokens_cache_hit, tokens_cache_miss, tokens_saida, latencia_ms, "
                    f"resposta, criado_em) VALUES (:i,'legenda_foto','deepseek',:c,'api',true,0,0,0,0,1,{valor},:t)"
                ),
                {"i": i, "c": chave, "t": datetime.now(UTC)},
            )
        await s.commit()
    try:
        assert (await _tipo(ids[0])) == (False, "null")  # legado confirmado
        async with _Session() as s:
            assert await tel.buscar_em_cache(s, chave_json, 720) is None
            assert await tel.buscar_em_cache(s, chave_sql, 720) is None
    finally:
        await _apagar(*ids)
