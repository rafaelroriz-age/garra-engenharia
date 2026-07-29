---
title: Registro de Decisões — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-27
---

# Registro de Decisões (Decision Log)

> Cada decisão é rastreável, datada e justificada. Revisões geram nova entrada referenciando a anterior.

---

## DEC-01 — Gerador de PDF: WeasyPrint + HTML/CSS Jinja2

| Campo | Valor |
|---|---|
| **Data** | 2026-07-08 |
| **Status** | Aprovada |
| **Contexto** | Laudos com até 200 páginas, tabelas complexas, cabeçalho/rodapé por página e 150+ fotos. Fidelidade visual ao template do cliente é mandatória (RNF-03). |
| **Alternativas** | ReportLab (complexo, difícil manter fidelidade), Puppeteer/Playwright (pesado, requer Chrome no servidor), LibreOffice headless (instável, lento) |
| **Decisão** | WeasyPrint + Jinja2. Templates HTML/CSS versionados no repositório. `@page` CSS para cabeçalho/rodapé. |
| **Justificativa** | Python nativo, integra diretamente no FastAPI, suporte CSS completo, sem overhead de processos externos. |
| **Consequências** | Validar visualmente os templates HTML antes de ir para produção. Possíveis sutilezas tipográficas vs. Word. |
| **Referência** | `00_docs/arquitetura.md` ADR-01 |

---

## DEC-02 — Armazenamento de Imagens: MinIO com API S3

| Campo | Valor |
|---|---|
| **Data** | 2026-07-08 |
| **Status** | Aprovada |
| **Contexto** | Relatórios acumulam 500+ fotos por contrato. Armazenar blobs no PostgreSQL degradaria performance e backup (RNF-07). |
| **Alternativas** | Sistema de arquivos local (sem URL pública, difícil backup), AWS S3 (custo recorrente), Cloudflare R2 (opção intermediária) |
| **Decisão** | MinIO self-hosted via Docker para desenvolvimento/produção inicial. Código usa SDK `boto3` (S3-compatível) para portabilidade. |
| **Justificativa** | Zero custo de serviço, controle total dos dados, migração trivial para S3/R2 se necessário. |
| **Consequências** | Gerenciar backup do volume MinIO. Configurar política de URL pré-assinada com expiração para downloads. |
| **Referência** | `00_docs/arquitetura.md` ADR-02 |

---

## DEC-03 — Mobile: PWA em vez de App Nativo

| Campo | Valor |
|---|---|
| **Data** | 2026-07-08 |
| **Status** | Aprovada (pendente confirmação de necessidade offline) |
| **Contexto** | Engenheiro usa smartphone em campo para registrar ocorrências e fotos (RNF-01). |
| **Alternativas** | App nativo React Native (melhor experiência, custo 3x maior), Flutter (idem), App Nativo puro (inviável para equipe pequena) |
| **Decisão** | PWA com Next.js 14. `manifest.json` com `display: standalone`. Service Worker para cache parcial. |
| **Justificativa** | Entregue como parte do frontend sem infraestrutura adicional. Suporte a câmera via `getUserMedia` e clipboard via API browser. |
| **Consequências** | [A ESCLARECER] confirmar necessidade de offline completo. Requer HTTPS para Clipboard API. |
| **Referência** | `00_docs/arquitetura.md` ADR-03 |

---

## DEC-04 — DOCX Editável: docxtpl (template Word + Jinja2)

| Campo | Valor |
|---|---|
| **Data** | 2026-07-08 |
| **Status** | Aprovada |
| **Contexto** | Engenheiro precisa de DOCX editável antes da entrega final (RNF-04). Recriar formatação Word programaticamente seria inviável. |
| **Alternativas** | python-docx puro (sem template; formatação perdida), LibreOffice (instável), pandoc (conversão de HTML, fidelidade baixa) |
| **Decisão** | docxtpl: usa o arquivo Word original do cliente como template com tags `{{ variavel }}` e `{%tr for ... %}`. |
| **Justificativa** | Preserva 100% da formatação do template original. O arquivo `.docx` do cliente vira artefato versionado no repositório. |
| **Consequências** | Qualquer mudança de layout deve ser feita no arquivo `.docx` template + re-teste de geração. |
| **Referência** | `00_docs/arquitetura.md` ADR-04 |

---

## DEC-05 — Stack Backend: Python/FastAPI

| Campo | Valor |
|---|---|
| **Data** | 2026-07-08 |
| **Status** | Aprovada |
| **Contexto** | Backend precisa integrar com WeasyPrint, docxtpl, Pillow (processamento de imagens) e Jinja2 — todas bibliotecas Python. |
| **Alternativas** | Node.js/Express (ecossistema diferente, bibliotecas PDF mais fracas), Go (sem bibliotecas PDF equivalentes) |
| **Decisão** | FastAPI (Python 3.12) com SQLAlchemy 2 async + Pydantic v2. |
| **Justificativa** | Ecossistema Python unifica geração de relatórios e API. Tipagem forte com Pydantic. OpenAPI gerado automaticamente. |
| **Consequências** | Equipe deve conhecer Python. ORM async pode ter curva de aprendizado. |
| **Referência** | `00_docs/arquitetura.md` Seção 1 |

---

## DEC-06 — Frontend: Next.js 14 + Tailwind + shadcn/ui

