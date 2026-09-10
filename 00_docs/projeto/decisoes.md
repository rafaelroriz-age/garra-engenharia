---
title: Registro de Decisões — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-09-10
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

