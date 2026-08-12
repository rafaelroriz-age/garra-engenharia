"""Endpoints de autenticação (BL-06, RNF-05, DEC-05; hardening em BL-23).

- `POST /api/v1/auth/register` — cria novo usuário. Exige um `auditor`
  autenticado, exceto quando ainda não existe nenhum usuário (bootstrap da
  primeira instalação) — OWASP A01/A07.
- `POST /api/v1/auth/login` — valida email/senha e retorna access token JWT,
  com limite de tentativas malsucedidas por (IP, e-mail) — OWASP A07.
- `GET /api/v1/auth/me` — retorna os dados do usuário autenticado.

Ver `app/api/deps.py` (`get_current_user`) para proteção de rotas e
`app/core/security.py` para hashing/JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user
from app.core import rate_limit
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Usuario
from app.schemas import LoginRequest, Token, UsuarioCreate, UsuarioRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "desconhecido"


@router.post("/register", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def register(
    dados: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    usuario_atual: Usuario | None = Depends(get_optional_user),
) -> Usuario:
    """Cria um novo usuário (uso interno da equipe, sem cadastro público)."""
    total_usuarios = await db.scalar(select(func.count()).select_from(Usuario))
    if total_usuarios and (usuario_atual is None or usuario_atual.role != "auditor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas um auditor autenticado pode cadastrar novos usuários.",
        )

    result = await db.execute(select(Usuario).where(Usuario.email == dados.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_password(dados.senha),
        ativo=True,
        role=dados.role or "auditor",
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
async def login(dados: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)) -> Token:
    """Valida email/senha e retorna um access token JWT."""
    ip = _client_ip(request)

    bloqueio_restante = rate_limit.segundos_ate_liberar(ip, dados.email)
    if bloqueio_restante:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente mais tarde.",
            headers={"Retry-After": str(bloqueio_restante)},
        )

    result = await db.execute(select(Usuario).where(Usuario.email == dados.email))
    usuario = result.scalar_one_or_none()

    if usuario is None or not usuario.ativo or not verify_password(dados.senha, usuario.senha_hash):
        rate_limit.registrar_falha(ip, dados.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    rate_limit.registrar_sucesso(ip, dados.email)
    access_token = create_access_token(subject=str(usuario.id))
    return Token(access_token=access_token)


@router.get("/me", response_model=UsuarioRead)
async def me(usuario_atual: Usuario = Depends(get_current_user)) -> Usuario:
    """Retorna os dados do usuário autenticado (identificado pelo token)."""
    return usuario_atual
