"""Testes do seed de demonstração (V1-08): idempotência, conteúdo semeado e limpeza.

Usa o PostgreSQL de 05_infra e um storage em memória (sem MinIO). O prefixo `DEMOTESTE` isola
o teste dos registros `DEMO` reais: nada com o prefixo padrão é lido nem apagado aqui.
"""
import io

import pytest
from PIL import Image
from sqlalchemy import func, select

from app.models import (
    Contrato,
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    RelatorioConteudo,
    Responsavel,
    Usuario,
    Visita,
    VisitaMaoObra,
    VisitaMedicao,
)
from app.scripts import seed_demo
from app.scripts.seed_demo import Prefixos
from tests.conftest import TestSessionLocal

PREF = Prefixos(base="DEMOTESTE")


class StorageFake:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def upload(self, key, data, content_type="application/octet-stream"):
        self.objetos[key] = data
        return key

    def delete(self, key):
        self.objetos.pop(key, None)


async def _contagens(db) -> dict[str, int]:
    edif_ids = select(Edificacao.id).where(Edificacao.nome.like(PREF.like))
    contratos = select(Contrato.id).where(Contrato.edificacao_id.in_(edif_ids))
    inspecoes = select(Inspecao.id).where(Inspecao.contrato_id.in_(contratos))
    visitas = select(Visita.id).where(Visita.inspecao_id.in_(inspecoes))
    ocorrencias = select(Ocorrencia.id).where(Ocorrencia.inspecao_id.in_(inspecoes))

    async def n(consulta) -> int:
        return await db.scalar(select(func.count()).select_from(consulta.subquery()))

    return {
        "edificacoes": await n(edif_ids),
        "contratos": await n(contratos),
        "inspecoes": await n(inspecoes),
        "visitas": await n(visitas),
        "ocorrencias": await n(ocorrencias),
        "mao_obra": await n(select(VisitaMaoObra.id).where(VisitaMaoObra.visita_id.in_(visitas))),
        "medicoes": await n(select(VisitaMedicao.id).where(VisitaMedicao.visita_id.in_(visitas))),
        "fotos": await n(
            select(Foto.id).where(Foto.visita_id.in_(visitas) | Foto.ocorrencia_id.in_(ocorrencias))
        ),
        "conteudos": await n(select(RelatorioConteudo.id).where(RelatorioConteudo.inspecao_id.in_(inspecoes))),
        "responsaveis": await n(select(Responsavel.id).where(Responsavel.nome.like(PREF.like))),
        "usuarios": await n(select(Usuario.id).where(Usuario.email == PREF.email)),
    }


@pytest.fixture
async def limpo():
    storage = StorageFake()
    async with TestSessionLocal() as db:
        await seed_demo.limpar(db, PREF, storage)
    yield storage
    async with TestSessionLocal() as db:
        await seed_demo.limpar(db, PREF, storage)


async def test_seed_duas_vezes_nao_duplica(limpo):
    async with TestSessionLocal() as db:
        primeira = await seed_demo.seed(db, limpo, PREF)
        antes = await _contagens(db)
    async with TestSessionLocal() as db:
        segunda = await seed_demo.seed(db, limpo, PREF)
        depois = await _contagens(db)

    assert antes == depois
    assert segunda.criados == {}
    assert primeira.inspecoes == segunda.inspecoes
    assert set(primeira.inspecoes) == {"RFO", "LTIP", "RFIP", "VISTORIA_CAUTELAR", "VISTORIA_RESIDENCIAL"}


async def test_seed_cria_o_volume_esperado(limpo):
    async with TestSessionLocal() as db:
        await seed_demo.seed(db, limpo, PREF)
        c = await _contagens(db)
        fotos = list((await db.execute(select(Foto).where(Foto.storage_key.like(f"{PREF.storage}%")))).scalars())

    assert c["edificacoes"] == 1
    assert c["contratos"] == c["inspecoes"] == c["conteudos"] == 5
    assert c["visitas"] == 2 and c["mao_obra"] > 0 and c["medicoes"] == 4
    assert c["ocorrencias"] == 4 * seed_demo.N_OCORRENCIAS
    assert c["fotos"] == 6 + 4 * seed_demo.N_OCORRENCIAS == len(fotos)
    assert c["usuarios"] == 1
    # Fotos aprovadas, com legenda, e o arquivo existe no storage (1200 px).
    assert all(f.status_validacao_ia == "aprovada" and f.legenda and f.aprovado_por_id for f in fotos)
    assert all(f.storage_key in limpo.objetos for f in fotos)
    largura, _ = Image.open(io.BytesIO(limpo.objetos[fotos[0].storage_key])).size
    assert largura == seed_demo.LADO_FOTO


async def test_seed_preenche_fiscal_ocorrencias_e_conteudo(limpo):
    async with TestSessionLocal() as db:
        await seed_demo.seed(db, limpo, PREF)
        fiscal = await db.scalar(select(Responsavel).where(Responsavel.nome.like(PREF.like), Responsavel.tipo == "fiscal"))
        edif = await db.scalar(select(Edificacao).where(Edificacao.nome.like(PREF.like)))
        ocorrencias = list(
            (
                await db.execute(
                    select(Ocorrencia).join(Inspecao).join(Contrato).where(Contrato.edificacao_id == edif.id)
                )
            ).scalars()
        )
        conteudos = {
            c.tipo: c.dados
            for c in (
                await db.execute(
                    select(RelatorioConteudo).join(Inspecao).join(Contrato).where(Contrato.edificacao_id == edif.id)
                )
            ).scalars()
        }

    assert fiscal.crea and fiscal.titulo_profissional and fiscal.qualificacoes
    assert edif.endereco and edif.cep
    assert {o.sistema_id for o in ocorrencias} and len({o.sistema_id for o in ocorrencias}) <= seed_demo.N_SISTEMAS
    assert all(o.grau_risco in {"CRITICO", "MEDIO", "MINIMO"} for o in ocorrencias)
    assert all(o.gut_gravidade and o.gut_urgencia and o.gut_tendencia for o in ocorrencias)
    assert conteudos["VISTORIA_CAUTELAR"]["parecer"]
    assert conteudos["VISTORIA_RESIDENCIAL"]["unidade"]


async def test_reset_recria_sem_duplicar(limpo):
    async with TestSessionLocal() as db:
        await seed_demo.seed(db, limpo, PREF)
        antes = await _contagens(db)
    async with TestSessionLocal() as db:
        await seed_demo.seed(db, limpo, PREF, reset=True)
        depois = await _contagens(db)
    assert antes == depois


async def test_limpar_remove_so_o_prefixo(limpo):
    async with TestSessionLocal() as db:
        await seed_demo.seed(db, limpo, PREF)
        await seed_demo.limpar(db, PREF, limpo)
        c = await _contagens(db)
    assert all(v == 0 for v in c.values())
    assert not limpo.objetos