| Campo | Valor |
|---|---|
| **Data** | 2026-07-08 |
| **Status** | Aprovada |
| **Contexto** | Interface precisa funcionar como PWA no mobile e desktop, com formulários complexos e tabelas de dados. |
| **Alternativas** | React puro + Vite (sem SSR), Nuxt.js (ecossistema Vue), SvelteKit (menor comunidade) |
| **Decisão** | Next.js 14 App Router + Tailwind CSS + shadcn/ui. |
| **Justificativa** | Componentes shadcn/ui prontos para formulários e tabelas complexas. Next.js suporta PWA nativo. Grande ecossistema. |
| **Consequências** | App Router tem curva de aprendizado se equipe conhece Pages Router. |
| **Referência** | `00_docs/arquitetura.md` Seção 1 |

---

## DEC-07 — Banco de Dados: PostgreSQL 16

| Campo | Valor |
|---|---|
| **Data** | 2026-07-08 |
| **Status** | Aprovada |
| **Contexto** | Modelo de dados complexo com múltiplos relacionamentos (Ocorrência → Foto → Sistema → Subsistema). |
| **Alternativas** | MySQL/MariaDB (menos suporte JSONB), SQLite (sem concorrência real), MongoDB (modelo relacional se perde) |
| **Decisão** | PostgreSQL 16 com JSONB para campos flexíveis e Alembic para migrations. |
| **Justificativa** | ACID, JSONB para campos variáveis por tipo de serviço, queries complexas para dashboard, migrations versionadas. |
| **Consequências** | Requer servidor PostgreSQL no deploy. Docker Compose já inclui. |
| **Referência** | `00_docs/arquitetura.md` Seção 1 |

---

## DEC-08 — Modelo de Ciclo de Vida: Incremental por Fatia Vertical com Gestão Iterativa Leve

| Campo | Valor |
|---|---|
| **Data** | 2026-07-17 |
| **Status** | Aprovada |
| **Contexto** | Equipe pequena sem PM dedicado; 10 lacunas `[A ESCLARECER]` ainda não validadas com o cliente (bloqueio B-01, risco R-06); templates Word originais ainda não entregues (bloqueio B-02, risco R-05); necessidade de entregar valor cedo (relatório fiel ao template é o principal ganho percebido pelo cliente). |
| **Alternativas** | Cascata (exige fechar 100% dos requisitos antes de iniciar — inviável com lacunas abertas), Scrum formal completo (overhead de cerimônias desproporcional para equipe pequena), V-model (exige planos de teste e especificação formal extensos antes de codificar, baixo ganho para este porte de projeto) |
| **Decisão** | Modelo incremental por fatias verticais (uma por tipo de documento: RFO → LTIP+Dashboard → Vistoria Cautelar/Residencial/RFIP), com gestão iterativa inspirada em Scrum leve (sprints de 1-2 semanas, backlog único priorizado, sem papéis/cerimônias formais completos). Etapas de fundação técnica, validação de lacunas e obtenção de templates rodam em paralelo desde o início. |
| **Justificativa** | Permite iniciar a construção imediatamente com o que já está desbloqueado (fundação técnica, incremento RFO com template já convertido como referência), adiando apenas os itens que realmente dependem do cliente (regra RN-04, geração DOCX fiel) sem travar o cronograma nem exigir re-arquitetura quando as lacunas forem resolvidas. |
| **Consequências** | Exige disciplina para não fechar definitivamente regras dependentes de validação (ex.: RN-04) antes da Etapa 1. Templates DOCX só entram em produção após recebimento e validação do `.docx` original (Etapa 2). |
| **Referência** | `00_docs/projeto/ciclo-de-vida.md`, `00_docs/projeto/cronograma.md`, `00_docs/projeto/backlog-tarefas.md` |

---

## DEC-09 — Estrutura de pastas de topo: prefixo numérico, sem aninhamento `src/`, infra em `05_infra/`

| Campo | Valor |
|---|---|
| **Data** | 2026-07-17 |
| **Status** | Aprovada |
| **Contexto** | O repositório foi reorganizado com prefixo numérico nas pastas de topo (`00_docs/`, `01_output-context/`, `02_prototipos/`) e pastas placeholder criadas para o código futuro (`03_frontend/`, `04_backend/`, `05_infra/`). Porém `.github/agents/devops.agent.md` e `.github/prompts/12-devops.prompt.md` já descreviam uma estrutura divergente com `src/backend/`, `src/frontend/` e `infra/` (sem prefixo), e havia divergência entre prompts sobre onde colocar o `docker-compose.yml` (raiz vs. `infra/`). Isso geraria confusão para agentes e para comandos de terminal (`npm`, `npx`, `docker compose`, `alembic`, etc.) sobre em qual pasta operar. |
| **Alternativas** | (a) Manter `src/backend/`/`src/frontend/` e migrar apenas `docs`/`output-context`/`prototipos` — rejeitada por manter duas convenções diferentes no mesmo repositório; (b) `docker-compose.yml` na raiz — rejeitada por misturar artefato de orquestração com pastas de topo numeradas; (c) `infra/` sem prefixo — rejeitada por reintroduzir a inconsistência de nomenclatura que motivou a renumeração. |
| **Decisão** | Sem aninhamento `src/`. Backend em `04_backend/`, frontend em `03_frontend/`, infraestrutura (docker-compose, nginx, backups, `.env.example`) em `05_infra/` — todos na raiz do repositório, seguindo o prefixo numérico já usado nas demais pastas. `docker-compose.yml`/`docker-compose.prod.yml`/`.env.example` residem em `05_infra/`, com build context apontando para `../04_backend` e `../03_frontend`. |
| **Justificativa** | Consistência total de convenção: qualquer agente ou pessoa sabe, pela numeração, onde cada camada mora e onde rodar cada comando de terminal — `cd 05_infra && docker compose up -d` para infraestrutura, `cd 03_frontend && npm run dev`/`npx` para frontend, comandos Python/alembic a partir de `04_backend/`. Elimina ambiguidade e risco de agentes criarem pastas duplicadas (`backend/`, `frontend/`, `infra/`, `src/`) fora da convenção. |
| **Consequências** | `.github/agents/devops.agent.md`, `.github/prompts/12-devops.prompt.md`, `14-setup-ambiente-desenvolvimento.prompt.md`, `15-scaffold-backend-fastapi.prompt.md`, `16-scaffold-frontend-nextjs-pwa.prompt.md`, `17-modelagem-dados-migrations.prompt.md` e `11-projetar-sistema-predial.prompt.md` foram atualizados para refletir esta convenção. Qualquer prompt/agente futuro que gere infraestrutura ou código de aplicação deve seguir `03_frontend/`, `04_backend/`, `05_infra/` sem exceção. |
| **Referência** | `00_docs/arquitetura.md` ADR-05 e Seção 7

