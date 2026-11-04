"""Schema genérico de resposta paginada, reutilizado pelos endpoints de listagem
(`GET /edificacoes`, `GET /contratos`, etc.) que exigem paginação (Seção 4 de
`00_docs/arquitetura.md`).
"""
from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    """Envelope de paginação: `items` da página atual + metadados."""

    items: list[T]
    total: int
    page: int
    page_size: int
