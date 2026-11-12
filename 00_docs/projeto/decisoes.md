---
title: Registro de Decisões — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-09-17
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
| **Status** | Aprovada (necessidade offline resolvida em 2026-09-10 por DEC-26) |
| **Contexto** | Engenheiro usa smartphone em campo para registrar ocorrências e fotos (RNF-01). |
| **Alternativas** | App nativo React Native (melhor experiência, custo 3x maior), Flutter (idem), App Nativo puro (inviável para equipe pequena) |
| **Decisão** | PWA com Next.js 14. `manifest.json` com `display: standalone`. Service Worker para cache parcial. |
| **Justificativa** | Entregue como parte do frontend sem infraestrutura adicional. Suporte a câmera via `getUserMedia` e clipboard via API browser. |
| **Consequências** | Offline completo confirmado como desnecessário pelo cliente (DEC-26): o Service Worker cacheia apenas leitura, e escritas exigem conectividade. Requer HTTPS para Clipboard API. |
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

---

## DEC-22 — Consolidação de branches de deploy: remoção de staging e sincronização automática `main` → `main_back`/`main_front`

| Campo | Valor |
|---|---|
| **Data** | 2026-08-05 |
| **Status** | Aprovada |
| **Contexto** | O usuário relatou desorganização real no fluxo de deploy: todos os commits/PRs continuavam sendo integrados só em `main`, mas o Render dispara deploy de produção a partir de `main_back`/`main_front` (DEC-17) — que ficaram até 3 commits (semanas de trabalho: RBAC/Portal do Cliente BL-30, dashboard BL-16, ocorrências BL-14, editor de anotação, template DOCX do contrato BL-40) defasadas de `main`. Além disso, `staging`/`staging_back`/`staging_front` nunca tiveram os serviços de fato provisionados no Render (bloqueado por falta de credencial, HT-04) e só geravam confusão. Havia ainda 12 PRs do Dependabot abertas contra `main`, e uma delas (`node-25-alpine`) tinha sido redirecionada manualmente para `main_front` (mudando o `base` do PR) como tentativa ad-hoc de "colocar `main_front` em dia", introduzindo conteúdo não revisado e divergência entre as branches de deploy. |
| **Alternativas** | (a) Manter o processo manual, só sincronizando `main_back`/`main_front` sob demanda quando lembrado — rejeitada: foi exatamente a causa da defasagem observada, sem garantia de repetição; (b) Abandonar `main_back`/`main_front` e apontar os serviços do Render direto para `main` — rejeitada nesta rodada por reverter a DEC-17 (isolamento de gatilho por serviço) sem necessidade, já que o problema real era falta de automação, não o desenho de branches em si; (c) Automatizar a propagação `main` → `main_back`/`main_front` via GitHub Actions a cada push, mantendo `main` como único trunk de integração. |
| **Decisão** | Adotada a alternativa (c). Novo workflow `.github/workflows/sync-deploy-branches.yml`: em todo push em `main`, faz `git merge` (nunca force-push) de `main` em `main_back` e em `main_front` e publica automaticamente — se houver conflito, abre uma issue avisando para resolução manual. `main_back`/`main_front` foram sincronizadas manualmente uma primeira vez (trazendo os 3 commits pendentes) e o workflow já validado nesta mesma sessão (merge automático confirmado em ambas). Removidas as branches `staging`, `staging_back` e `staging_front` (local e remoto) e o bloco "Staging" inteiro do `render.yaml` (2 serviços web + banco `garra-db-staging`), já que nunca chegaram a existir de fato no Render. `ci.yml` atualizado para dropar as branches de staging do trigger. Das 12 PRs abertas do Dependabot: 8 patch/minor de baixo risco foram mescladas em `main` (boto3, passlib, uvicorn, weasyprint — aplicado manualmente por conflito pontual —, pytest, radix-ui/react-dialog, actions/setup-python, docker/build-push-action); 5 majors não testados (Node 20→25, Next 14→16, ESLint 8→10, eslint-config-next, React 18→19) foram fechados sem merge — mesma decisão já tomada antes para bumps major (ver memória de repositório) — e o bump de Node 25 que havia sido indevidamente mesclado em `main_front` via PR redirecionado foi revertido para `node:20-alpine` em `03_frontend/Dockerfile` e `Dockerfile.render`, restaurando paridade com `main`. |
| **Justificativa** | Resolve a causa raiz (sincronização manual e esquecida) em vez de só corrigir o sintoma pontual, sem abrir mão do isolamento de gatilho por serviço da DEC-17. Regra única e simples para o time seguir: todo PR/commit vai para `main`; nunca commitar direto ou redirecionar PR para `main_back`/`main_front`. Remover staging elimina custo/confusão de uma feature nunca ativada, sem perda real (pode ser recriada a partir de `main` quando o ambiente for de fato necessário). |
| **Consequências** | HT-05 (`backlog-tarefas-humanas.md`, proteção de branch) passa a cobrir só 3 branches (`main`, `main_back`, `main_front`) em vez de 6. Um hotfix excepcional aplicado direto em `main_back`/`main_front` não é descartado pelo workflow (é um merge, não reset/force-push), mas precisa ser trazido de volta para `main` manualmente para não divergir de novo. Se o ambiente de staging for retomado no futuro, recriar as branches a partir de `main` e o bloco correspondente em `render.yaml` (removido, não versionado como comentário desta vez). |
| **Referência** | `render.yaml`, `.github/workflows/sync-deploy-branches.yml`, `.github/workflows/ci.yml`, DEC-17, `00_docs/projeto/plano-gestao-configuracao.md` Seção 1.1/3.1 |

---

## DEC-23 — Endpoint adicional `POST /responsaveis` + `GET /responsaveis` (fora da tabela original da Seção 4)

| Campo | Valor |
|---|---|
| **Data** | 2026-08-05 |
| **Status** | Aprovada |
| **Contexto** | Ao implementar os testes E2E dos fluxos RFO e LTIP (BL-21), ficou evidente uma falha de integração real: o formulário de Contrato (`03_frontend/app/contratos/contrato-form.tsx`) exige que o usuário digite os UUIDs de `fiscal_id`/`responsavel_legal_id`/`rte_id` de registros `Responsavel` já existentes (o próprio docstring do componente já registrava essa limitação como pendência), mas não existia nenhum endpoint de API para criar ou listar `Responsavel` — só era possível inserir esses registros diretamente no banco via fixture de teste (`tests/test_contratos.py` e outros). Sem esse endpoint, nenhum fluxo E2E ponta-a-ponta (via UI ou via chamada HTTP de setup) conseguia criar um Contrato válido. |
| **Alternativas** | (a) Deixar o teste E2E inserir `Responsavel` direto no banco via SQL/SQLAlchemy, ignorando a API — rejeitada: não testa o sistema como um usuário real o usaria, e não resolve a limitação real do formulário para uso em produção; (b) Adiar a criação de `Responsavel` para uma tarefa de UI dedicada (ex.: seletor de busca, como o próprio comentário do `contrato-form.tsx` já sugeria) — rejeitada por bloquear indefinidamente qualquer teste E2E de Contrato/RFO/LTIP; (c) Endpoint mínimo `GET /responsaveis` (lista, filtro opcional por `tipo`) + `POST /responsaveis` (cria) + `GET /responsaveis/{id}` (detalhe), reaproveitando o modelo/schema `Responsavel` que já existiam desde a BL-04 sem endpoint associado. |
| **Decisão** | Adicionados `app/api/v1/responsaveis.py` (3 endpoints acima, protegidos por `get_current_user`) e registrados em `app/main.py`. Sem paginação (volume esperado baixo — fiscais/executoras/contratantes de um único engenheiro ou pequena equipe). O teste E2E (BL-21) usa esse endpoint via chamada HTTP direta (`page.request`) como *setup* de dados de pré-requisito, e a UI de Contrato continua aceitando o UUID como texto — a melhoria de UX (seletor de busca) permanece como pendência registrada no próprio `contrato-form.tsx`, não é objeto desta decisão. |
| **Justificativa** | Mesmo racional de DEC-16 (endpoint fora da Seção 4 documentado formalmente aqui): reaproveita o modelo/schema já existentes, desbloqueia tanto os testes E2E quanto qualquer uso futuro de UI de gestão de responsáveis, sem exigir uma tela nova nesta tarefa. |
| **Consequências** | Endpoint não documentado na Seção 4 original de `00_docs/arquitetura.md` — esta decisão é a referência formal. 4 novos testes de integração em `tests/test_responsaveis.py`. Uma tela de CRUD de Responsáveis (ou um seletor de busca no formulário de Contrato) continua sendo uma melhoria futura, não implementada nesta tarefa. |
| **Referência** | `.github/prompts/29-testes-e2e-rfo-ltip.prompt.md`, `04_backend/app/api/v1/responsaveis.py`, `00_docs/arquitetura.md` Seção 4 |

---

## DEC-24 — Hardening de autenticação (BL-23): registro protegido com bootstrap explícito, rate limiting de login e configuração fail-closed

