"""Testes do modelo de dados de legendas assistidas por IA (BL-36; RF-15, RN-16, RN-17; DEC-37).

Duas partes:
- schemas Pydantic (`FotoRead`/`LegendaIARead`, `PromptIA*`): defaults, domínios e round-trip,
  sem banco;
- constraints no PostgreSQL real de `05_infra/docker-compose.yml` (migration `f7c2a9d4e6b1`):
  unicidade parcial de `ativo` por `nome`, CHECKs de estado e FK do prompt. Cada teste
  apaga o que criou.

Não há chamada a LLM nem endpoint de geração aqui (L12, L13 e L22 ficam para BL-34).
"""
import hashlib
import uuid
from datetime import UTC, datetime
from typing import get_args

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import Foto, PromptIA, Usuario
from app.models.foto import NIVEIS_CERTEZA_IA, STATUS_VALIDACAO_IA
from app.schemas.foto import FotoRead, LegendaIARead, NivelCertezaIA, StatusValidacaoIA
from app.schemas.prompt_ia import PromptIACreate, PromptIARead

CAMPOS_IA = tuple(LegendaIARead.model_fields)
HASH = hashlib.sha256(b"prompt de teste").hexdigest()


# ---------------------------------------------------------------- schemas (sem banco)


def test_dominios_do_schema_espelham_os_checks_do_modelo():
    assert get_args(StatusValidacaoIA) == STATUS_VALIDACAO_IA == ("rascunho", "aprovada")
    assert get_args(NivelCertezaIA) == NIVEIS_CERTEZA_IA


def test_foto_read_sem_sugestao_tem_campos_ia_nulos():
    foto = FotoRead(id=uuid.uuid4(), created_at=datetime.now(UTC), storage_key="k", origem="upload_manual")
    assert all(getattr(foto, campo) is None for campo in CAMPOS_IA)
    assert set(CAMPOS_IA) <= set(FotoRead.model_fields)


def test_foto_read_round_trip_json_com_legenda_aprovada():
    agora = datetime.now(UTC)
    original = FotoRead(
        id=uuid.uuid4(),
        created_at=agora,
        storage_key="fotos/a.jpg",
        origem="upload_manual",
        legenda="Fissura vertical na alvenaria do 2º pavimento.",
        legenda_bruta="trinca parede 2o andar",
        legenda_ia_sugerida="Fissura vertical em alvenaria (indício técnico).",
        nivel_certeza_ia="indicio_tecnico",
        status_validacao_ia="aprovada",
        alertas_ia=["sem escala na foto"],
        pendencias_ia=[],
        prompt_ia_id=uuid.uuid4(),
        prompt_conteudo_hash=HASH,
        legenda_ia_gerada_em=agora,
        aprovado_por_id=uuid.uuid4(),
        aprovado_em=agora,
    )
    copia = FotoRead.model_validate_json(original.model_dump_json())
    assert copia == original
    # A minuta da IA e a legenda final ficam em campos distintos (RF-15, RN-17).
    assert copia.legenda != copia.legenda_ia_sugerida


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("status_validacao_ia", "pendente"),
        ("status_validacao_ia", "APROVADA"),
        ("nivel_certeza_ia", "certeza_absoluta"),
        ("prompt_conteudo_hash", "abc"),
        ("prompt_conteudo_hash", HASH.upper()),
    ],
)
def test_legenda_ia_read_rejeita_valor_fora_do_dominio(campo, valor):
    with pytest.raises(ValidationError):
        LegendaIARead(**{campo: valor})


def test_prompt_ia_create_defaults_e_limites():
    prompt = PromptIACreate(nome="legenda_foto", versao="1.0", conteudo="Você é um engenheiro...")
    assert prompt.ativo is False
    for campos in ({"nome": ""}, {"versao": ""}, {"conteudo": ""}, {"nome": "x" * 101}, {"versao": "x" * 51}):
        dados = {"nome": "n", "versao": "v", "conteudo": "c"} | campos
        with pytest.raises(ValidationError):
            PromptIACreate(**dados)


