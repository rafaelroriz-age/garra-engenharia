"""Pacote de repositórios (Repository Pattern, `00_docs/arquitetura.md` Seção 9.2).

Um repositório por agregado, isolando as queries SQLAlchemy da camada de
serviço (`app/services/`). Endpoints (`app/api/v1/`) nunca acessam o
repositório diretamente — sempre através do service correspondente.
"""
