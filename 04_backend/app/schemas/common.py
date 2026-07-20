"""Schema genérico de resposta paginada, reutilizado pelos endpoints de listagem
(`GET /edificacoes`, `GET /contratos`, etc.) que exigem paginação (Seção 4 de
`00_docs/arquitetura.md`).
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope de paginação: `items` da página atual + metadados."""

    items: list[T]
    total: int
    page: int
    page_size: int
