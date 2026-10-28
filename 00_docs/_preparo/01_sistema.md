# 01 — Mapa do sistema (tarefa D01)

> Preparo da documentação, Bloco 0 do `BACKLOG.md`. Levantamento feito em 2026-10-28 sobre o commit `161ba19` (branch `worktree-backlog-D01`, 40 commits, de 2026-07-19 a 2026-09-10 segundo `git log --format=%cs`).
> Regra deste documento: toda afirmação cita o arquivo ou o comando que a comprova. Onde não deu para verificar, está escrito **não determinado**.

---

## 1. Objetivo do sistema e quem o usa

### 1.1 Objetivo declarado pelo dono

> «Sistema web (PWA) da Garra Engenharia que automatiza a produção de relatórios técnicos de engenharia predial (RFO, LTIP e relatório fotográfico): o engenheiro registra edificações, contratos, visitas e ocorrências com fotos pelo celular e gera PDF e DOCX fiéis aos modelos do cliente, com classificação de anomalias (CMM/GUT), dashboard de saúde da edificação e portal do cliente.»

O contexto de negócio está em `00_docs/estudo-do-contexto.md` §1: o gargalo é a produção manual dos documentos a partir de planilhas XLSM e templates.

### 1.2 Confronto com o código

| Parte do objetivo | O que o código faz | Situação |
|---|---|---|
| Sistema web PWA | Next.js 14 (`03_frontend/package.json`). `app/layout.tsx:29` declara `manifest: "/manifest.json"` e existe `public/manifest.json`. Não há service worker nem `next-pwa` (busca por `serviceWorker`/`next-pwa` sem resultado). | **Parcial**: instalável via manifest, mas sem modo offline. Isso é coerente com ADR-15 em `00_docs/arquitetura.md` (PWA online-first). |
| Registrar edificações, contratos, visitas e ocorrências | Rotas em `04_backend/app/api/v1/{edificacoes,contratos,inspecoes,visitas,ocorrencias}.py` e telas em `03_frontend/app/{edificacoes,contratos,inspecoes/[id]/visitas,inspecoes/[id]/ocorrencias}/`. A inspeção é criada junto com o contrato (`app/repositories/contrato_repository.py:74`). | **Conforme** |
| Fotos pelo celular | `POST /api/v1/fotos/upload` (multipart) e `POST /api/v1/fotos/upload-clipboard` (base64), em `app/api/v1/fotos.py`. A imagem é validada e recodificada pelo Pillow, sem EXIF (`app/services/image_processing.py:42`). No frontend, editor de anotação com Fabric.js (`components/photo-annotation-editor.tsx`). | **Conforme** |
| **Gerar PDF e DOCX fiéis aos modelos** | Existem os templates derivados do original (`04_backend/templates/rfo/`, `templates/ltip/`) e as funções `gerar_pdf`/`gerar_docx` em `app/services/report_generator/rfo_pipeline.py`. **Nenhuma rota da API chama essas funções**: `grep` por `rfo_pipeline`/`report_generator` em `app/` só encontra o próprio pacote; registros `Relatorio(...)` só são criados em `app/scripts/benchmark_relatorio_geracao.py:143`. A tela `03_frontend/app/inspecoes/[id]/relatorio/page.tsx` é um placeholder (`UnderConstruction`). Não existem as rotas `POST /inspecoes/{id}/relatorios/gerar` e `GET /relatorios/job/{job_id}` previstas em `00_docs/arquitetura.md` §4. | **Divergente**: o usuário final não consegue gerar relatório. Só há geração por script, e o PDF só renderiza dentro do container (`04_backend/README.md`, nota sobre GTK). |
| RFO, LTIP e relatório fotográfico | Pipeline só para o RFO (`rfo_pipeline.py`). Para o LTIP existem só os templates (`templates/ltip/*`, gerados por `app/scripts/build_ltip_templates.py`), sem função de renderização. Não há template próprio de relatório fotográfico (RFIP); o LTIP inclui fichas fotográficas (`00_docs/projeto/status.md`, linha BL-17). | **Parcial** |
| Classificação CMM/GUT | CMM: `grau_risco` em `MINIMO`/`MEDIO`/`CRITICO`, validado em `app/services/ocorrencia_service.py:62-80`. GUT: campos `gut_gravidade`, `gut_urgencia` e `gut_tendencia` (`app/models/ocorrencia.py:41-43`), gravados como vieram, sem cálculo do produto G×U×T. A regra RN-04 (prioridade padrão derivada do CMM, em `estudo-do-contexto.md` §5) **não é aplicada**: `criar` repassa `dados.prioridade` sem derivar (`app/repositories/ocorrencia_repository.py`). | **Parcial** |
| Dashboard de saúde da edificação | `GET /api/v1/edificacoes/{id}/dashboard` (`app/api/v1/dashboard.py`), que calcula conformidade por sistema, grau de risco por sistema e média de gravidade GUT por subsistema (`app/services/edificacao_service.py:56`). Tela em `03_frontend/app/dashboard/page.tsx`. | **Conforme** |
| Portal do cliente | `app/api/v1/portal.py` (prefixo `/api/v1/portal`): edificações, dashboard, acompanhamento, lista de relatórios e URL pré-assinada de download, tudo escopado pelo contratante (`app/services/portal_service.py`). Telas em `03_frontend/app/portal/`. | **Conforme**, mas a lista de relatórios fica vazia na prática, porque nada no fluxo da API cria `Relatorio` (ver a linha de PDF/DOCX). |
| Não citado no objetivo | Legendas de fotos assistidas por IA (ADR-12, RF-15): `requirements.txt` não tem SDK de LLM e o bloqueio B-04 está aberto em `00_docs/projeto/status.md`. Fila assíncrona Celery/Redis (ADR-06): ausente de `requirements.txt` e `docker-compose.yml`; o docstring de `rfo_pipeline.py` declara "continua pendente". | Não implementado |

