---
title: Guia de contribuição
type: gestao
status: ativo
owner: Garra Engenharia
related:
  - 00_docs/projeto/plano-gestao-configuracao.md
  - .github/pull_request_template.md
  - 00_docs/projeto/decisoes.md
  - BACKLOG.md
  - 00_docs/backlog-auto/BACKLOG-MANUAL.md
tags: [contribuicao, git, commits, pr, convencoes, agentes]
last_updated: 2026-11-03
---

<!-- ai-summary
System: regras para contribuir no monorepo, reunidas por referência às fontes oficiais.
Flow: pastas (DEC-09) -> branch a partir de main -> Conventional Commits -> PR com checklist -> CI -> sync para main_back/main_front (DEC-22).
Owner: Garra Engenharia.
Status: ativo (verificado na D05, 2026-11-04) — consolidado na D04 (2026-11-03); em caso de conflito, vale a fonte citada em cada item.
-->

# Guia de contribuição

Este guia reúne regras que estão espalhadas pelo projeto. Ele não as substitui: em caso de conflito, vale a fonte citada em cada item. Para montar o ambiente, veja [guia-desenvolvimento.md](guia-desenvolvimento.md).

## 1. Estrutura de pastas (DEC-09, ADR-05)

| Pasta | Conteúdo |
|---|---|
| `00_docs/` | documentação ([índice](README.md)) |
| `01_output-context/` | originais do cliente: **nunca alterar nem apagar** (são a fonte dos templates; DEC-25, ADR-13). Os binários ficam fora do git (`.gitignore`, seção "Documentos originais do cliente") |
| `02_prototipos/` | protótipos HTML estáticos |
| `03_frontend/` | Next.js (PWA) |
| `04_backend/` | FastAPI |
| `05_infra/` | Docker Compose, Nginx, backup |

Não crie pastas na raiz, nem `src/` ou `infra/` (`05_infra/README.md`, "Decisão fixa"; `.github/agents/devops.agent.md`). Exceções que já existem: `.github/` (caminho exigido pelo GitHub) e `backlog-auto/` (ferramenta de automação do backlog, `backlog.toml`).

## 2. Branches (DEC-22)

- `main` é o tronco: todo commit e todo PR, inclusive do Dependabot, entram em `main` (`.github/workflows/ci.yml`, cabeçalho; `render.yaml`, cabeçalho).
- `main_back` e `main_front` são branches de deploy do Render (`render.yaml`: `garra-backend` e `garra-frontend`). Recebem `main` automaticamente por merge (`.github/workflows/sync-deploy-branches.yml`). **Não commite nelas nem abra PR contra elas.**
- Não há branches de staging (removidas pela DEC-22; `git branch -r` não lista nenhuma).
- Branches de trabalho: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>` ([plano-gestao-configuracao.md](projeto/plano-gestao-configuracao.md) §1.1).

## 3. Commits

Conventional Commits com escopo da pasta e rodapé de referência ([plano-gestao-configuracao.md](projeto/plano-gestao-configuracao.md) §1.2):

```text
feat(backend): implementa autenticação JWT (BL-06)

Refs BL-06
```

Tipos: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `perf`. Escopos: `backend`, `frontend`, `infra`, `docs` (o histórico também usa `00_docs`, ex.: `git log --oneline | grep "docs(00_docs)"`).

## 4. Pull request

Use o checklist de [.github/pull_request_template.md](../.github/pull_request_template.md):

- testes novos ou atualizados; `pytest` (`04_backend`) e `npm run lint` + `npm run build` (`03_frontend`) passando localmente;
- nenhum segredo commitado (`.env`, chaves, tokens). O `.gitignore` da raiz ignora `.env` e `.env.*`, exceto `.env.example` e `.env.render.example`;
- migration Alembic nova sempre com `downgrade()` testado;
- variável de ambiente nova no `.env.example` correspondente (ver [configuracao.md](configuracao.md));
- `00_docs/` atualizado se o comportamento ou uma decisão mudou.

O PR referencia o item do backlog (`BL-XX`, em `00_docs/projeto/backlog-tarefas.md`), os requisitos (`RF/RN/RNF`, em `00_docs/estudo-do-contexto.md`) e a decisão, se houver (`DEC-XX`, em `00_docs/projeto/decisoes.md`).

O CI (`.github/workflows/ci.yml`) roda em todo PR para `main`: `ruff check .` (não bloqueante), `pytest`, `npm run lint` (não bloqueante), `npm run build`, build das imagens com scan Trivy (`HIGH`/`CRITICAL` falham) e o E2E Playwright.

## 5. Regras de código que afetam a documentação

- **Templates gerados não se editam à mão.** `templates/rfo/*` e `templates/ltip/*` saem de `app/scripts/build_rfo_templates.py` e `build_ltip_templates.py`; altere o gerador e regere (`04_backend/README.md`, seção BL-12/BL-13). Os ativos de marca saem de `app/scripts/build_brand_assets.py` (DEC-30, ADR-16).
- **PDF e DOCX derivam do mesmo `layout.json`** (DEC-25, ADR-13).
- **Autoria vem do token**, nunca do payload (`criado_por_id`, DEC-27).
- Requisitos ficam em `estudo-do-contexto.md`; decisões novas entram como `DEC-XX` em `decisoes.md`; ADRs em `arquitetura.md` §8.

## 6. Convenção dos documentos em `00_docs/`

Os documentos usam frontmatter YAML (`title`, `type`, `status`, `owner`, `related`, `tags`, `last_updated`) e um bloco `<!-- ai-summary ... -->` logo abaixo (modelo: `00_docs/estudo-do-contexto.md`; origem da convenção: `.github/agents/prompt_infra_segundo_cerebro_projeto_novo.md`). Todo documento novo entra no [índice](README.md) com uma linha.

## 7. Agentes e automação do backlog

- Instruções por papel em `.github/agents/*.agent.md` (backend, frontend, devops, arquiteto-software, design-ui-ux etc.) e prompts de tarefa em `.github/prompts/*.prompt.md`.
- `BACKLOG.md` (raiz) é o backlog executável do `backlog-auto`: cada tarefa roda numa sessão em worktree isolado, seguindo a "Regra de pronto" do próprio arquivo. Em lote paralelo, as sessões **não editam** `BACKLOG.md` nem os documentos de gestão compartilhados (`backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`); esses são atualizados no "Fechamento de lote" (`BACKLOG.md`).
- Manual da ferramenta: [00_docs/backlog-auto/BACKLOG-MANUAL.md](backlog-auto/BACKLOG-MANUAL.md). Configuração: `backlog.toml` (inclui a barreira `[guard]` contra push, apagar volumes Docker, tocar no banco do Render e apagar originais do cliente).
