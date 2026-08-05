"""Endpoints de autenticação (BL-06, RNF-05, DEC-05).

- `POST /api/v1/auth/register` — cria novo usuário (uso interno, sem cadastro público).
- `POST /api/v1/auth/login` — valida email/senha e retorna access token JWT.
- `GET /api/v1/auth/me` — retorna os dados do usuário autenticado.

Ver `app/api/deps.py` (`get_current_user`) para proteção de rotas e
`app/core/security.py` para hashing/JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Usuario
from app.schemas import LoginRequest, Token, UsuarioCreate, UsuarioRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def register(dados: UsuarioCreate, db: AsyncSession = Depends(get_db)) -> Usuario:
    """Cria um novo usuário (uso interno da equipe, sem cadastro público)."""
    result = await db.execute(select(Usuario).where(Usuario.email == dados.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_password(dados.senha),
        ativo=True,
        role="auditor",
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
async def login(dados: LoginRequest, db: AsyncSession = Depends(get_db)) -> Token:
    """Valida email/senha e retorna um access token JWT."""
    result = await db.execute(select(Usuario).where(Usuario.email == dados.email))
    usuario = result.scalar_one_or_none()

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha inválidos.",
    )
    if usuario is None or not usuario.ativo or not verify_password(dados.senha, usuario.senha_hash):
        raise credenciais_invalidas

    access_token = create_access_token(subject=str(usuario.id))
    return Token(access_token=access_token)


@router.get("/me", response_model=UsuarioRead)
async def me(usuario_atual: Usuario = Depends(get_current_user)) -> Usuario:
    """Retorna os dados do usuário autenticado (identificado pelo token)."""
    return usuario_atual
