---
description: "Ativa o agente Engenheiro DevOps para configurar infraestrutura, CI/CD, containers, deploy, monitoramento e backup do sistema de relatórios prediais."
---
## Contexto

Sistema de automação de relatórios prediais da Garra Engenharia.

**Stack definida em `00_docs/arquitetura.md`:**
- **Backend:** FastAPI (Python)
- **Frontend:** Next.js 14 (PWA)
- **Banco de dados:** PostgreSQL
- **Storage de imagens:** MinIO (compatível S3)
- **Geração de PDF:** WeasyPrint ou Puppeteer
- **Cache/filas:** Redis (opcional)

O sistema roda em VPS Linux (ou cloud equivalente). O engenheiro usa o sistema em campo via mobile/tablet — disponibilidade e HTTPS são essenciais.

## Tarefa

Assuma o papel de **Engenheiro DevOps** e configure toda a infraestrutura operacional:

### 1. Containerização
- `04_backend/Dockerfile` — multi-stage para FastAPI (build + runtime, usuário não-root)
- `03_frontend/Dockerfile` — multi-stage para Next.js (build + serve com Node)
- `05_infra/docker-compose.yml` — ambiente local completo: backend + frontend + PostgreSQL + MinIO + Redis (build context aponta para `../04_backend` e `../03_frontend`)
- `05_infra/docker-compose.prod.yml` — ambiente de produção com volumes persistentes e restart policies
- `05_infra/.env.example` — todas as variáveis de ambiente documentadas (DB, MinIO, JWT secret, URLs)

### 2. Reverse Proxy e HTTPS
- `05_infra/nginx/nginx.conf` — proxy reverso para backend (porta 8000) e frontend (porta 3000) com HTTPS automático via Let's Encrypt (Certbot ou Caddy)
- Headers de segurança: HSTS, CSP, X-Frame-Options, X-Content-Type-Options

### 3. CI/CD com GitHub Actions
- `.github/workflows/ci.yml` — em cada PR:
  - Lint + type-check (Python: ruff/mypy; JS: ESLint/tsc)
  - Testes unitários (pytest + jest)
  - Build de imagens Docker
  - Scan de vulnerabilidades (Trivy)
- `.github/workflows/cd-staging.yml` — deploy automático em staging após merge em `main`
- `.github/workflows/cd-production.yml` — deploy em produção com aprovação manual + healthcheck pós-deploy

### 4. Backup e Recuperação
- `05_infra/backup/backup-db.sh` — dump diário do PostgreSQL com retenção de 30 dias
- `05_infra/backup/restore-db.sh` — procedimento de restore documentado
- Estratégia de backup para volumes MinIO (fotos dos relatórios)

### 5. Monitoramento
- Health checks em todos os serviços do docker-compose
- Logs estruturados em JSON no backend (configurar logging do FastAPI)
- Alertas básicos: serviço down, disco > 80%, erros 5xx

### 6. Documentação Operacional
- `05_infra/README.md` com:
  - Pré-requisitos (Docker, domínio, servidor)
  - Como rodar localmente (passo a passo)
  - Como fazer deploy em produção
  - Como reverter para versão anterior (rollback)
  - Variáveis de ambiente obrigatórias

## Saída Esperada

```
05_infra/
  docker-compose.yml
  docker-compose.prod.yml
  .env.example
  nginx/nginx.conf
  backup/backup-db.sh
  backup/restore-db.sh
  README.md
04_backend/
  Dockerfile
03_frontend/
  Dockerfile
.github/workflows/
  ci.yml
  cd-staging.yml
  cd-production.yml
```

## Restrições
- NÃO hardcode senhas ou tokens — use variáveis de ambiente e GitHub Secrets.
- NÃO exponha PostgreSQL ou MinIO para a internet — somente na rede interna do Docker.
- SEMPRE inclua healthcheck em todos os serviços do compose.
- O deploy em produção DEVE exigir aprovação manual no pipeline.
- Teste o `docker compose up` localmente antes de considerar concluído.
