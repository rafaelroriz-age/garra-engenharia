"""Service Layer de `PromptIA` (BL-37; DEC-37 DP-2). Versões imutáveis; uma ativa por nome."""
import hashlib
import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, DomainError, NotFoundError
from app.models import PromptIA


def calcular_hash(conteudo: str) -> str:
    """SHA-256 hex do conteúdo (valor de `fotos.prompt_conteudo_hash`)."""
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


async def criar_versao(
    db: AsyncSession, *, nome: str, conteudo: str, criado_por_id: uuid.UUID | None = None
) -> PromptIA:
    nome = nome.strip()
    if not nome or not conteudo.strip():
        raise DomainError("Nome e conteúdo do prompt são obrigatórios.", type_suffix="prompt-ia-invalido")
    versoes = (await db.execute(select(PromptIA.versao).where(PromptIA.nome == nome))).scalars().all()
    proxima = max((int(v) for v in versoes if v.isdigit()), default=0) + 1
    prompt = PromptIA(nome=nome, versao=str(proxima), conteudo=conteudo, ativo=False, criado_por_id=criado_por_id)
    db.add(prompt)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("Versão do prompt criada em concorrência.", type_suffix="prompt-ia-versao-conflito") from exc
    return prompt


async def ativar(db: AsyncSession, prompt_id: uuid.UUID) -> PromptIA:
    prompt = await db.get(PromptIA, prompt_id)
    if prompt is None:
        raise NotFoundError(f"Prompt '{prompt_id}' não encontrado.", type_suffix="prompt-ia-nao-encontrado")
    await db.execute(
        update(PromptIA).where(PromptIA.nome == prompt.nome, PromptIA.id != prompt.id).values(ativo=False)
    )
    prompt.ativo = True
    await db.commit()
    return prompt


async def obter_ativo(db: AsyncSession, nome: str) -> PromptIA:
    prompt = (
        await db.execute(select(PromptIA).where(PromptIA.nome == nome, PromptIA.ativo))
    ).scalar_one_or_none()
    if prompt is None:
        raise DomainError(
            f"Não há versão ativa do prompt '{nome}'.", type_suffix="prompt-ia-sem-versao-ativa",
            title="Prompt de IA indisponível",
        )
    return prompt


async def alterar_conteudo(db: AsyncSession, prompt_id: uuid.UUID, conteudo: str) -> PromptIA:
    """Sempre recusa: versões são imutáveis (DP-2); crie uma nova versão."""
    raise DomainError(
        "O conteúdo de uma versão de prompt é imutável; crie uma nova versão.",
        type_suffix="prompt-ia-imutavel", title="Prompt imutável", status_code=409,
    )