### 1.3 Quem usa

Os atores vêm de `00_docs/estudo-do-contexto.md` §3. Os perfis de acesso estão no código: `app/models/usuario.py:27` (`role`, padrão `auditor`), `app/api/deps.py:90-91` e `03_frontend/lib/use-usuario-atual.ts:7`.

| Perfil (`role`) | Ator | O que pode fazer (código) |
|---|---|---|
| `auditor` | Engenheiro fiscal (Garra) | Tudo. `require_auditor` protege criação de edificação, contrato, responsável e usuário (`tests/test_rbac_auxiliar.py`). |
| `auxiliar` | Auxiliar de campo | `require_equipe`: cria visitas, ocorrências e fotos, com autoria em `criado_por_id` (`app/models/ocorrencia.py`, migration `7c1a4e0b93d5_...bl_42.py`). Não cria cadastros-mestre. |
| `cliente` | Contratante, síndico ou administradora | Só o portal (`app/api/v1/portal.py`), escopado pelo `Responsavel` vinculado ao usuário (`get_current_cliente_responsavel` em `app/api/deps.py:94`). |

---

## 2. Entradas e saídas

**Entradas**

| Entrada | Por onde entra | Evidência |
|---|---|---|
| Credenciais (e-mail e senha) | `POST /api/v1/auth/login`, `POST /api/v1/auth/register` | `app/api/v1/auth.py` |
| Cadastros: edificação, contrato (com executoras, NBRs e ART), responsáveis | JSON na API REST | `app/api/v1/{edificacoes,contratos,responsaveis}.py`, `app/schemas/` |
| Documentos técnicos da edificação | `POST /api/v1/edificacoes/{id}/documentos` | `app/api/v1/edificacoes.py:80` |
| Visitas (equipe, serviços executados, medições, mão de obra) | `POST /api/v1/inspecoes/{id}/visitas`, `/visitas/{id}/mao-obra`, `/visitas/{id}/medicoes` | `app/api/v1/inspecoes.py:35`, `app/api/v1/visitas.py` |
| Ocorrências (sistema, subsistema, situação, classificação, CMM, GUT, prioridade) | `POST /api/v1/inspecoes/{id}/ocorrencias` | `app/api/v1/ocorrencias.py:45` |
| Fotos (JPEG, PNG ou WEBP; até 25 MB no storage) | multipart ou base64 (área de transferência / Lightshot) | `app/api/v1/fotos.py`, `app/services/image_processing.py`, `04_backend/README.md` (BL-07) |
| Gabarito (sistemas prediais, subsistemas, tipos de anomalia e falha, localizações) | seed a partir de `00_docs/convertidos/RFO_INSPECAO.md` | `app/scripts/rfo_gabarito_parser.py`, `app/scripts/seed_gabarito.py` |
| Originais do cliente (`.xlsm`, PDFs) | só nos scripts de build de template, nunca pela API | `app/scripts/build_rfo_templates.py`, `app/scripts/build_ltip_templates.py` |
| Configuração | variáveis de ambiente / `.env` | `app/core/config.py`, `04_backend/.env.example`, `05_infra/.env.example` |