---

## DEC-10 — Processamento Assíncrono: Celery + Redis

| Campo | Valor |
|---|---|
| **Data** | 2026-07-17 |
| **Status** | Aprovada |
| **Contexto** | Geração de relatórios de até 200 páginas/150+ fotos não pode rodar no ciclo de requisição HTTP sem violar RNF-06 (< 60s) nem bloquear a API para outros usuários (risco R-03). |
| **Alternativas** | FastAPI `BackgroundTasks` (sem retry/backoff nativo, compete por CPU com a API), Celery + RabbitMQ (robusto, mas complexidade operacional desnecessária para o porte do projeto) |
| **Decisão** | Celery com Redis como broker e result backend. Endpoint dispara job e retorna `job_id`; frontend consulta status por polling. Idempotency key (`hash(inspecao_id + versao_alvo)`) evita geração duplicada. |
| **Justificativa** | Redis é leve, serve também como cache (gabarito e dashboard), e Celery oferece retry/backoff nativo sem exigir um broker robusto como RabbitMQ. |
| **Consequências** | Novos serviços `redis` e `celery-worker` no `docker-compose.yml`. Necessário definir política de retry e monitorar filas presas. |
| **Referência** | `00_docs/arquitetura.md` ADR-06, Seção 10.2 |

---

## DEC-11 — Padrão de Erros de API: RFC 7807 Problem Details

| Campo | Valor |
|---|---|
| **Data** | 2026-07-17 |
| **Status** | Aprovada |
| **Contexto** | Múltiplos tipos de documento e regras de validação por tipo de serviço exigem um formato de erro consistente entre backend e frontend. |
| **Alternativas** | Formato de erro ad-hoc por endpoint (inconsistente), apenas `detail` padrão do FastAPI/Pydantic (insuficiente para diferenciar erro de negócio de erro de schema) |
| **Decisão** | Adotar `application/problem+json` (RFC 7807) em todas as respostas de erro, com exception handler global convertendo `ValidationError`, `DomainError` e `NotFoundError` para esse formato. |
| **Justificativa** | Padrão de mercado, legível por humanos e máquinas; permite ao frontend implementar um único parser de erro para todos os formulários. |
| **Consequências** | Todo endpoint novo deve lançar as exceções de domínio padronizadas em vez de retornar erros ad-hoc. |
| **Referência** | `00_docs/arquitetura.md` ADR-07, Seção 10.7 |

---

## DEC-12 — Observabilidade Mínima v1: Logging Estruturado + Healthcheck

| Campo | Valor |
|---|---|
| **Data** | 2026-07-17 |
| **Status** | Aprovada |
| **Contexto** | Equipe pequena, sem orçamento definido para APM completo, mas é necessário rastrear falhas de geração de relatório (job assíncrono) e autenticação em produção. |
| **Alternativas** | Sem logging estruturado (inviável para depurar falhas assíncronas), stack completa Prometheus+Grafana+Sentry desde o v1 (overhead desproporcional) |
| **Decisão** | Logging estruturado em JSON correlacionando `request_id`/`job_id`, mais endpoints `/health` e `/health/ready`. APM completo (Sentry/Prometheus) adiado para pós v1.0. |
| **Justificativa** | Cobre a necessidade mínima de rastreabilidade sem overhead operacional desproporcional ao porte do projeto. |
| **Consequências** | Sem retenção/alerting automatizado até contratação de solução de APM. Estrutura de logging já compatível com adoção futura. |
| **Referência** | `00_docs/arquitetura.md` ADR-08, Seção 10.3 | |

---

## DEC-13 — Gabarito de Tipos de Anomalia/Falha/Localização: tabelas de domínio próprias (fora do ER original)