| Campo | Valor |
|---|---|
| **Data** | 2026-08-07 |
| **Status** | Aprovada |
| **Contexto** | A revisão de segurança OWASP Top 10 (BL-23) encontrou três falhas reais e exploráveis no backend: (1) `POST /api/v1/auth/register` era **público** — qualquer pessoa com a URL da API criava uma conta `auditor` com acesso total de escrita a todos os contratos/edificações/relatórios (A01), apesar de o docstring do endpoint afirmar "uso interno da equipe, sem cadastro público"; (2) não havia nenhum limite de tentativas em `POST /auth/login`, permitindo força bruta ilimitada (A07), mesmo com a mitigação já prevista em `arquitetura.md` Seção 10.1; (3) `Settings.jwt_secret_key` tinha default `"changeme"` e `/docs`/`/redoc`/`/openapi.json` eram montados em qualquer ambiente (A05) — subir produção sem preencher a variável assinaria tokens forjáveis por qualquer um que lesse o repositório. |
| **Alternativas** | (a) Manter `/register` público e apenas monitorar — rejeitada: é escalonamento de privilégio direto, não um risco teórico; (b) Remover `/register` e criar usuários só por script/psql — rejeitada: inviabiliza o onboarding manual do usuário Cliente previsto em DEC-18 e quebra os testes E2E, que precisam criar usuários isolados por execução; (c) Exigir autenticação de `auditor` em `/register`, com exceção de bootstrap quando a tabela `usuarios` está vazia + script idempotente `seed_admin` para formalizar o primeiro usuário; rate limiting em memória contando apenas falhas por (IP, e-mail); e validação fail-closed em `Settings` que impede o boot em produção com segredo default ou CORS `*`. |
| **Decisão** | Adotada a alternativa (c). `POST /auth/register` exige `auditor` autenticado (`get_optional_user`, dependency nova em `app/api/deps.py`) salvo no bootstrap; `UsuarioCreate` passou a aceitar `role` (`auditor`\|`cliente`), viabilizando o onboarding do Cliente (DEC-18) como operação privilegiada. `app/core/rate_limit.py`: 5 tentativas malsucedidas por (IP, e-mail) em janela de 15 min, zeradas por login bem-sucedido, resposta `429` com `Retry-After`. `app/core/middleware.py`: `SecurityHeadersMiddleware` (nosniff, `X-Frame-Options`, CSP, HSTS fora de dev) e `RequestIdMiddleware` (`X-Request-ID`, cumprindo a correlação prevista em ADR-08/DEC-12 e nunca implementada). `Settings` recusa iniciar fora de desenvolvimento com `JWT_SECRET_KEY` vazia/default/curta ou CORS `*`. Script `app/scripts/seed_admin.py` (idempotente, credenciais por variável de ambiente) cobre o bootstrap em produção e no CI. |
| **Justificativa** | Fecha escalonamento de privilégio e força bruta sem introduzir infraestrutura nova (nenhum Redis/WAF exigido nesta fase) e sem quebrar o fluxo legítimo: o bootstrap mantém a instalação inicial possível, e o contador só pune falhas. A validação fail-closed em `Settings` transforma um erro silencioso de configuração (produção com segredo default) em falha no boot, detectada no deploy e não em um incidente. |
| **Consequências** | `POST /auth/register` deixa de funcionar sem token — `03_frontend/e2e/helpers.ts` passou a logar com o admin de bootstrap antes de criar o usuário do teste, e o job `e2e` do `ci.yml` executa `python -m app.scripts.seed_admin` junto com o seed do gabarito. Em produção no Render, `ENVIRONMENT=production` sem `JWT_SECRET_KEY` forte impede o serviço de subir — reforça a pendência já registrada em HT-04. O rate limiting vive no processo: com múltiplas réplicas, migrar para o Redis de ADR-06/DEC-10 (interface pública do módulo não muda). Riscos residuais aceitos e documentados em `revisao-seguranca-owasp.md`: ausência de isolamento entre auditores (depende da lacuna #2), bumps major pendentes (DEC-22) e ausência de refresh token/revogação na v1.0. |
| **Referência** | `00_docs/projeto/revisao-seguranca-owasp.md`, `00_docs/arquitetura.md` Seção 10.1, `.github/prompts/31-revisao-seguranca-owasp.prompt.md` |

---

## DEC-25 — Templates de relatório derivados dos originais `.xlsx`/`.xlsm`/PDF já disponíveis (revisão do bloqueio B-02)

| Campo | Valor |
|---|---|
| **Data** | 2026-08-12 |
| **Status** | Aprovada |
| **Contexto** | O bloqueio B-02 foi registrado sob a premissa de que "só existem as versões `.md` convertidas" dos 5 modelos de documento, e que o projeto dependia de o cliente entregar arquivos `.docx`. Um inventário do diretório `01_output-context/` (2026-08-12) mostra que essa premissa está **errada**: os originais estão disponíveis desde o início, apenas em outros formatos — `RFO INSPEÇÃO .xlsx` (77,9 MB) e `Relatório de Fiscalização 1.xlsm` (17,5 MB) para o RFO; `Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx` (479,3 MB) para o RFIP; e PDFs finais de alta fidelidade para o LTIP (32,5 MB), a Vistoria Cautelar (38,5 MB) e a Vistoria Residencial (21,5 MB). O `.docx` nunca chegou porque o cliente **não produz esses documentos em Word** — RFO e RFIP nascem em planilha e os laudos circulam como PDF. O `.xlsx` do RFO, aliás, já é a fonte de verdade estrutural do gabarito de sistemas prediais (BL-05/DEC-13, via a conversão `RFO_INSPECAO.md`). |
| **Alternativas** | (a) Manter a espera pelo `.docx` do cliente — rejeitada: o artefato não existe do lado do cliente, a espera é indefinida e mantém BL-12/BL-13/BL-17 paradas sem contrapartida; (b) Adotar a planilha como formato de saída do sistema (openpyxl escrevendo sobre o `.xlsx` original como template) — rejeitada como formato primário da v1.0: RF-06 exige PDF e DOCX editável, o `.xlsm` carrega macros VBA (superfície de execução indesejada, OWASP A08) e os arquivos chegam a centenas de MB; (c) Construir os templates DOCX/HTML internamente, por script determinístico, a partir dos originais já disponíveis, validando por comparação visual contra o próprio original. |
| **Decisão** | Adotada a alternativa (c), com dois pipelines de extração conforme o formato de origem. **Origem planilha (RFO, RFIP):** `openpyxl` lê o original em modo somente leitura e extrai a especificação de layout — área de impressão, cabeçalho/rodapé, ordem e largura de colunas, células mescladas, estilos de fonte e imagens ancoradas. **Origem PDF (LTIP, Vistoria Cautelar, Vistoria Residencial):** extração de métricas tipográficas (família e corpo de fonte, margens, cores, posição da logo e da numeração de páginas) com `pypdf`/`pdfplumber`. Os dois caminhos alimentam um mesmo artefato intermediário versionado — `04_backend/templates/<tipo>/layout.json` — a partir do qual são gerados o `.docx` (docxtpl, DEC-04) e o `.html.j2` (WeasyPrint, DEC-01), seguindo o mesmo padrão de script determinístico já validado em BL-40 (`build_contract_template_docx.py`). Um `.docx` eventualmente entregue pelo cliente passa a ser insumo **opcional** de refinamento, nunca pré-requisito. |
| **Justificativa** | Remove uma dependência externa que não tinha como ser satisfeita e substitui a referência de fidelidade pelo artefato mais fiel disponível: a planilha viva (RFO/RFIP) e o PDF final (laudos) preservam fonte, margem, cabeçalho e estilo reais — informação que o `.md` convertido perde por completo. Também dá a HT-09 uma linha de base objetiva de comparação. Manter `layout.json` como camada intermediária evita reextrair o original (pesado e fora do Git) a cada ajuste de template e mantém PDF e DOCX derivados da mesma especificação, sem divergirem entre si. |
| **Consequências** | **B-02 deixa de ser bloqueio de engenharia:** BL-12, BL-13 e BL-17 são desbloqueadas; HT-02 fica reduzida à obtenção da logo vetorial/transparente (RN-07) e à confirmação de que os arquivos em `01_output-context/` são a versão vigente. Os originais permanecem fora do Git (`.gitignore`) — apenas `layout.json` e os templates gerados são versionados, e os scripts de extração devem receber o caminho do original por parâmetro/variável de ambiente, sem assumir presença no repositório. O `.xlsm` **nunca deve ser executado**: leitura apenas via `openpyxl` sem carregar VBA (OWASP A08). O RFIP de 479 MB exige leitura em modo streaming/`read_only` para não estourar memória. Fica um ponto em aberto para o cliente, que **não bloqueia** a v1.0: se o fluxo de trabalho real permanece em Excel, avaliar a exportação `.xlsx` como formato adicional de saída na v1.1. |
| **Referência** | `00_docs/arquitetura.md` ADR-13, `00_docs/projeto/status.md` (B-02), `00_docs/projeto/backlog-tarefas-humanas.md` (HT-02), DEC-01, DEC-04, DEC-13 |

---

## DEC-26 — Operação offline completa fora do escopo da v1.0 (PWA online-first)

| Campo | Valor |
|---|---|
| **Data** | 2026-09-10 |
| **Status** | Aprovada |
| **Contexto** | Resposta do cliente ao Bloco 1 da sessão de validação de lacunas (HT-01/BL-18, ver `ata-validacao-lacunas.md`): a lacuna #3 de `estudo-do-contexto.md` foi respondida com a opção **(a) — não há necessidade de operação offline**, porque as edificações inspecionadas têm cobertura 4G ou Wi-Fi disponível durante a vistoria. Até aqui a Seção 10.8 de `arquitetura.md` sustentava apenas uma "posição provisória" online-first, e o risco R-07 (`riscos.md`) tratava a descoberta tardia desse requisito como risco de prioridade alta sobre toda a arquitetura do frontend. |
| **Alternativas** | (a) Implementar offline completo preventivamente (Service Worker de escrita + IndexedDB + fila de sincronização com resolução de conflito) — rejeitada: custo alto e complexidade de conflito de dados para um requisito que o cliente declarou inexistente; (b) Implementar uma fila de escrita mínima "por garantia" — rejeitada: mesma classe de complexidade (idempotência de upload de foto, ordenação de eventos, reconciliação), sem demanda real; (c) Confirmar a posição online-first como decisão definitiva da v1.0, mantendo apenas o cache de leitura já previsto na PWA. |
| **Decisão** | Adotada a alternativa (c). A operação offline completa fica **formalmente fora do escopo da v1.0**. O Service Worker da PWA (ADR-03) continua cacheando somente dados de leitura de baixa volatilidade (gabarito de sistemas prediais, contratos em andamento); operações de escrita (visita, ocorrência, foto) exigem conectividade e falham com erro explícito ao usuário, sem fila local. RNF-02 deixa de ser `[A ESCLARECER]` e passa a ser um requisito fechado nesses termos. |
| **Justificativa** | Remove a maior incerteza arquitetural do frontend sem custo de implementação: a alternativa offline afetaria modelo de dados (IDs gerados no cliente), upload de fotos (idempotência), autenticação (token expirado offline) e a UX inteira de erro. Confirmado pelo próprio usuário do sistema, que é quem opera em campo. |
| **Consequências** | Risco **R-07 encerrado** (`riscos.md`). `escopo.md` deixa de marcar "Suporte offline completo" como `[A ESCLARECER]` e passa a listá-lo como fora de escopo por decisão do cliente. A Seção 10.8 de `arquitetura.md` deixa de ser "posição provisória". Se a necessidade surgir no futuro (ex.: obra em área sem cobertura), continua valendo o encaminhamento original: incremento arquitetural dedicado, com replanejamento de escopo e cronograma — nunca incorporado retroativamente. A premissa 4 de `escopo.md` ("o engenheiro tem acesso a internet durante o uso") passa de premissa a fato confirmado. |
| **Referência** | `00_docs/arquitetura.md` ADR-15, ADR-03 e Seção 10.8, `00_docs/estudo-do-contexto.md` RNF-02 e lacuna #3, `00_docs/projeto/riscos.md` R-07, `00_docs/projeto/ata-validacao-lacunas.md` |

---

## DEC-27 — RBAC: terceiro perfil `auxiliar` com escrita limitada e autoria rastreável

| Campo | Valor |
|---|---|
| **Data** | 2026-09-10 |
| **Status** | Aprovada |
| **Contexto** | Resposta do cliente ao Bloco 1 da sessão de validação de lacunas: a lacuna #2 de `estudo-do-contexto.md` foi respondida com a opção **(b) — o engenheiro não trabalha sozinho**; há auxiliares que também registram ocorrências e fotos em campo. O RBAC implementado em DEC-18/BL-30 só prevê `auditor` (escrita total) e `cliente` (leitura escopada), o que obrigaria os auxiliares a compartilhar uma credencial `auditor` — exatamente o cenário que a revisão OWASP (BL-23/DEC-24) já havia registrado como risco residual aceito "dependente da lacuna #2". |
| **Alternativas** | (a) Manter só `auditor` e dar essa credencial aos auxiliares — rejeitada: escalonamento de privilégio de fato (o auxiliar poderia emitir relatório em nome do responsável técnico e cadastrar usuários, OWASP A01) e perda de rastreabilidade de autoria; (b) Multi-tenancy/segregação por equipe com hierarquia de gestores — rejeitada pelo mesmo motivo de DEC-18: overengineering para o porte atual (um responsável técnico e poucos auxiliares); (c) Terceiro valor no enum `Usuario.role` já existente, com uma dependency de autorização por operação e registro de autoria nos registros criados. |
| **Decisão** | Adotada a alternativa (c). `Usuario.role` passa a aceitar `auditor` \| `auxiliar` \| `cliente`. O perfil `auxiliar` **pode**: criar/editar visitas, ocorrências e fotos (incluindo upload e anotação) dos contratos em que atua. O perfil `auxiliar` **não pode**: gerar ou emitir relatórios (`/relatorios/*`), criar/editar contratos, edificações e responsáveis, cadastrar usuários (`POST /auth/register`) nem acessar rotas do Portal do Cliente. Os registros de domínio criados em campo passam a gravar o autor (`criado_por_id` → `Usuario`), preservando a responsabilidade técnica: a autoria do laudo continua sendo do `auditor` que o emite, e o auxiliar aparece como quem coletou o dado. |
| **Justificativa** | Reaproveita integralmente a infraestrutura de RBAC já entregue em BL-30 (`Usuario.role` + `require_role()`), sem sistema de permissões novo. Fecha o risco residual de A01 registrado em `revisao-seguranca-owasp.md` e mantém intacto o princípio de que só o profissional habilitado emite documento técnico (RN-07). |
| **Consequências** | Gera **BL-42** em `backlog-tarefas.md`: migration Alembic (coluna `criado_por_id` em `visitas`, `ocorrencias` e `fotos`; sem mudança de tipo em `usuarios.role`, que já é `String`), ajuste de `require_role()` nos routers de escrita, `UsuarioCreate.role` passa a aceitar o novo valor e testes de autorização por perfil. O onboarding do auxiliar segue o mesmo fluxo manual do Cliente (auditor autenticado chamando `POST /auth/register`, DEC-24). O frontend precisa esconder as ações não permitidas — mas a autorização real é sempre validada no backend, nunca só na UI. Enquanto BL-42 não for implementada, auxiliares continuam sem credencial própria. |
| **Referência** | `00_docs/arquitetura.md` ADR-14 e Seção 10.1 (A01), DEC-18, DEC-24, `00_docs/projeto/revisao-seguranca-owasp.md`, `00_docs/estudo-do-contexto.md` RN-14 e lacuna #2 |

---

## DEC-28 — Assinatura dos PDFs emitidos: CREA/ART impressos, sem ICP-Brasil na v1.0

| Campo | Valor |
|---|---|
| **Data** | 2026-09-10 |
| **Status** | Aprovada |
| **Contexto** | Resposta do cliente ao Bloco 1 da sessão de validação de lacunas: a lacuna #9 de `estudo-do-contexto.md` foi respondida com a opção **(a) — basta o CREA impresso**. A responsabilidade técnica dos laudos e relatórios é registrada pelo número do CREA do engenheiro fiscal e pela ART correspondente, impressos no corpo do documento (RN-07/RN-09); nenhum contratante atual exige assinatura digital ICP-Brasil nos documentos entregues. |
| **Alternativas** | (a) Implementar assinatura PDF/PKCS#7 com certificado ICP-Brasil (e-CPF A3/A1) — rejeitada: exige compra e custódia de certificado (HT-08), biblioteca de assinatura, gestão de PIN/HSM e um fluxo de emissão distinto, sem demanda do cliente; (b) Assinatura eletrônica simples (imagem de assinatura digitalizada aplicada ao PDF) — não decidida agora: é mudança de template, não de arquitetura, e pode ser tratada como ajuste de layout se o cliente pedir; (c) Manter o documento como está hoje, com CREA e ART impressos. |
| **Decisão** | Adotada a alternativa (c). Nenhum módulo de assinatura digital entra na v1.0. Os templates continuam imprimindo CREA, ART e o bloco de assinaturas já presente nos originais (`RESPONSÁVEL TÉCNICO/FISCALIZAÇÃO`, `CONTRATADA`, `CONTRATANTE` — ver ADR-13/BL-12). |
| **Justificativa** | Preserva o comportamento atual dos documentos que o cliente já entrega e evita introduzir custódia de material criptográfico pessoal (e-CPF) na aplicação, que traria obrigações de segurança desproporcionais ao ganho. |
| **Consequências** | **HT-08** (obtenção do certificado ICP-Brasil) fica sem efeito para a v1.0 em `backlog-tarefas-humanas.md`. `escopo.md` deixa de marcar "Módulo de assinatura digital ICP-Brasil" como `[A ESCLARECER]` e passa a listá-lo como fora de escopo por decisão do cliente. Se um contratante futuro exigir ICP-Brasil, isso volta como incremento próprio (biblioteca de assinatura + custódia do certificado + revisão de fluxo de emissão), não como ajuste de template. |
| **Referência** | `00_docs/estudo-do-contexto.md` RN-07, RN-09 e lacuna #9, `00_docs/projeto/escopo.md`, `00_docs/projeto/backlog-tarefas-humanas.md` (HT-08) |

---

## DEC-29 — Fechamento das lacunas remanescentes (Blocos 2 e 3): encerramento do bloqueio B-01

| Campo | Valor |
|---|---|
| **Data** | 2026-09-17 |
| **Status** | Aprovada |
| **Contexto** | Após o Bloco 1 (DEC-26/27/28), o bloqueio **B-01** seguia aberto por seis lacunas de `estudo-do-contexto.md` §9 — #1, #4, #5, #7, #8 e #10 — todas de escopo localizado (regra de negócio ou formato de campo), sem impacto arquitetural. A #10 era a única que ainda prendia uma tarefa de engenharia (BL-15/RN-04). O gestor do projeto declarou o ponto encerrado em 2026-09-17 e determinou o desbloqueio, cabendo a esta decisão registrar formalmente a posição adotada para cada lacuna. Todas as opções escolhidas são as de **menor impacto sobre o que já foi entregue** — nenhuma delas exige refazer código existente. |
| **Alternativas** | Para cada lacuna, as alternativas apresentadas ao cliente estão em [pauta-validacao-lacunas.md](pauta-validacao-lacunas.md) (Blocos 2 e 3). A alternativa global rejeitada foi manter B-01 aberto até uma nova sessão com o cliente — descartada porque as seis lacunas não alteram arquitetura e o custo de manter a incerteza (BL-15 parada, RN-04 sem enforcement) já era maior que o de fixar uma posição revisável. |
| **Decisão** | Posição adotada por lacuna: **#10 — opção (b)**: a Prioridade é **sugerida automaticamente** a partir do Grau de Risco CMM (Crítico = 5, Médio = 3, Mínimo = 1) e permanece **editável** pelo engenheiro responsável, com registro de quem alterou e do valor sugerido original; "Prioridade 0" significa **"não aplicável"** (ocorrência Conforme ou sistema registrado como "Não se Aplica" por RN-10), nunca "não preenchido". **#1 — opção (a)**: não há periodicidade obrigatória de re-inspeção; o prazo de retorno é recomendação técnica escrita pelo engenheiro no corpo do laudo, caso a caso. **#8 — opção (b)**: a unidade da medição do RFO é **livre por item** (m², unidade, hora, verba), como o modelo `VisitaMedicao.unidade` já suporta. **#5 — opção (a)**: o DOCX continua **obrigatório** como rascunho editável antes da entrega; RNF-04 permanece inalterado. **#4 — opção (b)**: as fotos entram por **clipboard/upload manual**, com a marcação feita no editor interno (RF-14/BL-31); não haverá monitoramento de pasta. **#7 — opção (a)**: **sem integração com o CREA** — os números de CREA/ART são digitados manualmente. |
| **Justificativa** | (#10) É a única resposta compatível com a prática pericial: o Grau de Risco CMM classifica a anomalia, mas a priorização da intervenção depende de contexto (uso da edificação, custo, risco a terceiros) que só o responsável técnico avalia — automatizar sem escape tornaria o sistema um obstáculo. O registro do ajuste preserva a rastreabilidade exigida pela responsabilidade técnica (RN-07). (#1) Nem a NBR 16747 nem a IBAPE-NA fixam prazo obrigatório de retorno por grau de risco; criar calendário/alertas seria inventar requisito. (#8) O modelo já armazena `unidade` como texto livre e RF-03 já cita "m², unidades" — fixar m² seria uma regressão. (#5) RNF-04, BL-13 e o `rfo_template.docx` já entregues assumem o DOCX; removê-lo descartaria trabalho concluído sem ganho. (#4) BL-31 (editor de anotação interno) já cobre o caso de uso real do Lightshot; um agente desktop adicionaria um artefato instalável fora do escopo de uma PWA. (#7) Não há API pública estável do CREA para consulta de ART; a digitação manual é o comportamento atual do cliente. |
| **Consequências** | **B-01 encerrado.** **BL-15 desbloqueada** (🔴 → 🟢) com escopo definido: derivar a Prioridade do Grau de Risco no momento da criação da Ocorrência, permitir sobrescrita explícita e persistir a autoria do ajuste (campos novos em `ocorrencias`, migration Alembic + ajuste de `ocorrencia_service._validar_payload`, que hoje só valida o intervalo 0-5). **BL-18 e HT-01 concluídas.** Risco **R-06 encerrado**. RN-04 e RN-13 deixam de ser `[A ESCLARECER]` em `estudo-do-contexto.md`; a Seção 6 de `arquitetura.md` deixa de listar o agente desktop de monitoramento de pasta como hipótese em aberto; `escopo.md` passa a listar "Integração API com CREA" e "Monitoramento automático de pasta de fotos" como fora de escopo por decisão, não por indefinição. Permanecem abertos apenas **B-04** (provedor de LLM, lacuna #13) e o destino externo do backup (RNF-08) — nenhum dos dois faz parte de B-01. Qualquer uma destas posições pode ser revista pelo cliente; como nenhuma delas cria estrutura nova além dos campos de auditoria de BL-15, a reversão é barata. |
| **Referência** | `00_docs/projeto/pauta-validacao-lacunas.md` (Blocos 2 e 3), `00_docs/projeto/ata-validacao-lacunas.md`, `00_docs/estudo-do-contexto.md` RN-04, RN-13, RF-03 e §9, `00_docs/projeto/riscos.md` R-06, DEC-26, DEC-27, DEC-28 |

## DEC-30 — Marca vetorizada internamente a partir do JPEG oficial: encerramento do bloqueio B-02

| Campo | Valor |
|---|---|
| **Data** | 2026-09-17 |
| **Status** | Aprovada |
| **Contexto** | Desde DEC-25/ADR-13, o bloqueio **B-02** estava reduzido a um único item: a marca só existe em 4 JPEGs (`03_frontend/public/brand/logos/`), todos com fundo chapado embutido no arquivo (creme, preto ou ardósia). O cabeçalho dos relatórios (RN-07) usava `templates/assets/logo-garra.jpg` — ou seja, um retângulo creme impresso sobre o papel branco, com serrilhado de compressão em qualquer escala. A entrega do vetor (`.svg`/`.ai`) dependia de HT-02, que depende do cliente, que por sua vez pode não ter o arquivo (o mesmo padrão que já tinha criado a premissa falsa de B-02 original). |
| **Alternativas** | (a) **Continuar aguardando o vetor do cliente** — rejeitada pelo mesmo racional de ADR-13: mantém um bloqueio aberto por um artefato que pode não existir na origem, sem contrapartida técnica; (b) **Só remover o fundo do JPEG (PNG transparente)** — resolve o retângulo creme, mas continua raster: perde nitidez em qualquer ampliação e não serve para PWA/favicon; (c) **Redesenhar a marca à mão em SVG** — foi o que BL-41 fez para o ícone da PWA (skyline simplificado): rápido, porém é uma interpretação, não a marca do cliente; (d) **Vetorizar o JPEG oficial por script determinístico**, versionando o SVG resultante. |
| **Decisão** | Adotada a alternativa (d), com (b) como subproduto para o DOCX. Novo `app/scripts/bitmap_tracer.py` (rastreamento de contornos + Douglas-Peucker + emissão do caminho SVG) e `app/scripts/build_brand_assets.py` (CLI), que produzem a partir de `logo-principal-fundo-claro.jpg`: `logo-garra.svg` (2 tons, fundo transparente), `logo-garra-negativa.svg` (branca, para fundo escuro), `logo-garra-simbolo.svg` (só o skyline), `logo-garra.png` (transparente, para o DOCX, que não aceita SVG) e `marca.json` (procedência: sha256 do original, recorte, paleta e tolerância). O `rfo_pipeline` passa a embutir o SVG no HTML/PDF; os templates DOCX de RFO e LTIP passam a embutir o PNG. `templates/assets/logo-garra.jpg` foi removido. |
| **Justificativa** | A vetorização é reprodutível a partir do repositório (script + hash do original registrado), não uma conversão manual num editor gráfico — mesmo princípio de ADR-13 para o layout dos templates. Nenhuma dependência nova: o tracer usa só Pillow, já exigido pelo backend (as bibliotecas prontas de vetorização testadas quebram em processo junto do Pillow neste ambiente). Como o resultado é derivado da marca oficial, e não um redesenho, um `.ai`/`.svg` que o cliente venha a enviar continua sendo insumo **opcional** de refinamento: basta substituir os arquivos gerados. |
| **Consequências** | **B-02 encerrado.** HT-02 fica reduzida à confirmação da versão vigente dos originais (item de gestão, sem impacto de engenharia) e BL-19 deixa de citar a logo como pendência. O cabeçalho do PDF e do DOCX passa a sair com a marca em fundo transparente — validado na amostra de HT-09 regerada nesta data. Os assets gerados são versionados; quando a marca mudar, reexecutar `python -m app.scripts.build_brand_assets` em vez de editar os arquivos à mão (os SVGs trazem cabeçalho "ARQUIVO GERADO"). O ícone da PWA (`03_frontend/public/icon.svg`, BL-41) segue sendo o símbolo simplificado, por legibilidade em 16-32 px — decisão de design mantida, não mais uma consequência da falta de vetor. |
| **Referência** | `04_backend/app/scripts/build_brand_assets.py`, `04_backend/app/scripts/bitmap_tracer.py`, `04_backend/templates/assets/`, `04_backend/tests/test_brand_assets.py`, `00_docs/arquitetura.md` ADR-16, DEC-25/ADR-13, RN-07 |


## DEC-31 — Ambiente de desenvolvimento reproduzível (T01, T02, T04)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Parcialmente implementada (T02 e T04 concluídas); aguarda aprovação formal do dono e o ajuste do `ci.yml` |
| **Contexto** | O diagnóstico T01 ([diagnostico.md](../backlog-auto/diagnostico.md)) mostrou que `pytest` não coletava com pytest 9.2.0 + pytest-asyncio 0.23.3, que `ruff check .` retornava 214 achados sem configuração versionada (o resultado vinha de um `pyproject.toml` fora do repositório) e que o ambiente exige Python 3.12 e Docker. |
| **Decisão** | (1) **Testes:** `04_backend/requirements.txt` fixa `pytest>=9.1.1,<10.0` e `pytest-asyncio>=1.4.1,<1.5`; o 0.23.x é incompatível com o pytest 9 (`'Package' object has no attribute 'obj'`) e não deve voltar. Ao atualizar qualquer um dos dois, validar com `python -m pytest --collect-only -q`. Resultado da T02: 139 testes coletados. (2) **Lint:** configuração versionada em `04_backend/ruff.toml` (`E, F, I, B, UP, RUF`, ignora só `E501`, linha 100, py312); B008 tratado com `extend-immutable-calls` para `fastapi.Depends/Query/...`; os 38 F821 eram falsos positivos de anotações em string do SQLAlchemy, resolvidos com `TYPE_CHECKING`. Resultado da T04: `ruff check .` de 214 para 0 erros, sem mudança em `upgrade()`/`downgrade()` das migrations. |
| **Pendente** | Em `.github/workflows/ci.yml`: remover `continue-on-error: true` do passo "Lint (ruff)" e fixar a versão (`ruff==0.17.3`); é arquivo `.yml`, fora do escopo de um lote só de documentação, então fica para tarefa de código. Rodar a suíte de integração (`alembic upgrade head` + `pytest`) com a stack de `05_infra` no ar: nas duas tarefas ela não pôde ser verificada (sem Docker/schema). |
| **Consequências** | Altera `requirements.txt`, `ruff.toml` e dezenas de arquivos `.py` (imports, anotações), sem mudança de comportamento declarada. Risco associado: R-11. |
| **Referência** | `00_docs/backlog-auto/pytest-compat.md`, `00_docs/backlog-auto/ruff.md`, `00_docs/backlog-auto/diagnostico.md`, `04_backend/requirements.txt`, `04_backend/ruff.toml`, `.github/workflows/ci.yml` |

## DEC-32 — Tratamento das vulnerabilidades do frontend (proposta de T03)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | `npm audit` em `03_frontend`: 30 pacotes (2 críticos, 11 altos, 17 moderados); em produção (`--omit=dev`), 13 pacotes. O risco real concentra-se no `next` 14.2.35 (crítico, em runtime, sem correção em 14.x); `fabric` 6.9.1 e a cadeia `canvas`/`tar` têm exposição baixa/média. Ver [npm-audit.md](../backlog-auto/npm-audit.md). |
| **Alternativas** | (a) só `npm audit fix` sem `--force`; (b) upgrade do Next para 15.5.28+ ou 16.x (provável React 19) e do fabric para 7.4.0; (c) `npm audit fix --force` (descartada: propõe downgrades inválidos de eslint e eslint-config-next). |
| **Decisão proposta** | (1) Rodar `npm audit fix` sem `--force` nos 5 pacotes sem major (brace-expansion, js-yaml, nanoid, postcss-selector-parser, source-map-js). (2) Tratar o upgrade do Next como prioridade antes do próximo deploy de produção, em tarefa própria. (3) Fabric 7 junto ou depois, com teste do editor de fotos (RF-14). (4) Nunca usar `--force`. (5) Opcional: gate de CI com `npm audit --omit=dev --audit-level=critical`. |
| **Consequências** | A T03 não alterou nenhum arquivo do frontend (só análise). Os upgrades majors exigem teste de todas as rotas e do editor de anotação. Risco associado: R-12. | **Atualização (T07, 2026-11-04):** o item 1 foi aplicado (`package-lock.json`, 19 pacotes, sem major): achados 30 → 26, produção 13 → 10. Exceção: a cópia `brace-expansion` 1.1.16 permanece (eslint 8 e cadeia fabric 6 → canvas) até os itens 2–4. Ver [npm-audit-fix.md](../backlog-auto/npm-audit-fix.md).
| **Referência** | `00_docs/backlog-auto/npm-audit.md`, `03_frontend/package.json`, `03_frontend/Dockerfile.render` |

## DEC-33 — Pontuação GUT calculada no pipeline do LTIP e campos vazios como "—" (proposta de T05)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda confirmação do cliente) |
| **Contexto** | O `ltip_pipeline.py` precisa imprimir a pontuação GUT na ficha da ocorrência, mas ela não é persistida e `estudo-do-contexto.md` não define a fórmula (RN-04 trata só da prioridade). O template DOCX não tem fallback e imprimiria `None` em campo vazio. |
| **Decisão proposta** | (1) `pontuacao_gut` = G×U×T quando as três notas existem, calculada no pipeline. (2) Campo vazio ou `None` aparece como `—` no HTML e no DOCX; `prioridade = 0` (não aplicável) é preservada. |
| **Consequências** | Se o cliente adotar outra fórmula, só o pipeline muda. |
| **Referência** | `00_docs/backlog-auto/ltip-pipeline.md`, `04_backend/app/services/report_generator/ltip_pipeline.py` |

## DEC-34 — Correção das lacunas de validação de Ocorrências (proposta de T06)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono). Correções L1–L7 **aplicadas no código pela T08** em 2026-11-04, mas sem os testes executados (sem PostgreSQL); P1–P4 seguem sem decisão |
| **Contexto** | A revisão de BL-14 ([revisao-regras-ocorrencias.md](revisao-regras-ocorrencias.md)) achou 7 lacunas no backend: L1/L2 situação e classificação aceitam qualquer texto; L3/L4/L5 sistema, subsistema (e coerência com o sistema) e inspeção não são verificados, e o erro vira 500; L6 `PUT` sobrescreve `inspecao_id` e `seq_numero`; L7 filtro `sistema_id` inválido vira 500. |
| **Decisão proposta** | Aplicar a correção mínima no service, repositório e endpoint: validar enums com `DomainError`, checar existência e coerência com `NotFoundError`/`DomainError` (422), excluir `inspecao_id`/`seq_numero` do `PUT` e tipar `sistema_id` como UUID. Decidir ainda: P1 (restringir ocorrência a Inspeção LTIP/Vistoria), P2 (auxiliar pode excluir?), P3 (enums persistidos no banco exigem migration) e P4 (autoria de `prioridade_ajustada_*` regravada a cada `PUT`). |
| **Consequências** | Os testes `test_lacuna_*` devem falhar antes e passar depois, com PostgreSQL no ar. P1 quebraria fixtures que usam Inspeção RFO. Risco associado: R-13. |
| **Referência** | `00_docs/projeto/revisao-regras-ocorrencias.md`, `04_backend/tests/test_ocorrencias_regras.py` |

## DEC-35 — `layout.json` derivado de PDF guarda só geometria e rótulos fixos (proposta de T09/T10)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | As tarefas T09 (Vistoria Cautelar) e T10 (Vistoria Residencial) estenderam o método de ADR-13/DEC-25 aos PDFs finais do cliente. O rodapé desses PDFs traz nome, CREA, e-mail e telefone do responsável. O `templates/ltip/layout.json` (BL-17) guarda hoje as linhas do rodapé do emitente. |
| **Decisão proposta** | (A) Nos `layout.json` derivados de PDF, o rodapé e a identificação do responsável viram papéis/placeholders, nunca o texto do exemplar; o `layout.json` passa por verificador fail-closed de dado pessoal. Alinhar o LTIP em tarefa própria; se não for alinhado, registrar como resíduo de A02 em `riscos.md`. (B) O `layout.json` não grava `gerado_em`: regerar a partir do mesmo original não pode produzir diff; o sha256 do original basta para a procedência. |
| **Consequências** | Os `layout.json` das duas vistorias já seguem a regra; o do LTIP não. O nome do arquivo original identifica unidade/obra e por isso não é versionado. |
| **Referência** | `00_docs/backlog-auto/vistoria-cautelar-templates.md`, `00_docs/backlog-auto/vistoria-residencial-templates.md` |

## DEC-36 — RFIP: coluna auxiliar oculta como mapa rótulo → valor, numeração de páginas e quadro-resumo (proposta de T13)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | O template do RFIP (BL-12, T13) nasce de uma planilha de 491 MB cujas fichas fotográficas misturam rótulos fixos e valores do exemplar. A coluna B, oculta, traz marcadores `<CAMPO> Foto nº NN`, a mesma chave dos `PROCV` da aba de resumo. O exemplar numera as páginas a partir de 30 (anexo do laudo) e tem um quadro-resumo na aba `Relatório`. |
| **Decisão proposta** | (A) O extrator usa os marcadores da coluna auxiliar para separar rótulo de valor; um texto só é rótulo fixo se repetir igual em todas as fichas amostradas, e a ausência da coluna faz a extração falhar de forma explícita. (B) A numeração de páginas começa em 1 nos dois formatos; o valor original fica em `pagina.primeira_pagina_no_original`, sem ser aplicado. (C) O quadro-resumo é opcional (`incluir_resumo`) e vem depois das fichas. (D) O `layout.json` do RFIP segue a regra de DEC-35 (só geometria e rótulos fixos, verificador fail-closed de dado pessoal). |
| **Consequências** | Se o cliente mudar a planilha e remover a coluna auxiliar, o extrator precisa de revisão. A numeração contínua com o LTIP passa a ser decisão da montagem do pacote. |
| **Referência** | `00_docs/backlog-auto/rfip-templates.md` |

## DEC-37 — Legendas por IA: estados de validação, rastreio do prompt e independência do provedor (proposta de T14)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | RF-15, RN-16 e RN-17 já estão descritos em `arquitetura.md` §3 e na ADR-12, mas o código não tem `prompts_ia` nem as colunas de legenda IA em `fotos`. `PUT /fotos/{id}` descarta o usuário e não permite limpar a legenda. A análise mostrou que só 3 de 22 lacunas dependem do provedor de LLM (B-04). |
| **Decisão proposta** | (1) `status_validacao_ia` com valores fechados `rascunho` e `aprovada`; `NULL` = sem sugestão; só `aprovada` entra no relatório (DP-1). (2) Versões de `prompts_ia` imutáveis e `prompt_conteudo_hash` (SHA-256) gravado na geração (DP-2). (3) `aprovado_por_id`/`aprovado_em` vêm do token, nunca do payload, e só no `PUT` que aprova (DP-3). (4) O endpoint `gerar` escreve apenas nos campos de sugestão; `legenda` só muda no `PUT` de aprovação (DP-4). (5) `PUT /fotos/{id}` passa o usuário ao serviço e distingue `legenda: null` de campo ausente por `model_fields_set` (DP-5). (6) BL-36 e BL-37 deixam de depender de B-04; só BL-34 (adapter concreto), a retenção de dados (L13) e BL-38/39 dependem (DP-6). (7) Sem áudio no storage; a transcrição fica em `legenda_bruta` (DP-7). (8) Corrigir o rótulo do ER em `arquitetura.md:288` (DP-8). |
| **Consequências** | BL-36 e BL-37 podem começar antes da escolha do provedor, com um `FakeLegendaIAClient` nos testes. Toda migration nova precisa de `downgrade()` e de unicidade parcial de `ativo` por `nome`. A política de retenção (R-10) continua bloqueando o uso em produção. |
| **Andamento (T22, 2026-11-04)** | DP-1 a DP-4, DP-8 e a parte de persistência de DP-2 implementados em BL-36 (migration `f7c2a9d4e6b1`: `status_validacao_ia` por CHECK, `prompt_conteudo_hash`, `aprovado_por_id`/`aprovado_em`, FK `ON DELETE RESTRICT`, índice parcial de `ativo`). A imutabilidade das versões fica no serviço (BL-37), a regra de escrita e o `PUT` com usuário (DP-3, DP-4, DP-5) em BL-34. **DP-9 (proposta):** em BL-38, a regra «só `aprovada` entra no relatório» vale para legenda de origem IA; foto com `status_validacao_ia = NULL` (manual ou legada) entra com `legenda`; foto em `rascunho` entra com `legenda`, nunca com `legenda_ia_sugerida`. |
| **Andamento (T23/T24, 2026-11-04)** | T23 implementou a imutabilidade das versões de prompt e o cálculo do hash no serviço (`prompt_ia_service.py`), restando gravar `prompt_conteudo_hash` na geração (BL-34); o hash não tem coluna em `prompts_ia` (proposta: manter assim). T24 implementou DP-9 só no `rfo_pipeline.py`; os outros quatro pipelines ainda precisam chamar `legenda_para_relatorio`. DP-9 segue proposta, sem aprovação do dono. |
| **Andamento (T25, 2026-11-05)** | DP-3, DP-4, DP-5 e DP-6 implementados em BL-34 (endpoints com cliente injetável; `legenda` só muda no `PUT`; aprovação por `aprovar_legenda_ia` com aprovador e data do token; `legenda: null` limpa, ausente preserva; sem provedor → 503) e hash do prompt gravado na geração (parte restante de DP-2). **DP-10 (proposta):** `PUT` que altera `legenda` de foto já `aprovada` sem a flag mantém hoje o status e o aprovador anterior; pela regra «quem edita é quem aprova», tratar como nova aprovação pelo usuário do token ou exigir a flag (422). Aguarda o dono. Ver `00_docs/backlog-auto/legenda-ia-endpoints.md` |
| **Andamento (T26, 2026-11-05)** | BL-35 (frontend) consome o contrato de BL-34 sem enviar `aprovado_por_id`, `aprovado_em` nem `status_validacao_ia` (DP-3). Aprovação em duas etapas na UI; só `auditor`/`auxiliar` veem o painel (RN-18). Persiste DP-10: a edição manual da legenda no card continua um `PUT {legenda}` simples e mantém `aprovada`; aguarda o dono. **Proposta:** o `ApiError` do frontend passar a guardar o `type` do RFC 7807 para distinguir `legenda-ia-indisponivel` pelo sufixo. Ver [legenda-ia-frontend.md](../backlog-auto/legenda-ia-frontend.md) |
| **Referência** | `00_docs/backlog-auto/modelagem-legendas-ia-lacunas.md`, `00_docs/backlog-auto/legenda-ia-modelo.md` |

## DEC-38 — Visitas: unicidade, validação de domínio e CRUD completo (proposta de T15)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A revisão de BL-10 contra RN-01/RN-02 encontrou 18 lacunas: `seq_numero` sem UNIQUE (corrida gera duplicata), nenhuma regra de uma visita por dia, data futura aceita, visita aceita em inspeção que não é RFO, quantidades sem restrição (500 acima de int32), `PUT` que apaga `observacoes` omitida e ausência de GET/PUT/DELETE dos itens. |
| **Decisão proposta** | (A) Visita só em inspeção `tipo == "RFO"`, com `Inspecao.tipo` como enum; outro tipo retorna 409. (B) `UNIQUE(inspecao_id, data)` e `UNIQUE(inspecao_id, seq_numero)` em migration com `downgrade()`, 409 no serviço e data de visita ≤ hoje. (C) Payloads com `extra="forbid"`; equipe com `quantidade` inteira 1..32767; medição com `quantidade ≥ 0`; textos aparados e não vazios (a unidade segue livre, DEC-29). (D) `PUT` de visita passa a ser parcial (campo omitido preserva). (E) Completar o CRUD de campo: `GET /visitas/{id}` e PUT/DELETE de mão de obra e medição. Itens (A) e a data futura são interpretações de RN-01/RF-03 e precisam de confirmação do dono antes da correção. |
| **Consequências** | Exige migration e correção de dados duplicados existentes, se houver. O vínculo usuário↔contrato de DEC-27 (L15) continua sem imposição e depende de decisão própria. A regra de status da inspeção e a de mão de obra duplicada na mesma visita ficam em aberto. |
| **Andamento (T21, 2026-11-04)** | Itens A–E implementados e testados (migration `e5a1c3f7b9d2`, 409/422, PUT parcial, CRUD de itens). `Inspecao.tipo` como enum, status da inspeção, mão de obra duplicada e L15 (DEC-27) seguem abertos. Se o dono discordar de «só RFO» ou da data ≤ hoje, a reversão é pontual. Ver `00_docs/backlog-auto/visitas-correcoes.md`. |
| **Referência** | `00_docs/backlog-auto/revisao-regras-visitas.md`, `04_backend/tests/test_visitas_lacunas.py` |

## DEC-39 — Fotos: chave de storage controlada pelo servidor, orientação EXIF e validação de domínio (proposta de T16)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A revisão de BL-11 achou 9 lacunas. Duas são graves: o vínculo (`POST /ocorrencias|visitas/{id}/fotos`) aceita `storage_key` do cliente (`../../x`, prefixo qualquer, objeto de outro contrato) e `DELETE /fotos/{id}` apaga o objeto; e `reprocessar_imagem` descarta o EXIF sem `exif_transpose`, então foto de celular em pé sai deitada nos PDF/DOCX. Também faltam validação de `ordem`/`origem`/`legenda`, descarte de upload órfão e limite de corpo da requisição. |
| **Decisão proposta** | (A) O vínculo aceita só `storage_key` que case `^fotos/[0-9a-f-]{36}\.(jpg|png|webp)$`, exista no bucket e ainda não esteja vinculada (`UNIQUE(storage_key)`, migration com `downgrade()`); alternativa mais forte: o upload cria uma `Foto` pendente e o vínculo informa só `foto_id`. (B) `ImageOps.exif_transpose` antes de descartar o EXIF. (C) `origem` como enum fechado, `ordem ≥ 0`, `legenda` com `max_length` (sugestão 500) e `PUT` com `model_fields_set` para poder limpar a legenda. (D) Descarte de upload órfão (endpoint ou job de limpeza de `fotos/*` sem `Foto` com mais de 24 h). (E) Leitura de fotos com URL pré-assinada na resposta, para fechar o fluxo de exibição de BL-11. (F) Limite de corpo no proxy/Uvicorn e `Image.MAX_IMAGE_PIXELS` explícito (ex.: 50 Mpx). |
| **Consequências** | Fecha uma falha de controle de acesso a objetos (A01) e melhora a qualidade do relatório. O auxiliar continua editando fotos de qualquer contrato enquanto não houver vínculo usuário↔contrato. A URL pré-assinada usa o host interno do MinIO e precisa de endpoint público em produção (pendência de infra). |
| **Andamento (T19, 2026-11-04)** | Aplicados A (na aplicação, sem `UNIQUE`: exigiria migration), B, C e D (endpoint `DELETE /fotos/upload`) e o teto de 50 Mpx de F. Não aplicados: `UNIQUE(storage_key)`, E (URL pré-assinada) e o limite de corpo no proxy. `PUT` com `ordem: null` passou a limpar o campo. Ver `00_docs/backlog-auto/fotos-correcoes.md`. |
| **Referência** | `00_docs/backlog-auto/revisao-regras-fotos.md`, `04_backend/tests/test_fotos_lacunas.py` |

## DEC-40 — RNF-06 verificado por tipo de relatório e por job completo; fotos de 1200 px na entrada dos pipelines (proposta de T17)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A re-medição com os pipelines finais (1 execução por combinação) deu, para o job PDF+DOCX em sequência: RFO 21,1 s, Vistoria Cautelar 34,2 s, Vistoria Residencial 56,7 s e LTIP 63,2 s com apenas 137 páginas. A conclusão de 2026-08-05 (RNF-06 atingível reduzindo a foto uma vez no upload) vale para RFO e Cautelar, não vale para o LTIP e fica no limite na Residencial. O gargalo é o layout do WeasyPrint (98–99,7 % do PDF), não mais o tamanho das fotos. |
| **Decisão proposta** | (A) RNF-06 passa a ser verificado por tipo de relatório e pelo job completo (leitura das fotos, PDF, DOCX e upload), com PDF e DOCX gerados em processos paralelos e worker com ≥ 1 GB de RAM (pico de ~500 MB). (B) Os pipelines recebem sempre a derivada de 1200 px/q72, gerada uma vez no upload (BL-11), nunca a foto de 2000 px; o limite de upload dos artefatos finais (PDF 37–38 MB, DOCX 30–31 MB nas vistorias) fica separado do limite de foto (25 MB). (C) O template do LTIP troca o container flex único por linhas explícitas de duas fichas (`<table>` ou bloco por par com `break-inside: avoid`), pelo gerador `build_ltip_templates.py`, e ganha o placeholder `{{ ocorrencia.foto }}` no DOCX. (D) A Vistoria Residencial ganha profiling do WeasyPrint antes de ser dada como atendida. |
| **Consequências** | Enquanto o LTIP não for refeito, RNF-06 não é atendido para ele (R-03 reaberto). A medição precisa ser completada em host dedicado (3 execuções, cenário de 2000 px, LTIP com ~357 ocorrências para chegar a 200 páginas, extrapolação de ~93 s de PDF). O RFIP não foi medido (sem pipeline). |
| **Andamento (T20, 2026-11-04)** | O item (C) foi feito no LTIP sem trocar o gerador: 11,6 s (239 fotos) e 19,3 s (~200 páginas), RNF-06 atendido. Os detalhes viraram a DEC-41. O item (D) (profiling da Residencial) continua aberto. |
| **Referência** | `00_docs/backlog-auto/benchmark-pipelines-finais.md`, `00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md` |

## DEC-41 — WeasyPrint: sem container flex/grid único atravessando páginas; fotos por `url_fetcher` (proposta de T20)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-04 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | O LTIP levava 72,1 s (239 fotos) e 154,5 s (382 fotos) por causa do custo quadrático do WeasyPrint 70 num único `display: flex` de fichas que atravessa várias páginas. Trocando o container por linhas explícitas de duas fichas e entregando as fotos por `url_fetcher` em vez de data URI, o PDF caiu para 11,6 s e 19,3 s (−84 % e −88 %), na faixa do RFO (0,09 s/página). Implementa o item (C) de DEC-40 para o LTIP. |
| **Decisão proposta** | (A) Nos templates WeasyPrint, conteúdo repetitivo que atravessa páginas (fichas, fotos, figuras) não fica num único container `flex`/`grid`: cada linha vira bloco pequeno (tabela fixa ou flex por linha) com `page-break-inside: avoid`. (B) Os pipelines PDF entregam as fotos ao WeasyPrint por `url_fetcher` (`URLFetcher`), mantendo `renderizar_html` autocontido para testes e pré-visualização; hoje só o LTIP faz isso, e estender aos demais (RFO, vistorias, RFIP) fica para tarefa própria (economia de ~2 s e ~100 MB por 240 fotos). (C) Fixar `weasyprint>=70` em `requirements.txt` ou manter o fallback para data URI, que não foi testado. |
| **Consequências** | R-03 deixa de apontar o LTIP como violação de RNF-06. O DOCX do LTIP continua sem foto (lacuna de BL-17). O RFIP ainda não foi medido; o `rfip_pipeline.py` (T18) usa data URI e deve ser medido ao receber ocorrências reais. |
| **Andamento (T28, 2026-11-05)** | O item (B) foi estendido a RFO, Vistoria Cautelar e Vistoria Residencial por `report_generator/foto_fetcher.py` (estrito: só `garra-foto:<n>` registrado e `data:`). RFIP e LTIP não mudaram (o LTIP mantém cópia local; unificar é proposta). Testes de PDF pulados sem GTK; ganho **não medido**. Ver `pipelines-url-fetcher.md`. |
| **Referência** | `00_docs/backlog-auto/ltip-desempenho.md` |

## DEC-42 — Legenda por IA: aprovação só por auditor, invalidação ao editar/regerar e teto de custo (proposta de T29)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-05 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A revisão de segurança T29 (SEG-IA-01..09) achou: sem limite de taxa/custo em `POST /fotos/{id}/legenda-ia/gerar`; regerar legenda aprovada mantém `aprovado_por_id/em`; `PUT` que muda `legenda` aprovada mantém a aprovação (DP-10 de DEC-37); saída do LLM sem limite de tamanho; auxiliar aprova legenda embora RN-16/RN-18 reservem a aprovação ao responsável. |
| **Decisão proposta** | (A) Aprovar legenda IA só com perfil `auditor`; o auxiliar gera e edita rascunho (muda `test_auxiliar_gera_e_aprova` e a UI da T26). (B) Regerar ou editar legenda aprovada zera `aprovado_*` e volta a `rascunho`, o que fecha DP-10. (C) Limite de taxa por usuário e por foto em `gerar`, e tamanho máximo/saneamento da saída do LLM (`legenda_ia_sugerida`, alertas, pendências), antes de BL-34 ligar o adapter real. (D) Delimitar `legenda_bruta` no adapter (injeção de prompt). |
| **Consequências** | (C) e (D) bloqueiam produção do adapter real, junto de R-10. Decidir L15 (vínculo usuário↔contrato, DEC-27) continua pendente (SEG-IA-07). |
| **Referência** | `00_docs/backlog-auto/seguranca-legenda-ia.md` |
| **Andamento (T33–T35, 2026-11-06)** | (A) e (B) implementados no backend (T33, `legenda-ia-aprovacao-auditor.md`) e no painel (T34, `legenda-ia-aprovacao-frontend.md`). (C) e (D) implementados em `app/services/legenda_ia/` (T35, `legenda-ia-limites.md`): limite por usuário (10 por 60 s, 200 por dia) e por foto (5 por hora), com 429 antes de baixar a imagem; saída truncada em 500 caracteres e saneada (marcação, controle Unicode), `legenda_bruta` delimitada no envio e gravada original. Os defaults são escolha do agente, sem medição de uso: o dono deve revê-los. Pendente para a decisão ser considerada cumprida: orçamento global (SEG-IA-01), contador compartilhado entre workers (hoje em memória por processo), `Retry-After` no header, variáveis `LEGENDA_IA_*` no compose, e a revisão do adapter por SEG-IA-08. SEG-IA-06 (auxiliar remove foto aprovada) não está coberto por nenhum item. |

## DEC-43 — `origem` da foto: enum fechado no backend (proposta de T27)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-05 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | `FotoVincularPayload.origem` é `str` livre; não há CHECK no banco. O valor aceito só existe no frontend (`OrigemFoto`), e o seed usa `upload_manual`. A afirmação da T26 de que `upload` causava 422 era incorreta. |
| **Decisão proposta** | Impor `Literal["upload_manual","lightshot","clipboard"]` no payload e, em tarefa própria com migration, normalizar dados existentes e avaliar um CHECK. |
| **Consequências** | Registros antigos gravados com `upload` (se houver) precisam de migração de dados antes do CHECK. |
| **Andamento (T31, 2026-11-06)** | A parte do payload foi concluída: `FotoVincularPayload.origem` é `OrigemFoto = Literal["upload_manual","lightshot","clipboard"]` em `04_backend/app/schemas/foto.py` (422 para outro valor; `FotoBase`/`FotoRead` seguem `str`, então dados antigos continuam legíveis). Testes em `tests/test_foto_origem_enum.py` (schema sem banco: passam; endpoint: pulam sem PostgreSQL). O enum já havia sido esboçado na T19 (DEC-39 C). **Seguem abertos:** migration de normalização de dados antigos (ex.: `upload`) e CHECK no banco; a decisão continua proposta. |
| **Referência** | `00_docs/backlog-auto/frontend-origem-foto.md`, `00_docs/backlog-auto/dec-43-origem-foto.md` |

## DEC-44 — Política de limpeza de objetos órfãos no storage (proposta de T30)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-05 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A T30 confirmou o storage compatível com artefatos de IA e adicionou `exists`, `list_keys` e `listar_orfaos` (só leitura). Não existe tarefa agendada de limpeza; uploads sem vínculo (`DELETE /fotos/upload` só cobre o descarte explícito) podem acumular. |
| **Decisão proposta** | (1) Rodar `listar_orfaos` periodicamente apenas gerando relatório/log. (2) Só apagar objetos com idade > 24 h (exige expor `LastModified`, não incluído). (3) Iniciar em dry-run; apagar só com aprovação manual da lista, ou automático após N dias se o dono decidir. (4) Prefixos distintos para fotos (`fotos/`) e artefatos de IA (`ia/`). |
| **Consequências** | Nada é apagado automaticamente até a aprovação. Fakes futuros de `StorageClient` devem implementar `exists` e `list_keys`. |
| **Andamento (T32, 2026-11-06)** | Itens 1–3 em parte: `StorageClient.list_objects(prefix)` devolve `(chave, LastModified)` (`list_keys`/`listar_orfaos` inalterados) e `python -m app.scripts.relatorio_orfaos [--idade-minima-horas 24] [--prefixo fotos/]` gera o relatório **só em dry-run** (sem chamada de exclusão; há teste que garante isso). Testes com S3 falso: 9 passando junto com `test_storage_legenda_ia.py`. **Abertos:** exclusão (exige aprovação manual da lista), agendamento periódico e o item 4 (prefixos `fotos/` x `ia/`); script não executado contra PostgreSQL/MinIO reais. A decisão continua proposta. |
| **Referência** | `00_docs/backlog-auto/storage-legenda-ia.md`, `00_docs/backlog-auto/storage-orfaos-relatorio.md` |

## DEC-45 — Restore: dump `pre-restore` obrigatório e retenção dos `pre-restore-*` (proposta de T42)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-07 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | O teste com stubs mostrou que o script de restore termina o dump `pre-restore` com `|| true`: se ele falhar ou sair vazio, o script avisa «Estado anterior salvo» e executa `pg_restore --clean`, destruindo o banco sem rede de segurança. Os `pre-restore-*.dump` também nunca expiram. |
| **Decisão proposta** | (1) Abortar com exit ≠ 0 quando o `pre-restore` falhar ou estiver vazio, com `FORCAR_SEM_PRE_RESTORE=1` para ignorar de forma explícita. (2) Incluir os `pre-restore-*.dump` na retenção por `-mtime`. |
| **Consequências** | Muda o comportamento visível do script; o bloco INFO do teste vira asserção quando aprovada. Não aplicada nesta etapa. |
| **Referência** | `00_docs/backlog-auto/backup-verificacao.md` §4 |

## DEC-46 — Lint do backend bloqueante no CI só após limpeza, com ruff fixado (proposta de T39)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-07 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | `ruff check .` (ruff 0.17.3, `04_backend/ruff.toml`) acusa 11 erros em arquivos adicionados depois da T04 (2 RUF001, 4 I001, 2 RUF043, 3 RUF005). O CI instala `ruff` sem versão e mantém o passo com `continue-on-error: true`. |
| **Decisão proposta** | (1) Corrigir os 11 erros numa tarefa própria (4 com `--fix` seguro; RUF005/RUF043 à mão). (2) Trocar `pip install ruff` por `pip install "ruff==0.17.3"` em `ci.yml`. (3) Remover `continue-on-error` do passo. (4) Marcar o `ci.yml` como status check obrigatório (já pendente em BL-26). |
| **Consequências** | Sem a limpeza, novos erros de lint continuam entrando sem barrar o merge. Alterar `ci.yml` é mudança de YAML, fora do escopo de documentação. |
| **Andamento (T43, 2026-11-10)** | Itens 1 e 2 feitos: `ruff check 04_backend` sai com 0 achados (ruff 0.15.1 com `04_backend/ruff.toml`) e o CI instala `ruff==0.15.1`. **Divergência:** a proposta citava 0.17.3; prevaleceu a versão realmente usada localmente. `continue-on-error: true` **mantido**: itens 3 e 4 (bloqueante e status check obrigatório) aguardam aprovação. `pytest` não rodou (PostgreSQL fechado). A decisão continua proposta. |
| **Referência** | `00_docs/backlog-auto/ci-lint-bloqueante.md`, `00_docs/backlog-auto/ruff.md`, `00_docs/backlog-auto/lint-backend-limpeza.md` |


## DEC-47 — Contexto do RFO: legenda pelo helper comum, validação de completude e ocorrências no RFO (proposta de T45)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-10 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | `montar_contexto_rfo` (BL-13) foi escrita num worktree defasado e declarou inexistentes `legenda_foto.py` e o campo `legenda_status`. Na `main` o helper existe (`legenda_para_relatorio`: imprime sempre `legenda`, nunca `legenda_ia_sugerida`; o estado da IA fica em `status_validacao_ia`, DEC-37) e `Foto` **não** tem `legenda_status`. O `legenda_aprovada` do contexto é, na prática, código morto permissivo. Além disso, o banco traz campos nulos (`fiscal.crea`, `art_fiscalizacao`, `objeto`, `data_inicio`, `prazo_dias`) que o template imprime vazios, e o template do RFO não renderiza `ocorrencias` nem `observacoes_gerais`. |
| **Decisão proposta** | (1) Trocar `legenda_aprovada` por `legenda_para_relatorio` no contexto e descartar a proposta P1 do doc da T45 (nova coluna `legenda_status` **não** é necessária). (2) Validar campos obrigatórios do template antes de gerar e responder 422 (P2). (3) Decidir se o RFO imprime ocorrências (RF-04..06) ou se ficam só no LTIP (P3). |
| **Consequências** | Sem (1) o contexto fica divergente dos demais pipelines (T36/T37). Sem (2) o PDF/DOCX sai com campos em branco ou `None`. Nada aplicado nesta etapa; (1) e (2) cabem na T46 ou numa tarefa curta. **Atualização (T48/T50, 2026-11-11):** (1) e (2) foram implementados no código (ainda como proposta, sem aprovação); falta (3) e decidir `executores[].art_execucao`. Testes com banco não rodaram. |
| **Referência** | `00_docs/backlog-auto/rfo-contexto-banco.md` |

## DEC-48 — Emissão de relatórios: versionamento, chaves, unicidade e 503 (proposta de T46)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-10 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A T46 criou o primeiro endpoint que emite relatório (RFO). Foi preciso escolher versionamento, convenção de chaves no storage e comportamento sem WeasyPrint. Implementado como padrão, sem migration. |
| **Decisão proposta** | (P1) Cada emissão cria um `Relatorio` novo (`V01`, `V02`…) por inspeção e tipo, sem sobrescrever; avaliar se o Portal deve mostrar só a mais recente. (P2) Chaves `relatorios/{inspecao_id}/{tipo}-v{NN}.{ext}` para todos os tipos. (P3) Migration futura com `UNIQUE (inspecao_id, tipo, versao)` após conferir os dados; hoje a unicidade depende do lock `FOR NO KEY UPDATE`. (P4) `503 gerador-relatorio-indisponivel` como contrato para todo endpoint de geração. (P5) Teto de 200 MB por arquivo (`MAX_RELATORIO_SIZE_BYTES`), a revisar com o benchmark de 200 páginas. |
| **Consequências** | Sem P3 a unicidade não é garantida pelo banco. A emissão é síncrona e o tempo cresce com as fotos (RNF-06); geração assíncrona fica como tarefa futura. DEC-47 (2) e (3) seguem pendentes. **Atualização (T47/T49/T51, 2026-11-11):** P3 implementada (migration `e5a1f0c2b7d4`, não aplicada em banco migrado); P5 é constante, sem env (T47; alternativa: ler de `Settings` se o benchmark de 200 páginas mudar o teto); P1: o Portal mostra todas as versões e o único gap é a falta de `vigente` (proposta: adicionar `vigente`, manter versões antigas baixáveis, ocultar rascunhos; vigência por `inspecao_id`+`tipo`). Nada disso está aprovado. |
| **Referência** | `00_docs/backlog-auto/rfo-endpoint-emissao.md` |

## DEC-49 — Legenda por IA: DeepSeek Platform API em modo só texto, com contexto minimizado (proposta de T63/T65)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-11 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | T63 implementou o cliente real da DeepSeek (api-docs.deepseek.com, consultada em 2026-11-11). A documentação não afirma que nenhum modelo da API processe imagem (o nome com «vision» foi aposentado). T65 definiu o que vai ao provedor. |
| **Decisão proposta** | (P1) Provedor: DeepSeek Platform API, modelo padrão `deepseek-flash`, o que resolve o bloqueio B-04 (escolha do provedor). (P2) Modo `texto` por padrão: prompt no `system`, dados técnicos e legenda bruta delimitada no `user`; imagem só com `DEEPSEEK_ENVIAR_IMAGEM=true`, depois de confirmar um modelo com visão. (P3) Minimização (R-10): nenhum nome de cliente, endereço, pessoa, id ou data no contexto; CPF, CNPJ, e-mail e telefone viram marcadores por regex. (P4) `fake` só em desenvolvimento e teste; `fake` em produção ou `deepseek` sem chave → 503. (P5) A saída do modelo não define o status: `status_validacao` do modelo não é gravado (sempre `rascunho`), `nivel_certeza` é normalizado e valor desconhecido vira alerta. (P6) Retry de até 2 vezes, só em 429, 5xx e timeout. |
| **Consequências** | Sem imagem, a legenda só usa a anotação do usuário, e a acurácia depende de T67/T68 (R-18). A regex não detecta nome de pessoa em texto livre, então R-10 continua aberto até a política de retenção do provedor ser definida. A chave `DEEPSEEK_API_KEY` entra só por variável de ambiente (`sync: false` no Render). Nenhuma chamada real foi feita até agora. |
| **Referência** | `00_docs/backlog-auto/v1-legenda-ia-deepseek.md`, `00_docs/backlog-auto/ia-contexto-legenda.md` |

## DEC-50 — Emissão de relatórios por registro de emissores e conteúdo narrativo por (inspeção, tipo) (proposta de T57/T58/T60)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-11 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A emissão era só do RFO. T58 generalizou; T57 criou a base de dados para os tipos com texto narrativo; T60 registrou o primeiro tipo novo. |
| **Decisão proposta** | (P1) Cada tipo é um `Emissor` (`montar_contexto`, `validar_contexto`, `extrair_fotos`, `pipeline`) registrado em `relatorio_service.EMISSORES`; uma rota única `POST /inspecoes/{id}/relatorios/{tipo}`, mais listagem de versões e download interno por URL pré-assinada (auditor e auxiliar). Tipos registrados: RFO e VISTORIA_CAUTELAR. (P2) `TipoServico` é o enum de 5 valores, gravado em maiúsculas; a leitura aceita `TipoServico ou str` para não dar 500 com valores legados. (P3) `relatorio_conteudos`: um conteúdo por (inspeção, tipo de relatório), independente de `inspecao.tipo`; `PUT` substitui e é só do auditor; a leitura mescla o padrão com o salvo; placeholders só nos padrões. (P4) Campos obrigatórios da Vistoria Cautelar: fiscal (nome, CREA) e parecer, estendendo DEC-47. (P5) A cidade da emissão sai do endereço (`Cidade-UF`) até existir `cidade`/`uf` em `Edificacao`. (P6) Foto com legenda não aprovada continua no relatório, com legenda `—` (BL-36). |
| **Consequências** | LTIP, RFIP e Residencial só precisam registrar um `Emissor`, sem rota nova. `inspecoes.contrato_id` é UNIQUE, então um contrato tem uma inspeção só: RFO e LTIP do mesmo contrato exigem decisão de produto (a fixture de teste foi corrigida, o modelo não). Valores legados fora do enum (`FISCALIZAÇÃO DE OBRA` no dev) pedem migration de dados com aval do cliente. A Cautelar lista todas as ocorrências no Plano de Correções, sem filtrar por `situacao`; falta decidir com o cliente. `ResponsavelUpdate` existe sem rota, e a emissão devolve 409 se `assinatura_storage_key` aponta para arquivo ausente. |
| **Referência** | `00_docs/backlog-auto/v1-emissao-generica.md`, `v1-fundacao-dados.md`, `v1-vistoria-cautelar-contexto.md` |

## DEC-51 — Dados de demonstração com prefixo `DEMO` (proposta de T64)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-12 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | A conferência visual (HT-09) e a suíte completa precisam de dados dos 5 tipos de relatório sem tocar nos dados reais. |
| **Decisão proposta** | Tudo que o seed de demonstração cria leva o prefixo `DEMO` (nomes `DEMO - ...`, e-mail `demo.auditor@example.com`, chaves de storage `fotos/demo/`). `seed_demo --reset` e `--limpar` só mexem nesse prefixo. A senha do auditor vem só de `DEMO_SENHA`. Rodar em banco separado (`garra_demo_v1`), não no de desenvolvimento. |
| **Consequências** | Seed idempotente e reversível. Em ambiente novo o gabarito de sistemas prediais precisa do arquivo `00_docs/convertidos/RFO_INSPECAO.md`, que não está na imagem do backend (embutir o gabarito parseado ou montar a pasta como volume). Os relatórios emitidos no MinIO precisam de limpeza à parte. |
| **Referência** | `00_docs/backlog-auto/v1-amostras-ht09.md` |

## DEC-52 — Cache local e telemetria de custo da legenda IA (proposta de T68)

| Campo | Valor |
|---|---|
| **Data** | 2026-11-12 |
| **Status** | Proposta (aguarda aprovação do dono) |
| **Contexto** | R-10: com 150 ou mais fotos por relatório, o custo da legenda IA precisa ser medido e a regeração, evitada. |
| **Decisão proposta** | (P1) Chave do cache = sha256 de prompt (hash), modelo e contexto canônico, mais a `storage_key` em modo imagem. Só resposta de sucesso da API entra no cache; TTL de 720 h (`LEGENDA_IA_CACHE_TTL_H`, `0` desliga). Acerto de cache não chama o provedor e continua exigindo aprovação (a legenda volta a `rascunho`, DEC-42). (P2) Toda chamada grava `chamadas_ia` (tokens, custo estimado, latência, origem `api` ou `cache_local`; erro sem mensagem nem chave); `foto_id` é `SET NULL` para o histórico sobreviver à exclusão da foto. (P3) `GET /api/v1/ia/uso` só para auditor. (P4) Preços por variável de ambiente (`DEEPSEEK_PRECO_*`); sem os 3 preços o custo é `null`. |
| **Consequências** | A coluna `resposta` guarda a legenda saneada sem política de retenção definida (avaliar com R-10). O limite de taxa (DEC-42 C) continua contando acertos de cache; decidir se devem poupar cota. Preços reais dependem de IA-07. |
| **Referência** | `00_docs/backlog-auto/ia-telemetria-cache.md` |