**Saídas**

| Saída | Evidência |
|---|---|
| JSON REST com erros em RFC 7807 (`application/problem+json`) | `app/core/exception_handlers.py`, ADR-07 em `00_docs/arquitetura.md` |
| Token JWT (HS256, 60 min por padrão) | `app/core/security.py`, `app/core/config.py` |
| Objetos no MinIO/S3 (`fotos/<uuid>.<ext>`) e URLs pré-assinadas de 15 min | `app/services/foto_service.py:36-44`, `app/services/storage/s3_client.py` |
| Agregados do dashboard | `app/schemas/dashboard.py` |
| `GET /health` com estado do banco (`ok` ou `degraded`) | `app/main.py` |
| Templates `layout.json`, `.html.j2` e `.docx` (gerados por script) | `04_backend/templates/{rfo,ltip}/` |
| PDF e DOCX do RFO: **apenas por script** (benchmark), não pela API | `app/scripts/benchmark_relatorio_geracao.py`, `app/services/report_generator/rfo_pipeline.py` |
| Interface web | `03_frontend/app/` |

---

## 3. Componentes

| Caminho | Responsabilidade |
|---|---|
| `00_docs/` | Documentação: contexto (`estudo-do-contexto.md`), arquitetura e ADRs (`arquitetura.md`), gestão (`projeto/`), material do cliente (`cliente/`), originais convertidos para Markdown (`convertidos/`) |
| `01_output-context/` | Originais do cliente. Só `.md` e `README.md` são versionados; os binários ficam fora do git (commit `1831e21`; `ls 01_output-context` mostra 3 arquivos) |
| `02_prototipos/` | Protótipos HTML estáticos (`index.html`, `01-dashboard.html` … `06-laudo-preview.html`) |
| `03_frontend/app/` | Páginas Next.js (App Router): `(auth)/login`, `dashboard`, `edificacoes`, `contratos`, `inspecoes/[id]/{visitas,ocorrencias,relatorio}`, `portal/{,documentos}` |
| `03_frontend/components/` | UI shadcn (`ui/`), marca (`brand/`), layout (`layout/app-shell.tsx`, `nav-items.ts`), upload e anotação de foto, formulário de ocorrência |
| `03_frontend/lib/api-client.ts` | Cliente HTTP: base `NEXT_PUBLIC_API_URL` (padrão `http://localhost:8000/api/v1`), token JWT no `localStorage` |
| `03_frontend/lib/use-usuario-atual.ts` | Perfil do usuário logado, usado só para usabilidade (comentário na linha 20) |
| `03_frontend/e2e/` + `playwright.config.ts` | Testes E2E dos fluxos RFO e LTIP contra a stack local em execução |
| `04_backend/app/main.py` | App FastAPI: middlewares (segurança, request-id, CORS), handlers de erro, 11 routers, `/health`, migrations no boot opcionais |
| `04_backend/app/api/deps.py` | Autenticação (`get_current_user`) e RBAC (`require_role`, `require_auditor`, `require_equipe`, `get_current_cliente_responsavel`) |
| `04_backend/app/api/v1/*.py` | Rotas: `auth`, `dados_mestre`, `edificacoes`, `contratos`, `responsaveis`, `inspecoes`, `visitas`, `ocorrencias`, `fotos`, `dashboard`, `portal` |
| `04_backend/app/services/` | Regras de negócio por domínio (`*_service.py`), `image_processing.py`, `storage/` (interface `StorageClient` + `S3StorageClient`), `report_generator/rfo_pipeline.py` |
| `04_backend/app/repositories/` | Acesso a dados (contrato, edificação, foto, inspeção, ocorrência, visita) |
| `04_backend/app/models/` | 18 arquivos de modelo SQLAlchemy 2 async: as 14 entidades do ER, mais `Usuario`, `TipoAnomalia`, `TipoFalha` e `Localizacao` (`ls app/models`) |
| `04_backend/app/schemas/` | Schemas Pydantic v2 de request e response |
| `04_backend/app/core/` | `config.py` (Settings, com fail-closed em produção), `database.py`, `security.py`, `errors.py`, `exception_handlers.py`, `middleware.py`, `rate_limit.py` (em memória), `migrations.py` |
| `04_backend/app/scripts/` | Seeds (`seed_gabarito`, `seed_admin`, `seed_benchmark_rfo`), extratores de layout (`rfo_layout_extractor`, `ltip_layout_extractor`), builders de template, benchmark de geração |
| `04_backend/alembic/versions/` | 5 migrations: schema inicial, gabarito, usuário/JWT, role contratante (BL-30), autoria/auxiliar (BL-42) |
| `04_backend/templates/` | `rfo/` e `ltip/` (`layout.json` + `.html.j2` + `.docx` derivados), `contracts/`, além de `rfo_template.html.j2` e `rfo_benchmark_template.docx` na raiz da pasta |
| `04_backend/tests/` | 18 módulos pytest (integração contra Postgres e MinIO reais, mais templates com planilha/PDF sintéticos) |
| `05_infra/docker-compose.yml` | Dev: `postgres` (16-alpine, `127.0.0.1:5433`), `minio` (9000/9001), `createbuckets`, `backend` (8000), `frontend` (3000) |
| `05_infra/docker-compose.prod.yml`, `nginx/`, `backup/` | VPS alternativa: compose de produção, `nginx.conf`, `backup-db.sh` e `restore-db.sh` |
| `render.yaml` | Blueprint do Render: `garra-backend` (branch `main_back`), `garra-frontend` (`main_front`), banco `garra-db` |
| `.github/workflows/` | `ci.yml` (ruff, pytest, lint, build, Trivy, E2E), `cd-staging.yml` e `cd-production.yml` (VPS manual, fallback), `sync-deploy-branches.yml` |
| `.github/agents/`, `.github/prompts/` | Instruções de agentes por papel e prompts de tarefa |

