"""Hashing de senha (bcrypt) e emissão/validação de token JWT (BL-06, RNF-05).

Ver DEC-05 (`00_docs/projeto/decisoes.md`) e `app/core/config.py` para as
variáveis `JWT_SECRET_KEY`/`JWT_ALGORITHM`/`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Nome da claim usada para identificar o usuário no payload do token (subject = id do usuário).
SUBJECT_CLAIM = "sub"


def hash_password(senha: str) -> str:
    """Gera o hash bcrypt de uma senha em texto plano."""
    return _pwd_context.hash(senha)


def verify_password(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash armazenado."""
    return _pwd_context.verify(senha, senha_hash)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Cria um token JWT assinado, com `subject` (id do usuário) como claim `sub`."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload: dict[str, Any] = {SUBJECT_CLAIM: subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Decodifica o token JWT e retorna o `subject` (id do usuário), ou `None` se inválido/expirado."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    return payload.get(SUBJECT_CLAIM)
