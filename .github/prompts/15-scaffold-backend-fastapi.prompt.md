---
description: "Ativa o agente Engenheiro Backend para criar o scaffold inicial do backend FastAPI do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-02 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 0 (Fundação Técnica) de `00_docs/projeto/ciclo-de-vida.md`.
Estrutura de pastas definida em `00_docs/arquitetura.md` Seção 7. Stack: FastAPI (Python 3.12) + SQLAlchemy 2 async + Pydantic v2 (DEC-05).
Esta tarefa depende apenas do ambiente de desenvolvimento (prompt `14-setup-ambiente-desenvolvimento.prompt.md`) e é 100% desbloqueada — não depende de B-01 nem B-02.

## Tarefa
Assuma o papel de **Engenheiro Backend** e crie o scaffold inicial do backend:

1. Crie a estrutura de pastas em `04_backend/app/` conforme `00_docs/arquitetura.md` Seção 7:
   ```
   backend/
     app/
       api/v1/
       models/
       schemas/
       services/
       core/
       main.py
     templates/assets/
     alembic/
   ```
2. Configure `04_backend/app/core/config.py` para carregar variáveis de ambiente (URL do PostgreSQL, credenciais do MinIO, secret JWT) via Pydantic Settings.
3. Configure `04_backend/app/main.py` com a instância FastAPI, CORS básico e um endpoint `GET /health` retornando status da API e conectividade com o PostgreSQL.
4. Crie `04_backend/requirements.txt` (ou `pyproject.toml`) com as dependências principais: fastapi, uvicorn, sqlalchemy, alembic, asyncpg, pydantic-settings, python-jose, passlib[bcrypt], boto3, weasyprint, docxtpl, jinja2, pytest, httpx.
5. Adicione o serviço `backend` ao `05_infra/docker-compose.yml` (criado no prompt 14), com build a partir de um `Dockerfile` de desenvolvimento simples (contexto de build: `../04_backend`).
6. Escreva um teste (`04_backend/tests/test_health.py`) validando que `GET /health` retorna 200.
7. Rode os testes e valide que a API sobe localmente.

## Saída Esperada
- Estrutura de pastas do backend criada
- `04_backend/app/main.py` com endpoint `/health` funcional
- `04_backend/Dockerfile` e serviço `backend` no `05_infra/docker-compose.yml`
- `04_backend/requirements.txt` com dependências
- Teste `test_health.py` passando
- Resumo: como rodar o backend localmente e como executar os testes

## Restrições
- NÃO implemente ainda modelos de negócio, autenticação ou endpoints de domínio — isso é feito em tarefas subsequentes (prompts 17, 19 e seguintes).
- NÃO desvie da estrutura de pastas definida em `00_docs/arquitetura.md` sem justificar (o código deve ficar em `04_backend/`, não em `backend/` na raiz).
- SEMPRE valide entradas nos limites do sistema (mesmo que mínimas nesta etapa).
- Leia os arquivos antes de modificá-los.