---

## 4. Fluxo principal

Fluxo do RFO, que é o coberto por `03_frontend/e2e/rfo.spec.ts` e por `estudo-do-contexto.md` §8.

```text
[Navegador / PWA]
  1. Login ─ POST /api/v1/auth/login ─> JWT ─> localStorage (lib/api-client.ts)
  2. Edificação ─ POST /api/v1/edificacoes            (require_auditor)
  3. Contrato   ─ POST /api/v1/contratos  ─> cria a Inspecao junto (contrato_repository.py:74)
  4. Visita     ─ POST /api/v1/inspecoes/{id}/visitas (+ /mao-obra, /medicoes)  (require_equipe)
  5. Ocorrência ─ POST /api/v1/inspecoes/{id}/ocorrencias  ─ validação RN em ocorrencia_service._validar_payload
  6. Foto       ─ POST /api/v1/fotos/upload | /upload-clipboard
                    └─ Pillow verifica e recodifica, sem EXIF ─> MinIO "fotos/<uuid>" ─> URL pré-assinada
                ─ POST /api/v1/visitas/{id}/fotos | /ocorrencias/{id}/fotos  (vincula a foto ao registro)
  7. Dashboard  ─ GET /api/v1/edificacoes/{id}/dashboard ─> agrega as ocorrências (edificacao_service.obter_dashboard)
  8. Relatório  ─ tela /inspecoes/[id]/relatorio = PLACEHOLDER (não há rota de geração)
  9. Cliente    ─ GET /api/v1/portal/... (escopado pelo contratante) ─> download por URL pré-assinada,
                  se existir Relatorio com pdf_key/docx_key

[FastAPI] ─ SQLAlchemy async/asyncpg ─> PostgreSQL     [FastAPI] ─ boto3 ─> MinIO/S3
```

Fluxo de templates, fora da aplicação e sob responsabilidade do desenvolvedor (`04_backend/README.md`, seção BL-12/BL-13):

```text
original do cliente (.xlsm / PDF, fora do git)
  └─ rfo_layout_extractor.py (openpyxl, keep_vba=False) | ltip_layout_extractor.py (pdfplumber)
       └─ templates/<tipo>/layout.json (versionado, só geometria)
            ├─ <tipo>_template.html.j2 ─> WeasyPrint ─> PDF   (rfo_pipeline.gerar_pdf)
            └─ <tipo>_template.docx    ─> docxtpl    ─> DOCX  (rfo_pipeline.gerar_docx)
```

---

## 5. Como instalar, rodar e testar

### 5.1 Comandos documentados