def test_prompt_ia_read_round_trip_a_partir_do_orm():
    obj = PromptIA(
        id=uuid.uuid4(), nome="legenda_foto", versao="2.0", conteudo="texto", ativo=True,
        created_at=datetime.now(UTC), criado_por_id=None,
    )
    lido = PromptIARead.model_validate(obj)
    assert PromptIARead.model_validate_json(lido.model_dump_json()) == lido
    assert lido.ativo is True and lido.versao == "2.0"


# ---------------------------------------------------------------- banco (PostgreSQL)


@pytest_asyncio.fixture
async def usuario(db_session: AsyncSession):
    obj = Usuario(
        nome="Aprovador BL-36",
        email=f"aprovador-{uuid.uuid4()}@garra-engenharia.com.br",
        senha_hash=hash_password("senha-forte-123"),
        role="auditor",
    )
    db_session.add(obj)
    await db_session.commit()
    usuario_id = obj.id  # após rollback o objeto expira; guardar o id antes
    yield obj
    await db_session.rollback()
    await db_session.execute(delete(Foto).where(Foto.aprovado_por_id == usuario_id))
    await db_session.execute(delete(Usuario).where(Usuario.id == usuario_id))
    await db_session.commit()


@pytest_asyncio.fixture
async def nome_prompt(db_session: AsyncSession):
    """Nome único por teste; apaga fotos e prompts criados com ele."""
    nome = f"teste_bl36_{uuid.uuid4().hex[:12]}"
    yield nome
    await db_session.rollback()
    ids = (await db_session.execute(select(PromptIA.id).where(PromptIA.nome == nome))).scalars().all()
    if ids:
        await db_session.execute(delete(Foto).where(Foto.prompt_ia_id.in_(ids)))
        await db_session.execute(delete(PromptIA).where(PromptIA.id.in_(ids)))
    await db_session.commit()


async def _criar(db: AsyncSession, *objs):
    db.add_all(objs)
    await db.commit()
    for obj in objs:
        await db.refresh(obj)
    return objs


async def _falha(db: AsyncSession, obj, constraint: str):
    db.add(obj)
    with pytest.raises(IntegrityError) as exc:
        await db.commit()
    await db.rollback()
    assert constraint in str(exc.value)


def _foto(**campos) -> Foto:
    return Foto(storage_key=f"fotos/bl36-{uuid.uuid4()}.jpg", origem="upload_manual", **campos)


async def test_prompt_ia_defaults_do_servidor(db_session: AsyncSession, nome_prompt: str):
    (prompt,) = await _criar(db_session, PromptIA(nome=nome_prompt, versao="1", conteudo="c"))
    assert prompt.ativo is False
    assert prompt.created_at is not None
    assert prompt.criado_por_id is None


async def test_prompt_ia_unico_por_nome_e_versao(db_session: AsyncSession, nome_prompt: str):
    await _criar(db_session, PromptIA(nome=nome_prompt, versao="1", conteudo="c"))
    await _falha(db_session, PromptIA(nome=nome_prompt, versao="1", conteudo="outro"), "uq_prompts_ia_nome_versao")


async def test_no_maximo_uma_versao_ativa_por_nome(db_session: AsyncSession, nome_prompt: str):
    # Várias versões inativas do mesmo nome e uma ativa: permitido.
    await _criar(
        db_session,
        PromptIA(nome=nome_prompt, versao="1", conteudo="c1"),
        PromptIA(nome=nome_prompt, versao="2", conteudo="c2"),
        PromptIA(nome=nome_prompt, versao="3", conteudo="c3", ativo=True),
    )
    # Segunda ativa do mesmo nome: bloqueada pelo índice único parcial.
    await _falha(db_session, PromptIA(nome=nome_prompt, versao="4", conteudo="c4", ativo=True), "uq_prompts_ia_nome_ativo")


async def test_versoes_ativas_de_nomes_diferentes_convivem(db_session: AsyncSession, nome_prompt: str):
    outro = f"{nome_prompt}_b"
    try:
        await _criar(
            db_session,
            PromptIA(nome=nome_prompt, versao="1", conteudo="c", ativo=True),
            PromptIA(nome=outro, versao="1", conteudo="c", ativo=True),
        )
    finally:
        await db_session.execute(delete(PromptIA).where(PromptIA.nome == outro))
        await db_session.commit()


