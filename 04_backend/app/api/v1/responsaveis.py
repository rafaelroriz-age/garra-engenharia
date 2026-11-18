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
- `POST /responsaveis` — cria um Responsável; `usuario_id` segue a mesma regra
  do `PUT` (422 se o usuário não existe, 409 se já vinculado) — DEC-59.
- `PUT /responsaveis/{id}` — atualização parcial (DEC-50): só o auditor; campo
  omitido não muda; `usuario_id` segue a regra do `POST` (ver `atualizar_responsavel`).

Leitura liberada à equipe (`auditor`/`auxiliar`); criação restrita ao `auditor`
(RN-18, DEC-27) — responsável técnico/legal é dado contratual, não de campo.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor, require_equipe
from app.core.database import get_db
from app.core.errors import ConflictError, DomainError, NotFoundError
from app.models import Responsavel, Usuario
from app.schemas import ResponsavelCreate, ResponsavelRead, ResponsavelUpdate

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


async def _validar_vinculo_usuario(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    responsavel_id: uuid.UUID | None,
) -> None:
    """Regra de `usuario_id` (POST e PUT): o usuário precisa existir (422) e não
    pode já estar vinculado a outro Responsável (409). `responsavel_id` é o
    Responsável sendo atualizado (excluído da checagem); `None` na criação."""
    if await db.get(Usuario, usuario_id) is None:
        raise DomainError(detail=f"Usuário {usuario_id} não encontrado.")
    filtros = [Responsavel.usuario_id == usuario_id]
    if responsavel_id is not None:
        filtros.append(Responsavel.id != responsavel_id)
    ocupado = await db.execute(select(Responsavel.id).where(*filtros))
    if ocupado.first() is not None:
        raise ConflictError(f"O usuário {usuario_id} já está vinculado a outro Responsável.")


@router.post("", response_model=ResponsavelRead, status_code=status.HTTP_201_CREATED)
async def criar_responsavel(
    dados: ResponsavelCreate,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> Responsavel:
    """Cria um novo Responsável (fiscal, responsável legal, RTE ou contratante).

    `usuario_id` (opcional) segue a regra de `_validar_vinculo_usuario`: 422 se
    o usuário não existe, 409 se já está vinculado a outro Responsável.
    """
    if dados.usuario_id is not None:
        await _validar_vinculo_usuario(db, dados.usuario_id, responsavel_id=None)
    responsavel = Responsavel(**dados.model_dump())
    db.add(responsavel)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("Conflito de unicidade ao criar o Responsável (usuario_id).") from exc
    await db.refresh(responsavel)
    return responsavel


@router.put("/{responsavel_id}", response_model=ResponsavelRead)
async def atualizar_responsavel(
    responsavel_id: uuid.UUID,
    dados: ResponsavelUpdate,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> Responsavel:
    """Atualização parcial de um Responsável (DEC-50). Só o auditor.

    Só os campos presentes no corpo mudam (`exclude_unset`). `nome` e `tipo`
    são obrigatórios no banco: `null` explícito é 422. `usuario_id` segue a
    mesma regra do `POST`: ele concede acesso ao Portal do Cliente (DEC-18), e
    só o auditor o altera; o usuário precisa existir e não pode já estar
    vinculado a outro Responsável (409). `null` desfaz o vínculo.
    """
    responsavel = await db.get(Responsavel, responsavel_id)
    if responsavel is None:
        raise NotFoundError(f"Responsável {responsavel_id} não encontrado.")

    alteracoes = dados.model_dump(exclude_unset=True)
    for campo in ("nome", "tipo"):
        if campo in alteracoes and alteracoes[campo] is None:
            raise DomainError(detail=f"O campo '{campo}' é obrigatório e não pode ser nulo.")

    novo_usuario_id = alteracoes.get("usuario_id")
    if novo_usuario_id is not None and novo_usuario_id != responsavel.usuario_id:
        await _validar_vinculo_usuario(db, novo_usuario_id, responsavel_id=responsavel_id)

    for campo, valor in alteracoes.items():
        setattr(responsavel, campo, valor)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("Conflito de unicidade ao atualizar o Responsável (usuario_id).") from exc
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