- **Stack completa (Docker)**: a partir de `05_infra/`, `cp .env.example .env` (o compose exige `POSTGRES_PASSWORD`, `MINIO_ROOT_*` e `JWT_SECRET_KEY`, com `:?` em `docker-compose.yml`) e depois `docker compose up -d --build`. Fonte: `05_infra/README.md`, `04_backend/README.md`.
- **Backend local**: a partir de `04_backend/`, `python -m venv .venv`, `pip install -r requirements.txt`, `cp .env.example .env`, `alembic upgrade head`, `python -m app.scripts.seed_gabarito` e `uvicorn app.main:app --reload`. A documentação interativa fica em `/docs`, só com `ENVIRONMENT` de desenvolvimento (`app/main.py`).
- **Frontend local**: a partir de `03_frontend/`, `npm install` e `npm run dev` (porta 3000).
- **Testes**: `pytest` e `ruff check .` em `04_backend/`; `npm run lint`, `npm run build` e `npm run test:e2e` em `03_frontend/`. O E2E exige a stack no ar (`playwright.config.ts`). O CI roda o mesmo conjunto (`.github/workflows/ci.yml`).

### 5.2 Resultado da execução nesta tarefa (2026-10-28)

Ambiente: Windows 11; Python 3.12.4 do `.venv` da raiz do checkout principal; Node v26.7.0; npm 11.19.0; ruff 0.15.1. O comando `docker` não existe no PATH (bash `docker: command not found`; PowerShell `Get-Command docker` vazio).

| Verificação | Resultado |
|---|---|
| PostgreSQL do compose (`localhost:5433`) | **Fora do ar** (`Test-NetConnection -Port 5433` → `False`) |
| MinIO (`localhost:9000`) | **Fora do ar** (`Test-NetConnection -Port 9000` → `False`) |
| `pytest` (04_backend) | **Não rodou de forma válida.** Ver o detalhamento abaixo. |
| `ruff check .` (04_backend) | **201 erros**, mas usando um `pyproject.toml` externo ao repositório (`Settings path: C:\Users\dynatest\OneDrive - Dynatest Engenharia\pyproject.toml`, segundo `ruff check . --show-settings`). Com `ruff check . --isolated` (regras padrão, como num CI sem config): **47 erros**, sendo 38 F821 nos modelos (`app/models/*.py`, nomes de anotação entre aspas sem `TYPE_CHECKING`), 8 F401 (imports não usados, 5 deles em `app/repositories/ocorrencia_repository.py`) e 1 F541 (`tests/test_ltip_templates.py`). |
| `npm ci` (03_frontend, no worktree) | exit 0. Avisos de pacotes deprecados (`eslint@8.57.1`, `glob@10.3.10`, `tar@6.2.1`) e um script de instalação não liberado (`unrs-resolver@1.12.2`) |
| `npm run lint` (03_frontend) | **OK**: `✔ No ESLint warnings or errors` (exit 0) |
| `npm run build` (03_frontend) | **OK**: `✓ Compiled successfully`, 13 rotas na tabela do `next build`, First Load JS compartilhado de 87,4 kB (exit 0) |
| `npm run test:e2e` (03_frontend) | **Não rodou**: exige a stack do compose no ar (`playwright.config.ts`) |

Detalhamento do `pytest`:

1. `python -m pytest -q`: a coleta foi interrompida com **2 erros**. Faltam `openpyxl` (`tests/test_rfo_templates.py`) e `pdfplumber` (`tests/test_ltip_templates.py`) no venv usado, embora os dois estejam em `requirements.txt`. Nenhuma dependência foi instalada, porque o venv é compartilhado com o checkout principal.
2. `python -m pytest -q --ignore=tests/test_ltip_templates.py --ignore=tests/test_rfo_templates.py -rA --tb=line`: **11 passed, 2 failed, 80 errors**.
   - Os 80 erros e as 2 falhas (`test_seguranca.py::test_login_bloqueia_apos_tentativas_malsucedidas_consecutivas` e `test_registro_publico_bloqueado_quando_ja_existem_usuarios`) vêm de infraestrutura ausente: `botocore.exceptions.EndpointConnectionError` no MinIO (`test_storage.py`) e `UndefinedTableError` no banco.
   - Sem `.env` e sem variáveis `POSTGRES_*`, o `Settings` usa a porta padrão **5432** (`app/core/config.py`), e não a 5433 do compose. Nessa porta responde um serviço Windows **`postgresql-x64-17`** (Running), alheio ao projeto e sem o schema. As migrations **não** foram aplicadas nele, para não alterar um banco de terceiros.
   - Os 11 que passaram não dependem de tabela: `test_health` (1), `test_auth` (2, sem token e com token inválido), `test_edificacoes` (1), `test_responsaveis` (1, 401 sem auth) e `test_seguranca` (6: cabeçalhos, request-id, fail-closed de `Settings` e contador de login).
   - Total de testes do backend: 93 nos 16 módulos coletados, mais 21 nos dois ignorados (11 LTIP e 10 RFO, por `grep -c "def test_"`).