| Campo | Valor |
|---|---|
| **Data** | 2026-07-17 |
| **Status** | Aprovada |
| **Contexto** | BL-05 (`00_docs/projeto/backlog-tarefas.md`) exige popular o gabarito de Sistemas, Subsistemas, Tipos de Anomalia, Tipos de Falha e Localizações a partir de `00_docs/convertidos/RFO_INSPECAO.md` como "dados mestre editáveis" (RF-10), com endpoints `GET /gabarito/tipos-anomalia`, `GET /gabarito/tipos-falha` e `GET /gabarito/localizacoes` já previstos em `00_docs/arquitetura.md` Seção 4. Porém o diagrama ER da Seção 3 só modela `SistemaPredial`/`Subsistema` como tabelas — os campos `Ocorrencia.tipo_anomalia`, `Ocorrencia.tipo_falha` e `Ocorrencia.localizacao` foram deliberadamente deixados como texto livre na BL-04 (sem FK, validação de RN-04/RN-05 adiada para BL-14+). |
| **Alternativas** | (a) Enums Python/`CHECK` constraint hardcoded no banco — rejeitada por RF-10 exigir dado mestre **editável** em runtime, não fixo no schema; (b) Adicionar FK de `Ocorrencia` para essas novas tabelas já nesta tarefa — rejeitada por estar fora do escopo da BL-05 (a validação/associação de `Ocorrencia` com o gabarito é tarefa da BL-14 em diante, conforme já documentado no docstring de `app/models/ocorrencia.py`); (c) Não persistir esses gabaritos em tabela nenhuma, deixando os endpoints `/gabarito/*` recalcularem a partir do parser do markdown a cada requisição — rejeitada por acoplar a API à existência do arquivo `RFO_INSPECAO.md` em produção e não permitir edição futura do gabarito. |
| **Decisão** | Criadas 3 tabelas de domínio simples e independentes — `tipos_anomalia`, `tipos_falha`, `localizacoes` (schema idêntico ao de `SistemaPredial`: `id`, `nome` único, `ordem`) — populadas uma única vez pelo seed (`app/scripts/seed_gabarito.py`, idempotente) a partir do parser de `RFO_INSPECAO.md` (`app/scripts/rfo_gabarito_parser.py`). Nenhuma FK nova em `Ocorrencia` nesta tarefa. |
| **Justificativa** | Atende RF-10 (dado mestre editável e consultável via API) sem antecipar a modelagem de validação de `Ocorrencia` (RN-04/RN-05), que exige decisões de negócio (ex.: se o engenheiro pode sobrescrever a prioridade calculada — lacuna relacionada a BL-15) ainda não tomadas. O parser lê o markdown diretamente (em vez de valores copiados manualmente) para eliminar risco de erro de transcrição da planilha original; para os 2 Sistemas cuja aba de gabarito não reservou coluna de Subsistema (`Sistemas_Hidrossanitários`, `Vedações_verticais`), os subsistemas foram complementados a partir dos pares Sistema/Subsistema efetivamente registrados na seção `## Relatório` do mesmo arquivo (mesma fonte, sem inventar dados). |
| **Consequências** | Quando a BL-14+ modelar a validação de `Ocorrencia`, essas 3 tabelas passam a ser a fonte de valores válidos (possível adição de FK opcional `tipo_anomalia_id`/`tipo_falha_id`/`localizacao_id` mantendo os campos de texto livre atuais por compatibilidade, ou migração completa — decisão a ser tomada naquele momento). Reexecutar o seed é seguro (idempotente por `nome`) caso o `RFO_INSPECAO.md` seja atualizado. |
| **Referência** | `.github/prompts/18-seed-gabarito-sistemas-prediais.prompt.md`, `00_docs/arquitetura.md` Seção 4 |

---

## DEC-14 — Gestão de Configuração: GitHub, Trunk-Based, Conventional Commits e CI/CD via GitHub Actions

| Campo | Valor |
|---|---|
| **Data** | 2026-07-19 |
| **Status** | Aprovada |
| **Contexto** | O repositório ainda não estava inicializado com Git nem possuía pipeline de CI/CD. Era necessário definir como o código seria versionado, integrado e implantado antes do início das tarefas de codificação desbloqueadas (BL-06 em diante), para não acumular dívida de processo. |
| **Alternativas** | (a) GitFlow completo (branches `develop`/`release/*`) — rejeitado por overhead de gestão desproporcional a uma equipe de 1 engenheiro (mesmo racional de DEC-08); (b) Multi-repositório (backend/frontend/infra separados) — rejeitado por dificultar rastrear uma fatia vertical (feature que toca API + tela + infra) em um único histórico; (c) GitLab CI/Jenkins self-hosted — rejeitado por adicionar infraestrutura de CI própria sem necessidade, quando GitHub Actions já é gratuito para o volume esperado e integra nativamente com Issues/PRs. |
| **Decisão** | Monorepo único no GitHub. Branching trunk-based simplificado (`main` protegida + branches curtas `feat/*`/`fix/*`/`chore/*`/`docs/*`, squash merge via PR). Conventional Commits para mensagens. SemVer (`vMAJOR.MINOR.PATCH`) com tag apenas em `main` após deploy de produção validado. CI/CD via GitHub Actions: `ci.yml` (lint, testes, build, scan Trivy) em todo PR; `cd-staging.yml` automático a cada merge em `main`; `cd-production.yml` manual (GitHub Environments com aprovação) disparado por tag. Detalhes completos em `00_docs/projeto/plano-gestao-configuracao.md`. |
| **Justificativa** | Minimiza overhead de processo para o tamanho atual da equipe, mantém `main` sempre deployável (consistente com o modelo incremental por fatia vertical de DEC-08), e usa ferramentas já gratuitas/nativas do GitHub (Actions, Environments, GHCR, Secrets) sem introduzir infraestrutura de CI adicional. |
| **Consequências** | Exige configuração manual única de proteção de branch e GitHub Environments (não automatizável por código). Gera backlog derivado: BL-25 a BL-29 (`backlog-tarefas.md`). Enquanto a decisão de hospedagem (B-03) não for tomada, staging e produção reusam o mesmo `docker-compose.prod.yml`, variando apenas `.env` e domínio. |
| **Referência** | `00_docs/projeto/plano-gestao-configuracao.md` |

