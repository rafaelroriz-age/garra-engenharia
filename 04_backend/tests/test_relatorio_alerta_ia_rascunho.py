"""Alerta de fotos com legenda IA em rascunho na emissão do relatório (BL-38, DEC-37 DP-9 proposta).

`fotos_ia_em_rascunho` (ids das fotos) na resposta de `POST /inspecoes/{id}/relatorios/rfo`.
Alerta, não bloqueio: a emissão segue com 201. Exige o PostgreSQL de 05_infra (localhost:5433).
"""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.models import Foto
from tests.test_relatorios_emissao_generica import (  # noqa: F401  (fixtures reutilizadas)
    FOTO_RFO,
    _auth,
    _TestSessionLocal,
    api,
    cenario,
)


async def _marcar_foto(**campos) -> str:
    async with _TestSessionLocal() as s:
        await s.execute(update(Foto).where(Foto.storage_key == FOTO_RFO).values(**campos))
        await s.commit()
        return str((await s.execute(select(Foto.id).where(Foto.storage_key == FOTO_RFO))).scalar_one())


def _emitir(ctx, dados):
    client: TestClient = ctx[0]
    return client.post(
        f"/api/v1/inspecoes/{dados["rfo_id"]}/relatorios/rfo",
        headers=_auth(dados["usuarios"]["auditor"]),
    )


@pytest.mark.asyncio
async def test_sem_rascunhos_devolve_lista_vazia(api, cenario):  # noqa: F811
    resp = _emitir(api, cenario)
    assert resp.status_code == 201, resp.text
    assert resp.json()["fotos_ia_em_rascunho"] == []


@pytest.mark.asyncio
async def test_com_rascunho_lista_id_da_foto_e_emite_mesmo_assim(api, cenario):  # noqa: F811
    foto_id = await _marcar_foto(legenda_ia_sugerida="Sugestão IA", status_validacao_ia="rascunho")
    resp = _emitir(api, cenario)
    assert resp.status_code == 201, resp.text  # alerta, não bloqueio
    corpo = resp.json()
    assert corpo["fotos_ia_em_rascunho"] == [foto_id]
    assert corpo["tem_pdf"] and corpo["tem_docx"]


@pytest.mark.asyncio
async def test_legenda_aprovada_e_ignorada(api, cenario):  # noqa: F811
    await _marcar_foto(
        legenda_ia_sugerida="Sugestão IA",
        status_validacao_ia="aprovada",
        aprovado_por_id=cenario["usuarios"]["auditor"].id,
        aprovado_em=datetime.now(UTC),
    )
    resp = _emitir(api, cenario)
    assert resp.status_code == 201, resp.text
    assert resp.json()["fotos_ia_em_rascunho"] == []