async def test_foto_nova_sem_sugestao_tem_campos_ia_nulos(db_session: AsyncSession):
    (foto,) = await _criar(db_session, _foto(legenda="legenda manual"))
    try:
        assert all(getattr(foto, campo) is None for campo in CAMPOS_IA)
        lida = FotoRead.model_validate(foto)
        assert lida.status_validacao_ia is None and lida.legenda == "legenda manual"
    finally:
        await db_session.delete(foto)
        await db_session.commit()


@pytest.mark.parametrize(
    ("campos", "constraint"),
    [
        ({"legenda_ia_sugerida": "s", "status_validacao_ia": "pendente"}, "ck_fotos_status_validacao_ia"),
        ({"nivel_certeza_ia": "certeza_absoluta"}, "ck_fotos_nivel_certeza_ia"),
        ({"status_validacao_ia": "rascunho"}, "ck_fotos_status_ia_exige_sugestao"),
        ({"legenda_ia_sugerida": "s", "status_validacao_ia": "aprovada"}, "ck_fotos_aprovada_exige_aprovador"),
        ({"prompt_conteudo_hash": "nao-e-sha256"}, "ck_fotos_prompt_conteudo_hash"),
    ],
)
async def test_foto_checks_de_legenda_ia(db_session: AsyncSession, campos: dict, constraint: str):
    await _falha(db_session, _foto(**campos), constraint)


async def test_foto_aprovada_sem_data_de_aprovacao_falha(db_session: AsyncSession, usuario: Usuario):
    foto = _foto(legenda_ia_sugerida="s", status_validacao_ia="aprovada", aprovado_por_id=usuario.id)
    await _falha(db_session, foto, "ck_fotos_aprovada_exige_aprovador")


async def test_foto_prompt_ia_inexistente_viola_fk(db_session: AsyncSession):
    await _falha(db_session, _foto(prompt_ia_id=uuid.uuid4()), "fk_fotos_prompt_ia_id_prompts_ia")


async def test_ciclo_rascunho_aprovada_e_round_trip(db_session: AsyncSession, usuario: Usuario, nome_prompt: str):
    (prompt,) = await _criar(db_session, PromptIA(nome=nome_prompt, versao="1", conteudo="c", ativo=True))
    gerada_em = datetime.now(UTC)
    (foto,) = await _criar(
        db_session,
        _foto(
            legenda_bruta="trinca parede",
            legenda_ia_sugerida="Fissura em alvenaria.",
            nivel_certeza_ia="constatacao_direta",
            status_validacao_ia="rascunho",
            alertas_ia=["foto sem escala"],
            pendencias_ia=["confirmar pavimento"],
            prompt_ia_id=prompt.id,
            prompt_conteudo_hash=HASH,
            legenda_ia_gerada_em=gerada_em,
        ),
    )
    # Rascunho não toca na legenda final (RF-15 / DP-4).
    assert foto.legenda is None
    assert foto.alertas_ia == ["foto sem escala"] and foto.pendencias_ia == ["confirmar pavimento"]

    foto.legenda = "Fissura em alvenaria do 2º pavimento."
    foto.status_validacao_ia = "aprovada"
    foto.aprovado_por_id = usuario.id
    foto.aprovado_em = datetime.now(UTC)
    await db_session.commit()
    await db_session.refresh(foto)

    lida = FotoRead.model_validate(foto)
    assert lida.status_validacao_ia == "aprovada"
    assert lida.legenda_ia_sugerida == "Fissura em alvenaria."  # sugestão preservada (RN-17)
    assert lida.prompt_ia_id == prompt.id and lida.aprovado_por_id == usuario.id
    assert FotoRead.model_validate_json(lida.model_dump_json()) == lida


async def test_prompt_usado_por_foto_nao_pode_ser_apagado(db_session: AsyncSession, nome_prompt: str):
    (prompt,) = await _criar(db_session, PromptIA(nome=nome_prompt, versao="1", conteudo="c"))
    await _criar(db_session, _foto(prompt_ia_id=prompt.id))
    await db_session.delete(prompt)
    with pytest.raises(IntegrityError) as exc:
        await db_session.commit()
    await db_session.rollback()
    assert "fk_fotos_prompt_ia_id_prompts_ia" in str(exc.value)
