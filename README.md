# Garra Engenharia — Automação de Relatórios Prediais

## Objetivo

Sistema web (PWA) da Garra Engenharia que automatiza a produção de relatórios técnicos de engenharia predial (RFO, LTIP e relatório fotográfico): o engenheiro registra edificações, contratos, visitas e ocorrências com fotos pelo celular e gera PDF e DOCX fiéis aos modelos do cliente, com classificação de anomalias (CMM/GUT), dashboard de saúde da edificação e portal do cliente.

O problema que ele resolve é a produção manual desses documentos a partir de planilhas XLSM e Word (`00_docs/estudo-do-contexto.md` §1).

**Estado atual (2026-11-03).** Já funcionam: login com os perfis `auditor`, `auxiliar` e `cliente`; cadastros de edificação, contrato e responsáveis; visitas, ocorrências com grau de risco CMM e prioridade sugerida (RN-04), notas GUT e fotos com anotação; dashboard da edificação; portal do cliente. **Ainda não funciona:** gerar o PDF/DOCX pela interface. Não há rota de geração na API e a tela de relatório é um placeholder. Os templates do RFO e do LTIP já são derivados dos originais do cliente, mas só o RFO tem renderizador (`rfo_pipeline.py`), e ele só é chamado por script. O relatório fotográfico (RFIP) não tem template próprio. Detalhes e evidências em [00_docs/arquitetura.md](00_docs/arquitetura.md) §0.

## Documentação

**Índice completo: [00_docs/README.md](00_docs/README.md).** Pontos de partida:

- [Guia de desenvolvimento](00_docs/guia-desenvolvimento.md): instalar, rodar e testar.
- [Arquitetura](00_docs/arquitetura.md) e [dicionário de dados](00_docs/dicionario-de-dados.md).
- [Configuração](00_docs/configuracao.md): variáveis de ambiente.
- [Guia de contribuição](00_docs/guia-contribuicao.md): branches, commits e PR.
- [Requisitos](00_docs/estudo-do-contexto.md) e [decisões](00_docs/projeto/decisoes.md).

## Pastas

| Pasta | Conteúdo |
|---|---|
| `00_docs/` | documentação ([índice](00_docs/README.md)) |
| `01_output-context/` | originais do cliente: fonte dos templates, **não alterar** (binários fora do git) |
| `02_prototipos/` | protótipos HTML estáticos das telas |
| `03_frontend/` | Next.js 14 (App Router, PWA) — [README](03_frontend/README.md) |
| `04_backend/` | FastAPI, SQLAlchemy 2 async, Alembic, WeasyPrint, docxtpl — [README](04_backend/README.md) |
| `05_infra/` | Docker Compose (PostgreSQL, MinIO, backend, frontend), Nginx, backup — [README](05_infra/README.md) |
| `.github/` | CI/CD (`workflows/`), template de PR, instruções de agentes e prompts |
| `backlog-auto/`, `BACKLOG.md`, `backlog.toml` | backlog executável por sessões automáticas ([manual](00_docs/backlog-auto/BACKLOG-MANUAL.md)) |
| `render.yaml` | Blueprint de produção no Render (`garra-backend`, `garra-frontend`, `garra-db`) |

Não se criam pastas novas na raiz (DEC-09).

## Início rápido

Requer Docker, Python 3.12 e Node 20. A sequência completa e os problemas conhecidos estão no [guia de desenvolvimento](00_docs/guia-desenvolvimento.md).

```powershell
cd 05_infra
Copy-Item .env.example .env          # troque as senhas
docker compose up -d postgres minio createbuckets

cd ..\04_backend
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env          # ajuste POSTGRES_PORT=5433
alembic upgrade head
python -m app.scripts.seed_gabarito
$env:ADMIN_SENHA = "<senha forte>"; python -m app.scripts.seed_admin   # primeiro usuário (auditor)
uvicorn app.main:app --reload        # http://localhost:8000

cd ..\03_frontend
npm install
npm run dev                          # http://localhost:3000
```

Testes: `pytest` e `ruff check .` em `04_backend/`; `npm run lint`, `npm run build` e `npm run test:e2e` em `03_frontend/`.
