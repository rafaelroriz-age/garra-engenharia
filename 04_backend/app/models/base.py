"""Base declarativa do SQLAlchemy 2 (async) compartilhada por todos os modelos.

Ver `00_docs/arquitetura.md` Seção 3 (Diagrama ER) e DEC-07
(`00_docs/projeto/decisoes.md`).
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base declarativa para todos os modelos ORM do domínio."""
