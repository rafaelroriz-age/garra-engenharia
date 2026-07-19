---
description: "Ativa o agente Engenheiro DevOps para configurar o ambiente de desenvolvimento local com Docker Compose (PostgreSQL + MinIO) do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-01 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 0 (Fundação Técnica) de `00_docs/projeto/ciclo-de-vida.md`.
Stack e decisões em `00_docs/arquitetura.md` (Seção 1 e 7) e `00_docs/projeto/decisoes.md` (DEC-02 MinIO, DEC-07 PostgreSQL).
Esta tarefa é 100% desbloqueada — não depende das lacunas `[A ESCLARECER]` (B-01) nem dos templates Word (B-02).
Nenhum código existe ainda em `04_backend/` ou `03_frontend/`.
Convenção fixa do repositório (DEC-09): toda infraestrutura (docker-compose, `.env.example`, nginx, backups) vive em `05_infra/` — nunca na raiz do repositório.

## Tarefa
Assuma o papel de **Engenheiro DevOps** e configure o ambiente de desenvolvimento local:

1. Crie `05_infra/docker-compose.yml` com os serviços:
   - `postgres` (PostgreSQL 16) com volume persistente e variáveis de ambiente para usuário/senha/database
   - `minio` (armazenamento de objetos compatível S3) com volume persistente, console habilitado e bucket inicial para fotos/relatórios
2. Adicione healthcheck em cada serviço.
3. Crie `05_infra/.env.example` documentando todas as variáveis necessárias (credenciais do PostgreSQL, credenciais do MinIO, nome do bucket, portas).
4. Documente em `05_infra/docker-compose.yml` (comentários) o propósito de cada serviço.
5. Suba o ambiente localmente (`cd 05_infra && docker compose up -d`) e valide que ambos os serviços respondem (healthcheck OK).

## Saída Esperada
- `05_infra/docker-compose.yml` com serviços `postgres` e `minio`
- `05_infra/.env.example` documentando as variáveis de ambiente
- Confirmação de que `docker compose up -d` (executado a partir de `05_infra/`) sobe os dois serviços com healthcheck saudável
- Resumo: portas expostas, credenciais padrão de desenvolvimento, como parar/reiniciar o ambiente

## Restrições
- NÃO hardcode senhas — use variáveis de ambiente com valores de exemplo no `.env.example`.
- NÃO exponha PostgreSQL/MinIO além do necessário para desenvolvimento local (bind em `localhost`).
- NÃO inclua ainda os serviços `backend`/`frontend` no `docker-compose.yml` — isso é feito nas tarefas de scaffold (prompts 15 e 16).
- NÃO crie `docker-compose.yml` na raiz do repositório nem em `infra/` — o local definitivo é `05_infra/` (DEC-09).
- Leia os arquivos antes de modificá-los.