---

## DEC-15 — Autenticação (BL-06): entidade `Usuario` própria em vez de reaproveitar `Responsavel`

| Campo | Valor |
|---|---|
| **Data** | 2026-07-19 |
| **Status** | Aprovada |
| **Contexto** | RNF-05 exige login/senha para uso individual ou pequena equipe. O diagrama ER (BL-04) já tinha uma entidade `Responsavel` (fiscal de contrato, responsável legal de executora, RTE), levantada como possível candidata a reaproveitamento para autenticação (ver `.github/prompts/19-autenticacao-jwt.prompt.md`). |
| **Alternativas** | (a) Adicionar `email`/`senha_hash`/`ativo` à tabela `responsaveis` existente — rejeitada: `Responsavel` modela uma pessoa física/jurídica de referência do contrato (pode nem ter acesso ao sistema, ex.: responsável legal de uma executora terceira) e mistura dois conceitos de domínio distintos (quem é referenciado em um contrato vs. quem loga no sistema); (b) Tabela `usuarios` própria, sem vínculo obrigatório com `Responsavel`. |
| **Decisão** | Criar entidade `Usuario` nova (`app/models/usuario.py`, tabela `usuarios`: `id`, `nome`, `email` único, `senha_hash`, `ativo`), fora do diagrama ER original, dedicada exclusivamente a autenticação. Sem FK para `Responsavel` nesta tarefa — associar um `Usuario` a um `Responsavel` (quando a mesma pessoa for as duas coisas) fica para tarefa futura, se necessário. |
| **Justificativa** | Mantém `Responsavel` fiel ao seu propósito original (dado de referência do contrato, sem credenciais) e evita acoplar o modelo de autenticação a uma entidade de negócio que pode mudar por motivos não relacionados a login. Mesmo racional de separação de conceitos usado em DEC-13 (gabarito fora do ER original). |
| **Consequências** | Endpoints `/api/v1/auth/register`/`/login`/`/me` operam sobre `usuarios`, não `responsaveis`. Se no futuro for necessário que um `Responsavel` também tenha login, adicionar FK opcional `usuario_id` em `Responsavel` (não o inverso). |
| **Referência** | `00_docs/arquitetura.md` Seção 1 (linha de Autenticação), `.github/prompts/19-autenticacao-jwt.prompt.md` |

---

## DEC-16 — Endpoint adicional `POST /edificacoes/{id}/documentos` (fora da tabela original da Seção 4)

| Campo | Valor |
|---|---|
| **Data** | 2026-07-20 |
| **Status** | Aprovada |
| **Contexto** | RF-01 exige suporte a upload de documentos técnicos (projetos, ARTs) da Edificação. `00_docs/arquitetura.md` Seção 4 já modela o campo `documentos_tecnicos` (JSONB) na Edificação, mas não lista um endpoint dedicado de upload — apenas os 4 endpoints de CRUD. BL-07 (storage MinIO) já estava concluída quando esta tarefa (BL-08) foi executada. |
| **Alternativas** | (a) Exigir que o cliente envie a URL/base64 do documento dentro do próprio `POST`/`PUT /edificacoes` — rejeitada: mistura upload binário com atualização de metadados simples, dificulta paginação/validação de tamanho por arquivo; (b) Endpoint dedicado `POST /edificacoes/{id}/documentos` (multipart), reaproveitando o `StorageClient` (ADR-02/Seção 9.9) e apenas anexando metadados (`nome`, `tipo`, `storage_key`) à lista já existente em `documentos_tecnicos`. |
| **Decisão** | Adicionar `POST /api/v1/edificacoes/{id}/documentos` (multipart/form-data, campos `arquivo` + `tipo`) que faz upload via `StorageClient` e acrescenta um item a `documentos_tecnicos` (lista de objetos `{nome, tipo, storage_key}`), sem endpoint de download dedicado nesta etapa (a URL pode ser obtida via presigned URL futura, análoga ao fluxo de Fotos da BL-11). |
| **Justificativa** | Reaproveita a infraestrutura de storage já validada (BL-07) em vez de criar uma pendência nova; mantém o endpoint de CRUD (`POST`/`PUT /edificacoes`) livre de upload binário. |
| **Consequências** | Endpoint não documentado na Seção 4 original de `00_docs/arquitetura.md` — esta decisão é a referência formal. Download/gestão fina de documentos (remoção individual, URL pré-assinada) ficam para uma tarefa futura se o cliente precisar. |
| **Referência** | `.github/prompts/21-crud-edificacoes.prompt.md` |

---

## DEC-17 — Branching por serviço no monorepo: `main_front`/`main_back`/`staging_front`/`staging_back`

