# Variáveis de ambiente da emissão de relatórios (DEC-48) — auditoria de deploy

**Tarefa:** T47 · **Decisão de referência:** DEC-48 (P5, teto de 200 MB) · **Papel:** DevOps · **Branch:** `worktree-backlog-T47`

## Resultado

**Nenhuma variável de ambiente nova foi introduzida pela emissão de relatórios (T46 / BL-13).** Não há campo novo em `Settings` nem variável para repassar ao deploy. Nenhum arquivo de infra foi alterado.

O teto por arquivo é uma **constante de módulo**, não lida do ambiente:

- `04_backend/app/services/relatorio_service.py:37` → `MAX_RELATORIO_SIZE_BYTES = 200 * 1024 * 1024`
- `relatorio_service.py:158` → passado como `max_size_bytes=` em `storage.upload(...)`

Isso bate com a DEC-48 P5 ("Teto de 200 MB por arquivo, a revisar com o benchmark de 200 páginas"), que não pede configuração por ambiente.

## Variáveis encontradas

| Variável | Origem | Existia antes? | Ação |
|---|---|---|---|
| `MAX_RELATORIO_SIZE_BYTES` | constante em `relatorio_service.py`, não env | n/a (não é env) | nenhuma |
| `RELATORIO_MAX_UPLOAD_SIZE_BYTES` | `04_backend/app/scripts/benchmark_relatorio_geracao.py:46` (script de benchmark, 150 MB, local ao script) | n/a | nenhuma; não é variável de ambiente |

Busca feita: `grep` por `MAX_RELATORIO`, `RELATORIO_` e campos de `Settings` em `04_backend`, `05_infra`, `render.yaml` e `00_docs`.

## Verificação de infra (sem alterações)

- `05_infra/.env.example`, `04_backend/.env.example`, `05_infra/docker-compose.yml`, `05_infra/docker-compose.prod.yml` e `render.yaml`: nenhuma referência a `MAX_RELATORIO` ou a campos de relatório.
- Não foi necessário adicionar comentários nem valores padrão.

## Divergência de base (registrar para o integrador)

A T46 está na `main` (commit `92a0d08`, merge `b83514e`), mas o branch `worktree-backlog-T47` foi criado antes dela (base `14ead2f`). Por isso a auditoria foi feita com `git show main:...` e `git grep ... main`, sem alterar o histórico deste branch.

Ao comparar com a `main`, há mudanças de infra que **ainda não estão neste branch**, do trabalho de Legenda por IA (T40, DEC-42 C):

- `05_infra/docker-compose.yml`, `05_infra/docker-compose.prod.yml` e `render.yaml` repassam `LEGENDA_IA_*` ao serviço `backend` na `main`.
- `04_backend/app/core/config.py` tem os campos `legenda_ia_*` na `main`.

Ao integrar, o merge com a `main` traz essas mudanças. Não foram recriadas aqui para não duplicar trabalho.

## Comandos e saída

```text
$ docker compose -f docker-compose.yml config
bash: line 1: docker: command not found   (Docker não instalado neste ambiente)

$ docker compose -f docker-compose.prod.yml config
bash: line 1: docker: command not found   (não executado)
```

Como não há alteração em código nem em compose, `pytest` e `ruff check .` (04_backend) e `npm run lint` / `npm run build` (03_frontend) não foram executados: a parte tocada é só esta documentação.

## Decisão proposta (não aplicada)

- **P-T47-1:** manter `MAX_RELATORIO_SIZE_BYTES` como constante (estado atual, sem mudança). Alternativa: ler de `Settings` (`MAX_RELATORIO_SIZE_BYTES`, default 200 MB) e expor no `.env.example` e nos compose, caso o benchmark de 200 páginas (DEC-48 P5) mude o teto e o ajuste precise ser feito sem rebuild. Decisão do integrador; não registrada em `decisoes.md` nesta tarefa.