3. Para rodar de forma válida: subir `05_infra/docker-compose.yml` (`docker compose up -d postgres minio createbuckets`), criar `04_backend/.env` com `POSTGRES_PORT=5433`, rodar `alembic upgrade head` e `python -m app.scripts.seed_gabarito`, e por fim `pytest`.

---

## 6. Dependências e serviços externos

**Backend** (`04_backend/requirements.txt`): FastAPI, Uvicorn, SQLAlchemy 2 async, asyncpg, Alembic, Pydantic v2, pydantic-settings, python-jose (JWT), passlib + bcrypt `<4.1` (fixado por incompatibilidade, conforme comentário no arquivo), boto3, WeasyPrint `>=69`, docxtpl + docxcompose, Jinja2, openpyxl, pdfplumber, pypdf, Pillow, python-multipart; para testes, pytest `>=9.1.1`, pytest-asyncio e httpx. O `ruff` **não** está em `requirements.txt`; o CI o instala à parte (`.github/workflows/ci.yml`, passo "Instalar dependências"). O WeasyPrint exige bibliotecas GTK que não existem no Windows local (`04_backend/README.md`).

**Frontend** (`03_frontend/package.json`): Next.js 14.2.35, React 18, Radix UI, Tailwind 3 + tailwindcss-animate, class-variance-authority, lucide-react e Fabric.js 6 (anotação de foto); em desenvolvimento, Playwright, ESLint 8 e TypeScript 5.

**Serviços**

| Serviço | Uso | Onde |
|---|---|---|
| PostgreSQL 16 | Banco principal | `05_infra/docker-compose.yml`; `garra-db` em `render.yaml` |
| MinIO / S3 | Fotos e arquivos de relatório | `docker-compose.yml`; `app/services/storage/s3_client.py` |
| Render | Hospedagem de produção (Blueprint) | `render.yaml`; `05_infra/.env.render.example` |
| GHCR + VPS via SSH | Deploy alternativo (manual) | `.github/workflows/cd-*.yml` |
| GitHub Actions + Dependabot + Trivy | CI, atualização de dependências e scan de imagem | `.github/workflows/ci.yml`, `.github/dependabot.yml` |
| Provedor de LLM | **Não determinado**: nenhum escolhido (bloqueio B-04 em `00_docs/projeto/status.md`) | — |

---

## 7. Riscos e lacunas visíveis no código

