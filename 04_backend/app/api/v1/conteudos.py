"""Endpoints do conteúdo narrativo do relatório (V1-01).

- `GET /inspecoes/{id}/conteudo/{tipo}` — padrões do tipo mesclados com o salvo
  (equipe: `auditor`/`auxiliar`).
- `PUT /inspecoes/{id}/conteudo/{tipo}` — grava o conteúdo editado (só `auditor`:
  texto do laudo é responsabilidade técnica, RN-18/DEC-27).

`tipo` aceita minúsculas (`ltip` -> `LTIP`). Contrato de `dados` em
`app/schemas/relatorio_conteudo.py` e `00_docs/backlog-auto/v1-fundacao-dados.md`.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor, require_equipe
from app.core.database import get_db
from app.models import Usuario
from app.models.tipo_servico import TipoServico
from app.schemas.relatorio_conteudo import RelatorioConteudoRead, RelatorioConteudoUpdate
from app.services import relatorio_conteudo_service

router = APIRouter(prefix="/api/v1/inspecoes", tags=["conteudos"])


@router.get("/{inspecao_id}/conteudo/{tipo}", response_model=RelatorioConteudoRead)
async def obter_conteudo(
    inspecao_id: uuid.UUID,
    tipo: TipoServico,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> RelatorioConteudoRead:
    """Conteúdo do relatório `tipo` da inspeção: textos padrão + edições salvas."""
    return await relatorio_conteudo_service.obter(db, inspecao_id, tipo)


@router.put("/{inspecao_id}/conteudo/{tipo}", response_model=RelatorioConteudoRead)
async def salvar_conteudo(
    inspecao_id: uuid.UUID,
    tipo: TipoServico,
    payload: RelatorioConteudoUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_auditor),
) -> RelatorioConteudoRead:
    """Substitui o conteúdo salvo do relatório `tipo` e devolve o resultado mesclado."""
    return await relatorio_conteudo_service.salvar(db, inspecao_id, tipo, payload.dados, usuario_id=usuario.id)
