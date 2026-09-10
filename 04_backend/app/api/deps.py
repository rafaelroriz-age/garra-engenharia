"""Dependencies de FastAPI compartilhadas entre routers (BL-06).

`get_current_user` protege rotas autenticadas: extrai o token `Bearer` do
header `Authorization`, valida/decodifica via `app.core.security` e carrega o
`Usuario` correspondente. Retorna 401 em qualquer falha (token ausente,
inválido, expirado ou usuário inexistente/inativo).
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import DomainError, NotFoundError
from app.core.security import decode_access_token
from app.models import Responsavel, Usuario

# tokenUrl é apenas informativo para a documentação OpenAPI (login usa JSON, não form).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais inválidas ou expiradas.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Resolve o `Usuario` autenticado a partir do token `Bearer`, ou lança 401."""
    if token is None:
        raise _CREDENTIALS_EXCEPTION

    subject = decode_access_token(token)
    if subject is None:
        raise _CREDENTIALS_EXCEPTION

    try:
        usuario_id = uuid.UUID(subject)
    except ValueError:
        raise _CREDENTIALS_EXCEPTION from None

    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if usuario is None or not usuario.ativo:
        raise _CREDENTIALS_EXCEPTION

    return usuario


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario | None:
    """Como `get_current_user`, mas devolve `None` em vez de 401 quando não autenticado.

    Usado por rotas que mudam de comportamento conforme haja ou não sessão
    (ex.: bootstrap do primeiro usuário em `POST /auth/register`, BL-23).
    """
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None


def require_role(*roles: str):
    """Garante que o usuário autenticado possua um dos papéis exigidos."""

    async def dependency(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.role not in roles:
            raise DomainError(
                detail="Você não possui permissão para acessar este recurso.",
                type_suffix="acesso-negado",
                title="Acesso negado",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return dependency


# Perfis de acesso (RN-18, DEC-27/ADR-14). `require_equipe` cobre os dados de campo e as
# leituras internas; `require_auditor` cobre o que exige responsabilidade técnica ou
# administração (contratos, edificações, responsáveis, emissão de relatório e cadastro
# de usuários). O perfil `cliente` nunca alcança nenhuma das duas — só acessa `/portal/*`.
require_auditor = require_role("auditor")
require_equipe = require_role("auditor", "auxiliar")


async def get_current_cliente_responsavel(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Responsavel:
    """Resolve o `Responsavel` vinculado ao usuário autenticado para o Portal do Cliente."""
    result = await db.execute(select(Responsavel).where(Responsavel.usuario_id == current_user.id))
    responsavel = result.scalar_one_or_none()
    if responsavel is None:
        raise NotFoundError(
            detail="Nenhum responsável vinculado ao usuário autenticado foi encontrado.",
            type_suffix="recurso-nao-encontrado",
        )
    return responsavel
