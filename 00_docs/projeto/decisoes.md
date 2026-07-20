---
title: Registro de Decisões — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-17
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

