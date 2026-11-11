"""Testes do serviço de prompts de IA e do contrato `LegendaIAClient` (BL-37, DEC-37 DP-2/DP-6).

Requer o PostgreSQL de `05_infra/docker-compose.yml` (localhost:5433). Cada teste usa um
`nome` único e remove suas linhas ao final, sem tocar em dados de outros testes.
"""
import hashlib
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.errors import DomainError
from app.models import PromptIA
from app.services import prompt_ia_service
from app.services.legenda_ia import (
    ContextoLegenda,
    FakeLegendaIAClient,
    LegendaIAClient,
    LegendaIAResultado,
)


@pytest.fixture
def nome() -> str:
    return f"teste-bl37-{uuid.uuid4().hex[:12]}"


@pytest_asyncio.fixture(autouse=True)
async def _limpeza(db_session, nome):
    yield
    await db_session.rollback()
    await db_session.execute(delete(PromptIA).where(PromptIA.nome == nome))
    await db_session.commit()


async def test_versoes_incrementais_por_nome(db_session, nome):
    v1 = await prompt_ia_service.criar_versao(db_session, nome=nome, conteudo="a")
    v2 = await prompt_ia_service.criar_versao(db_session, nome=nome, conteudo="b")
    outro = await prompt_ia_service.criar_versao(db_session, nome=nome + "-x", conteudo="c")
    try:
        assert (v1.versao, v2.versao, outro.versao) == ("1", "2", "1")
        assert v1.ativo is False
    finally:
        await db_session.execute(delete(PromptIA).where(PromptIA.nome == nome + "-x"))
        await db_session.commit()


async def test_hash_estavel_sha256():
    esperado = hashlib.sha256("conteúdo".encode()).hexdigest()
    assert prompt_ia_service.calcular_hash("conteúdo") == esperado
    assert prompt_ia_service.calcular_hash("conteúdo") == esperado
    assert prompt_ia_service.calcular_hash("outro") != esperado


async def test_ativacao_exclusiva(db_session, nome):
    v1 = await prompt_ia_service.criar_versao(db_session, nome=nome, conteudo="a")
    v2 = await prompt_ia_service.criar_versao(db_session, nome=nome, conteudo="b")
    await prompt_ia_service.ativar(db_session, v1.id)
    assert (await prompt_ia_service.obter_ativo(db_session, nome)).id == v1.id
    await prompt_ia_service.ativar(db_session, v2.id)
    ativos = (await db_session.execute(
        select(PromptIA).where(PromptIA.nome == nome, PromptIA.ativo)
    )).scalars().all()
    assert [p.id for p in ativos] == [v2.id]
    assert (await prompt_ia_service.obter_ativo(db_session, nome)).versao == "2"


async def test_ativar_inexistente(db_session):
    with pytest.raises(DomainError) as exc:
        await prompt_ia_service.ativar(db_session, uuid.uuid4())
    assert exc.value.status_code == 404


async def test_imutabilidade_do_conteudo(db_session, nome):
    v1 = await prompt_ia_service.criar_versao(db_session, nome=nome, conteudo="original")
    with pytest.raises(DomainError) as exc:
        await prompt_ia_service.alterar_conteudo(db_session, v1.id, "novo")
    assert exc.value.type_suffix == "prompt-ia-imutavel"
    await db_session.refresh(v1)
    assert v1.conteudo == "original"


async def test_sem_prompt_ativo_gera_erro_de_dominio(db_session, nome):
    await prompt_ia_service.criar_versao(db_session, nome=nome, conteudo="a")
    with pytest.raises(DomainError) as exc:
        await prompt_ia_service.obter_ativo(db_session, nome)
    assert exc.value.type_suffix == "prompt-ia-sem-versao-ativa"


async def test_criar_valida_entrada(db_session, nome):
    with pytest.raises(DomainError):
        await prompt_ia_service.criar_versao(db_session, nome=nome, conteudo="   ")
    with pytest.raises(DomainError):
        await prompt_ia_service.criar_versao(db_session, nome=" ", conteudo="a")


async def test_fake_deterministico():
    client = FakeLegendaIAClient()
    assert isinstance(client, LegendaIAClient)
    trinca = ContextoLegenda(legenda_bruta="trinca na parede")
    r1 = await client.gerar_legenda(trinca, "prompt", b"img")
    r2 = await client.gerar_legenda(trinca, "prompt", b"img")
    r3 = await client.gerar_legenda(ContextoLegenda(), "prompt", b"outra")
    assert r1 == r2 and isinstance(r1, LegendaIAResultado)
    assert r1.legenda_sugerida and r1 != r3
    assert r3.pendencias  # sem legenda bruta, o Fake sinaliza pendência
    assert client.chamadas == 3