| Campo | Valor |
|---|---|
| **Data** | 2026-07-21 |
| **Status** | Aprovada |
| **Contexto** | Com a hospedagem definida como Render (DEC-16 de infraestrutura/BL-20) e o Blueprint (`render.yaml`) definindo serviços web independentes para backend e frontend, cada serviço do Render observa uma única branch para disparar `autoDeployTrigger: commit`. Com apenas `main`/`staging` (consolidação de 2026-07-21, ver memória de repositório), um push que só mexe em `03_frontend/` redeploya também o backend (e vice-versa), sem necessidade, e staging/produção não tinham nenhuma branch dedicada por serviço. O usuário solicitou explicitamente 4 branches: `main_front`, `main_back`, `staging_front`, `staging_back`. |
| **Alternativas** | (a) Manter só `main`/`staging` e usar path filters (`paths:` no Render Build Filters) para condicionar o deploy por pasta alterada, sem branches novas — rejeitada por não ter sido a preferência expressa do usuário e por exigir configuração adicional de "Build Filters" por serviço no Dashboard (menos explícito que a branch determinar o gatilho); (b) Dividir fisicamente o conteúdo de cada branch (só a pasta do serviço correspondente, via `git subtree`/histórico filtrado) — rejeitada por quebrar a convenção de monorepo (DEC-09) e exigir reescrever histórico, complexidade desproporcional já que o Render só precisa de um nome de branch como gatilho, não de um repositório fisicamente separado; (c) Substituir/renomear `main`/`staging` pelas 4 novas — rejeitada nesta rodada para não interromper nenhum processo que já possa depender do nome antigo (ex.: badges, links); `main`/`staging` continuam existindo, apenas sem nenhum serviço do Render apontando para elas. |
| **Decisão** | Criadas as 4 branches a partir do estado atual de `main`/`staging` (idênticos no momento da criação), com o MESMO conteúdo do monorepo em todas (nenhum histórico filtrado). Cada branch serve apenas de gatilho de deploy: `render.yaml` agora declara `branch: main_back`/`branch: main_front`/`branch: staging_back`/`branch: staging_front` em cada serviço correspondente, mais os 2 serviços de staging (`garra-backend-staging`, `garra-frontend-staging`) e um banco `garra-db-staging` isolado do de produção. `ci.yml` passou a rodar em push/PR para as 4 novas branches (mantendo `main`/`staging` durante a transição). `cd-staging.yml`/`cd-production.yml` (fluxo SSH+GHCR para VPS, nunca usado de fato após a escolha do Render) viraram fallback manual (`workflow_dispatch`), já que o deploy real passa a ser o auto-deploy nativo do Render por branch. |
| **Justificativa** | Isola o gatilho de deploy por serviço sem duplicar/filtrar o código-fonte (mantém DEC-09: um único monorepo, uma única árvore de arquivos). Usar branches dedicadas é mais simples de auditar do que Build Filters (fica visível em `git log`/PRs qual branch disparou qual deploy) e não exige nenhuma configuração adicional no Render além do campo `branch:` já suportado nativamente pelo Blueprint. |
| **Consequências** | Fluxo de trabalho passa a exigir decidir, ao abrir um PR, qual(is) branch(es)-alvo mergear (ex.: uma mudança de frontend vai para `main_front`; se também mexer no backend, precisa de PR separado ou merge nas duas). `main`/`staging` ficam "órfãs" de deploy — usadas só se o processo de PR/proteção de branch continuar centralizado nelas antes de promover para as branches de serviço (a definir na prática de trabalho do time). HT-05 (proteção de branch, `backlog-tarefas-humanas.md`) precisa ser repetido para as 4 novas branches, não só `main`. Serviços de staging em `render.yaml` são recursos pagos adicionais — avaliar custo antes de aplicar o Blueprint (ver comentário no topo do arquivo). |
| **Referência** | `render.yaml`, `.github/workflows/ci.yml`, `.github/workflows/cd-staging.yml`, `.github/workflows/cd-production.yml`, `00_docs/projeto/plano-gestao-configuracao.md` Seção 1.1 |

---

## DEC-18 — RBAC: perfis `auditor`/`cliente` e Portal do Cliente escopado via `Responsavel.usuario_id`

