"""Endpoints de Responsável (fiscal / responsável legal / RTE / contratante).

Fora do contrato original de `00_docs/arquitetura.md` Seção 4 — registrado
como DEC-23 em `00_docs/projeto/decisoes.md`. Antes desta tarefa, `Responsavel`
só era criado diretamente no banco (fixtures de teste, `tests/*.py`); o
formulário de Contrato (`03_frontend/app/contratos/contrato-form.tsx`) exige
que o usuário digite UUIDs de `fiscal_id`/`responsavel_legal_id`/`rte_id` já
existentes, mas não havia nenhuma forma de criá-los ou consultá-los via API —
gap de integração encontrado ao implementar os testes E2E (BL-21).

- `GET /responsaveis` — lista (filtro opcional por `tipo`), sem paginação
  (volume esperado é baixo: fiscais/executoras/contratantes de um único
  engenheiro ou pequena equipe).
- `POST /responsaveis` — cria um Responsável.

Leitura liberada à equipe (`auditor`/`auxiliar`); criação restrita ao `auditor`
(RN-18, DEC-27) — responsável técnico/legal é dado contratual, não de campo.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor, require_equipe
from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models import Responsavel, Usuario
from app.schemas import ResponsavelCreate, ResponsavelRead

router = APIRouter(prefix="/api/v1/responsaveis", tags=["responsaveis"])


@router.get("", response_model=list[ResponsavelRead])
async def listar_responsaveis(
    tipo: str | None = Query(None, description="Filtra por tipo (ex.: fiscal, responsavel_legal, rte, sindico)"),
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> list[Responsavel]:
    """Lista responsáveis, com filtro opcional por `tipo`."""
    query = select(Responsavel).order_by(Responsavel.nome)
    if tipo:
        query = query.where(Responsavel.tipo == tipo)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=ResponsavelRead, status_code=status.HTTP_201_CREATED)
async def criar_responsavel(
    dados: ResponsavelCreate,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> Responsavel:
    """Cria um novo Responsável (fiscal, responsável legal, RTE ou contratante)."""
    responsavel = Responsavel(**dados.model_dump())
    db.add(responsavel)
    await db.commit()
    await db.refresh(responsavel)
    return responsavel


@router.get("/{responsavel_id}", response_model=ResponsavelRead)
async def obter_responsavel(
    responsavel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Responsavel:
    """Detalhe de um Responsável (usado para validação pontual, ex.: pré-preencher formulário)."""
    responsavel = await db.get(Responsavel, responsavel_id)
    if responsavel is None:
        raise NotFoundError(f"Responsável {responsavel_id} não encontrado.")
    return responsavel
