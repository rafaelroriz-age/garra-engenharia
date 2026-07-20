---
description: "Ativa o agente Engenheiro DevOps para implementar docker-compose.prod.yml e o reverse proxy Nginx com HTTPS do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-27 do backlog em `00_docs/projeto/backlog-tarefas.md`, derivada de DEC-14 (`00_docs/projeto/decisoes.md`) e do mesmo escopo de BL-24 (deploy de produção).
Plano completo de gestão de configuração em `00_docs/projeto/plano-gestao-configuracao.md`: CD via GitHub Actions (`cd-staging.yml` automático, `cd-production.yml` manual por tag), ambos já referenciam `05_infra/docker-compose.prod.yml` e `05_infra/nginx/nginx.conf`, que **ainda não existem** — são pré-requisitos para o primeiro deploy real funcionar.
Estrutura de pastas (DEC-09): toda a infraestrutura reside em `05_infra/`, com build context apontando para `../04_backend` e `../03_frontend`.
Topologia de deploy alvo descrita em `00_docs/arquitetura.md` Seção 10.5 (Nginx → frontend/backend → PostgreSQL/Redis/MinIO).
Esta tarefa **não depende** da decisão final de hospedagem (B-03) — o `docker-compose.prod.yml` deve ser agnóstico de provedor (roda em qualquer VPS/servidor Linux com Docker).

## Tarefa
Assuma o papel de **Engenheiro DevOps** e implemente:

1. `05_infra/docker-compose.prod.yml`: serviços `nginx`, `frontend`, `backend`, `celery-worker`, `postgres`, `redis`, `minio` (mesma topologia da Seção 10.5 de `00_docs/arquitetura.md`), com:
   - Volumes nomeados persistentes para `postgres`, `minio` e certificados
   - `restart: unless-stopped` em todos os serviços de aplicação
   - Variáveis sensíveis lidas de `.env` (nunca hardcoded), reaproveitando as chaves já documentadas em `05_infra/.env.example`
   - Healthchecks em todos os serviços (reaproveitar o padrão de `05_infra/docker-compose.yml`)
2. `05_infra/nginx/nginx.conf`: reverse proxy roteando `/api/*` para o backend e o restante para o frontend, com:
   - HTTPS via Let's Encrypt/Certbot (ou Caddy, se preferir simplicidade — registre a escolha como decisão)
   - Headers de segurança: HSTS, CSP, X-Frame-Options, X-Content-Type-Options (mitigação A05 OWASP, `00_docs/arquitetura.md` Seção 10.1)
   - Redirecionamento HTTP → HTTPS
3. Atualize `05_infra/.env.example` caso novas variáveis sejam necessárias (ex.: domínio, e-mail para Certbot).
4. Valide localmente subindo o `docker-compose.prod.yml` (pode usar certificado self-signed ou HTTP puro para validação local, documentando a diferença para o ambiente real).
5. Atualize `05_infra/README.md` com instruções de deploy em produção usando este arquivo.

## Saída Esperada
- `05_infra/docker-compose.prod.yml` funcional
- `05_infra/nginx/nginx.conf` com HTTPS e headers de segurança configurados
- `05_infra/README.md` atualizado com o procedimento de deploy de produção
- Resumo: como validar localmente, o que precisa ser configurado manualmente no servidor real (domínio, DNS, certificado)

## Restrições
- NÃO hardcode domínio, e-mail ou segredos no `docker-compose.prod.yml` — sempre via `.env`.
- NÃO remova os healthchecks já existentes no `docker-compose.yml` de desenvolvimento.
- NÃO tome a decisão de hospedagem (B-03) por conta própria — mantenha a solução agnóstica de provedor.
- Leia os arquivos antes de modificá-los.