| Campo | Valor |
|---|---|
| **Data** | 2026-07-24 |
| **Status** | Aprovada |
| **Contexto** | O usuário do projeto esclareceu diretamente que, além do papel do "auditor" (Engenheiro Roniel/equipe), existe o papel de "cliente", cuja função no sistema é acompanhar a auditoria feita pelo auditor através de dashboards, seus documentos, entre outras coisas. Isso resolve formalmente a lacuna #6 de `00_docs/estudo-do-contexto.md` (antes `[A ESCLARECER]`) e reverte a posição de `escopo.md`, que listava "Portal de acesso para clientes" como fora de escopo. |
| **Alternativas** | (a) Multi-tenancy completo (organizações/contas separadas) — rejeitada por ser overengineering para o porte atual (uso individual/pequena equipe de auditoria, clientes apenas consultando); (b) Link público sem login (token de convite/URL secreta) — rejeitada por não permitir controle de acesso auditável (RN-14) nem histórico de quem acessou, incompatível com RNF-05; (c) Reaproveitar `Responsavel.tipo="cliente"` sem um campo `role` em `Usuario` — rejeitada por reintroduzir a mistura de conceitos que a DEC-15 deliberadamente separou. |
| **Decisão** | Adicionar `role` (enum `auditor` \| `cliente`, default `auditor`) em `Usuario`. Adicionar FK opcional e única `usuario_id` em `Responsavel` (permite login para um Responsavel do tipo contratante). Adicionar FK opcional `contratante_id` em `Contrato` referenciando `Responsavel` (hoje `Contrato` só modela `fiscal_id`; o contratante não era rastreável por FK). Dependency `require_role()` no FastAPI protege rotas por perfil. Novo router `/portal/*` (somente leitura) sempre resolve o escopo do cliente a partir de `Responsavel.usuario_id = current_user.id` — nunca aceita `edificacao_id`/`contrato_id` arbitrário vindo do cliente da requisição (RN-14). Onboarding do usuário Cliente é manual, feito pelo engenheiro fiscal (lacuna #11 de `estudo-do-contexto.md`, posição interina). |
| **Justificativa** | Mantém a separação de conceitos de DEC-15 (Usuario ≠ Responsavel), reaproveita a infraestrutura de auth já existente (BL-06) em vez de criar um sistema de contas paralelo, e centraliza a validação de escopo de acesso do cliente em um único conjunto de rotas (`/portal/*`) em vez de reabrir os endpoints internos do auditor a um segundo perfil de permissão. |
| **Consequências** | Nova migration Alembic (`role` em `usuarios`, `usuario_id` em `responsaveis`, `contratante_id` em `contratos`). Gera o backlog BL-30 (RBAC + vínculo) a BL-33 (`backlog-tarefas.md`). Endpoints existentes (`/edificacoes/{id}/dashboard`, `/relatorios/{id}/download/*`) continuam exclusivos do perfil `auditor`. |
| **Referência** | `00_docs/arquitetura.md` ADR-09, Seção 3 (Diagrama ER), Seção 4 (Portal do Cliente), Seção 10.1 (A01) |

---

## DEC-19 — Editor de Anotação de Fotos: canvas client-side (Fabric.js), sem novo endpoint de backend

| Campo | Valor |
|---|---|
| **Data** | 2026-07-24 |
| **Status** | Aprovada |
| **Contexto** | O usuário esclareceu que a função real do Lightshot no fluxo do auditor é desenhar setas, formas e marcações técnicas sobre a foto — não apenas capturar a tela — e pediu explicitamente que o próprio sistema ofereça a opção de editar/marcar a imagem, para simplificar a confecção dos relatórios sem depender exclusivamente de uma ferramenta externa sem API pública. |
| **Alternativas** | (a) Continuar dependendo 100% do Lightshot externo (RF-05 como estava) — não atende ao pedido explícito de oferecer edição dentro do sistema; (b) Editor server-side (Pillow desenhando a partir de coordenadas enviadas pelo frontend) — rejeitada por exigir novo endpoint, round-trip de coordenadas normalizadas e pior UX (sem preview interativo) que um canvas nativo do browser; (c) Canvas client-side (Fabric.js/Konva.js), achatando a imagem antes do upload. |
| **Decisão** | Fabric.js integrado ao componente de upload de fotos já existente (BL-11), com ferramentas de seta, retângulo/elipse, texto e traço livre. A imagem achatada (`canvas.toBlob()`) é o arquivo efetivamente enviado aos endpoints `POST /fotos/upload` / `/fotos/upload-clipboard` já implementados — sem mudança de schema nem endpoint novo no backend. Compatibilidade retroativa: uma imagem já marcada externamente no Lightshot pode ser colada/enviada e ainda editada/complementada no editor do sistema antes de salvar (RN-15). |
| **Justificativa** | Resolve o pedido do usuário com o menor custo de implementação possível (zero mudança de backend), reaproveitando 100% da infraestrutura de upload/storage/reprocessamento Pillow (mitigação A08) já validada na BL-11. |
| **Consequências** | Nova dependência de frontend (`fabric` via npm). Por decisão consciente (RN-15), a versão sem marcação não é retida separadamente — limitação documentada, aceitável para o v1.0; pode evoluir para reter `storage_key_original` opcional em `Foto` se necessário no futuro. |
| **Referência** | `00_docs/arquitetura.md` ADR-10, Seção 1 (Stack) |

---

## DEC-20 — Backlog de Gestão em quadro Kanban via MCP Notion (ferramenta interna do time, não parte do sistema entregável)

| Campo | Valor |
|---|---|
| **Data** | 2026-07-24 |
| **Status** | Aprovada |
| **Contexto** | O usuário pediu para integrar o servidor MCP do Notion a este workspace e montar um quadro de backlog (colunas Backlog/To do/In progress/Done, no estilo de visualização em quadro do Notion) a partir das tarefas já rastreadas em `backlog-tarefas.md`. É uma ferramenta de **gestão do projeto de desenvolvimento** (equivalente ao já feito com o board do GitHub/Trello), não uma feature do produto entregue ao cliente Garra Engenharia — não envolve dados de clientes finais, edificações, ocorrências ou fotos de vistoria. |
| **Alternativas** | (a) GitHub Projects (já há repositório no GitHub, DEC-14) — evitaria uma ferramenta nova, mas o usuário pediu explicitamente o estilo de quadro do Notion; (b) Trello/Linear via MCP — mesma limitação, não é o que foi pedido; (c) Notion MCP oficial remoto (`https://mcp.notion.com/mcp`), autenticado via OAuth 2.1 pelo próprio VS Code (mesmo padrão já usado para o MCP do GitHub em `.vscode/mcp.json`), sem chave de API digitada no chat. |
| **Decisão** | Adicionar o servidor `notion` em `.vscode/mcp.json` como servidor remoto HTTP (`https://mcp.notion.com/mcp`), autenticado via OAuth do VS Code (fluxo "Sign in", sem token colado no chat/agente). Nenhuma credencial do Notion é solicitada, digitada ou lida pelo agente. O conteúdo enviado ao Notion se limita a metadados de tarefas de backlog já públicos no próprio repositório (`backlog-tarefas.md`): ID, título, requisito/decisão relacionada e status — nenhum dado pessoal, de cliente ou de vistoria é enviado. |
| **Justificativa** | Reaproveita o mesmo padrão de integração MCP remoto já validado para GitHub (sem segredo manual) em vez de introduzir um provedor de PAT manual como foi feito para o Render (necessário porque o Render não oferece OAuth nativo no MCP). Dados enviados são de baixo risco (gestão de projeto de software, não dados de clientes/vistorias). |
| **Consequências** | Requer ação humana única: iniciar o servidor pela paleta de comandos do VS Code e autenticar via OAuth no navegador (ver HT-12 em `backlog-tarefas-humanas.md`) — só então o agente consegue de fato criar/atualizar o banco de dados no Notion. Reversível: remover a entrada `notion` de `.vscode/mcp.json` desativa a integração sem afetar o restante do sistema (feature isolada, fora do `04_backend`/`03_frontend` entregáveis). O board (`00_docs/projeto/backlog-kanban.md`) precisa ser mantido em paralelo ao `backlog-tarefas.md` até que haja automação de sincronização (fora de escopo desta decisão). |
| **Referência** | `00_docs/arquitetura.md` ADR-11, `.vscode/mcp.json`, `00_docs/projeto/backlog-kanban.md`

---

## DEC-21 — Geração assistida de legendas técnicas por IA: prompt versionado + Adapter de LLM, sempre com aprovação humana

| Campo | Valor |
|---|---|
| **Data** | 2026-07-27 |
| **Status** | Aprovada |
| **Contexto** | O cliente (Eng. Roniel) elaborou e validou um "Prompt-Sistema Universal para Transcrição e Redação de Legendas Fotográficas Técnicas", aplicável a qualquer tipo de relatório fotográfico da Garra Engenharia (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP), com regras rígidas de não invenção de dados, níveis de certeza técnica e formato de saída JSON estruturado — e pediu explicitamente que o prompt seja tratado como componente versionado, separado do código, com aprovação humana obrigatória antes de qualquer legenda compor um relatório emitido. Isso formaliza um novo requisito (RF-15) e novas regras de negócio (RN-16, RN-17) em `estudo-do-contexto.md`. |
| **Alternativas** | (a) Deixar a transcrição/redação de legendas 100% manual (fora do sistema, via chat externo com uma IA genérica) — rejeitada: perde rastreabilidade de qual prompt/versão gerou qual legenda e não integra ao fluxo de upload de fotos já existente (BL-11); (b) Persistir o prompt embutido no código da aplicação — rejeitada: impede atualização sem deploy e quebra a rastreabilidade por versão explicitamente pedida pelo cliente; (c) Enviar a legenda da IA diretamente para o campo `Foto.legenda` sem revisão — rejeitada: viola a exigência do cliente e o princípio de responsabilidade técnica do profissional habilitado (RN-07); (d) Prompt versionado em tabela própria (`prompts_ia`) + Adapter de LLM (`LegendaIAClient`) + minuta sempre revisável antes da aprovação. |
| **Decisão** | Adotar a alternativa (d): tabela `prompts_ia` (`id`, `nome`, `versao`, `conteudo`, `ativo`, `created_at`) armazena o prompt-sistema fornecido pelo cliente como artefato versionado. Novo serviço `app/services/ia_legenda/` (Adapter, mesmo padrão de `StorageClient`) abstrai o provedor de LLM. Novo endpoint `POST /fotos/{id}/legenda-ia/gerar` gera uma sugestão (nunca persistida como definitiva); `PUT /fotos/{id}` grava a legenda aprovada/editada junto com `aprovado_por_id`, `aprovado_em` e `prompt_ia_id`. Novos campos em `Foto`: `legenda_bruta`, `legenda_ia_sugerida`, `nivel_certeza_ia`, `status_validacao_ia`, `alertas_ia`, `pendencias_ia`. |
| **Justificativa** | Mantém a responsabilidade técnica do profissional habilitado (a IA produz apenas minuta), atende à exigência explícita de versionamento do cliente, e reaproveita o padrão Adapter já validado no projeto (ADR-02) para não travar a implementação a um único provedor de LLM. |
| **Consequências** | Nova migration Alembic (tabela `prompts_ia` + colunas em `fotos`). Gera o backlog BL-34 (backend) e BL-35 (frontend) em `backlog-tarefas.md`. A escolha do provedor de LLM (custo, política de retenção/privacidade dos dados enviados a terceiros) fica pendente como lacuna #13 de `estudo-do-contexto.md` — bloqueia o início de BL-34. |
| **Referência** | `00_docs/arquitetura.md` ADR-12, Seção 1 (Stack), Seção 3 (Diagrama ER), Seção 4 (API — Fotos) | |