| # | Risco ou lacuna | Evidência | Impacto |
|---|---|---|---|
| 1 | Geração de relatório não exposta ao usuário: sem endpoint, sem job, tela placeholder | §1.2; `app/api/v1/` sem rota de relatório; `03_frontend/app/inspecoes/[id]/relatorio/page.tsx` | Principal entrega do objetivo indisponível no produto |
| 2 | Pipeline de renderização só para o RFO; o LTIP tem templates sem renderizador; não há RFIP | `app/services/report_generator/__init__.py` exporta só `rfo_pipeline` | Escopo parcial |
| 3 | `render.yaml` não define nenhuma variável `MINIO_*` para o `garra-backend`; os padrões de `Settings` apontam para `localhost:9000` com credenciais vazias | `render.yaml` (envVars do backend); `app/core/config.py`; `05_infra/.env.render.example:36-41` (vazios) | Upload e download de fotos em produção devem falhar. O comportamento real em produção é **não determinado** (não foi testado) |
| 4 | Divergência de porta: `04_backend/.env.example` e `Settings` usam `POSTGRES_PORT=5432`, mas o compose publica `5433` | `04_backend/.env.example`; `05_infra/docker-compose.yml` | Testes e app locais conectam no banco errado (aconteceu nesta tarefa, §5.2) |
| 5 | Registro público liberado enquanto não há usuários: o primeiro a chamar `/auth/register` vira `auditor` | `app/api/v1/auth.py:39` e `:54` | Num banco de produção vazio, quem chegar primeiro toma a conta administrativa |
| 6 | `seed_admin` tem senha padrão embutida (`Admin@Garra123`) quando `ADMIN_SENHA` não é definida | `app/scripts/seed_admin.py:57` | Credencial previsível se o seed rodar sem variável |
| 7 | Rate limit de login em memória do processo | `app/core/rate_limit.py:1-20` | Perde o estado a cada restart e não vale entre réplicas |
| 8 | JWT guardado em `localStorage` | `03_frontend/lib/api-client.ts:58-70` | Exposto a XSS; não há cookie httpOnly |
| 9 | RN-04 (prioridade derivada do CMM) e produto GUT não implementados | `app/services/ocorrencia_service.py`, `app/repositories/ocorrencia_repository.py` | Classificação depende de preenchimento manual |
| 10 | Fila assíncrona (ADR-06) e legendas por IA (ADR-12) ausentes | `requirements.txt`; docstring de `rfo_pipeline.py` | Geração síncrona; RF-15 bloqueado |
| 11 | `ruff check --isolated` com 47 erros (38 F821 nos modelos) | §5.2; `.github/workflows/ci.yml:78-82` (comentário: "Lint ainda não é bloqueante") | O lint do backend não barra merge; a dívida se acumula. O resultado nos logs do Actions é **não determinado** |
| 12 | `03_frontend` usa `NEXT_PUBLIC_API_URL`, mas não tem `.env.example` | `ls -a 03_frontend`; `lib/api-client.ts:13` | Configuração do frontend só documentada no compose e no `render.yaml` |
| 13 | `playwright.config.ts` remete a `03_frontend/e2e/README.md`, que não existe | `ls 03_frontend/e2e` | Referência quebrada |
| 14 | Os testes E2E validam o placeholder do relatório, e não a geração | `03_frontend/e2e/rfo.spec.ts` (comentário inicial) | Cobertura E2E não protege o objetivo central |
| 15 | Os originais do cliente não estão no git; `build_*_templates --original` depende de arquivos locais | commit `1831e21`; `ls 01_output-context` | Regerar o layout exige a máquina de quem tem os originais (o modo sem `--original` funciona a partir do `layout.json`) |
| 16 | `04_backend/README.md` está desatualizado em partes: a árvore lista 3 migrations (são 5) e 5 testes (são 18), e o texto ainda diz que a geração "depende da entrega dos modelos originais", embora o ADR-13 tenha removido essa dependência | `04_backend/README.md` vs `ls alembic/versions tests` | Fica para a D03 classificar |
| 17 | Sem `README.md` na raiz do repositório e sem índice em `00_docs/README.md` | `ls` na raiz e em `00_docs` | Previsto na D04 do `BACKLOG.md` |
| 18 | Dois templates soltos fora das pastas por tipo (`templates/rfo_template.html.j2`, `templates/rfo_benchmark_template.docx`) | `ls 04_backend/templates` | Origem e uso exatos: **não determinado** (provável legado do benchmark BL-22) |
| 19 | Produção no Render com banco desconectado registrada como parcialmente resolvida | `00_docs/projeto/status.md` (achado de 2026-08-05, HT-04) | Situação atual: **não determinado** (não foi consultada) |

### Decisões propostas (não aplicadas; cabem ao fechamento de lote)

- **Proposta P-01**: alinhar `POSTGRES_PORT=5433` em `04_backend/.env.example` com a porta publicada pelo compose (risco 4).
- **Proposta P-02**: incluir `ruff` em `requirements.txt` (ou num `requirements-dev.txt`) e criar um `pyproject.toml`/`ruff.toml` em `04_backend/`, para que o resultado não dependa de config externa ao repositório (risco 11).
- **Proposta P-03**: acrescentar ao `render.yaml` as variáveis `MINIO_*` (ou de um S3 gerenciado) do backend (risco 3).

---

## Registro da tarefa

- Arquivo alterado: só este (`00_docs/_preparo/01_sistema.md`). Nenhum código, teste ou dado foi tocado. `BACKLOG.md`, `PROGRESSO.md` e os documentos de gestão de `00_docs/projeto/` não foram editados.
- Regra de pronto do `BACKLOG.md`: item 1 não se aplica (a tarefa não tem código); item 2 está atendido por este documento (fatos, caminhos, comandos e saídas); itens 3 e 4 foram respeitados.
