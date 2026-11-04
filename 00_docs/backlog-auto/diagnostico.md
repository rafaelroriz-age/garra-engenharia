# Diagnóstico do ambiente — T01

- **Tarefa:** T01 (diagnóstico do ambiente de desenvolvimento)
- **Data:** 2026-11-04
- **Branch/worktree:** `worktree-backlog-T01`
- **Escopo:** somente leitura de código. Nenhum arquivo de código foi alterado. Foram instaladas dependências locais (`04_backend/.venv` e `03_frontend/node_modules`, ambos ignorados pelo git).

## 1. Versões de ferramentas

| Ferramenta | Versão encontrada | Esperado pelo projeto | Observação |
|---|---|---|---|
| Python (sistema, `python` do Anaconda) | 3.14.6 | 3.12 (`04_backend/README.md`) | Python 3.14 não serve: `pillow==10.4.0` (faixa `>=10.3,<11.0`) não tem wheel e falha ao compilar. |
| Python (venv `04_backend/.venv`) | 3.12.4 | 3.12 | Criado com `uv venv --python 3.12`. Dependências de `requirements.txt` instaladas com sucesso. |
| Node.js | v26.7.0 | 14+ (Next 14) | Funciona para `npm ci` e `npm run lint`. |
| npm | 11.19.0 | — | — |
| Docker | **não instalado** (`docker: command not found` no Bash e no PowerShell) | Docker Desktop (`05_infra/README.md`) | Impede subir PostgreSQL e MinIO nesta máquina. |

Pacotes relevantes no venv 3.12: pytest 9.2.0, pytest-asyncio 0.23.3, fastapi 0.162.0, sqlalchemy 2.1.8, asyncpg 0.32.0. ruff 0.15.1 vem do Anaconda (`C:\Users\dynatest\anaconda3\Scripts\ruff.exe`), não do venv.

## 2. Serviços de infraestrutura (`05_infra/docker-compose.yml`)

- `docker compose ps` **não foi executado**: o binário `docker` não existe nesta máquina.
- Verificação por porta (PowerShell `Test-NetConnection`, localhost):
  - `5433` (PostgreSQL): **fechada**
  - `9000` (MinIO API): **fechada**
- Conclusão: **PostgreSQL e MinIO não estão no ar.** Nenhum serviço foi subido ou derrubado.

## 3. Resultados dos comandos de verificação

### 3.1 Backend — `pytest -q` (em `04_backend`, com `.venv`)

- Resultado: **falha na coleta (INTERNALERROR), 0 testes executados**, exit code 3.
- Erro: `AttributeError: 'Package' object has no attribute 'obj'` (dentro de `pytest_asyncio/plugin.py`, `pytest_collectstart`).
- Causa provável (não verificada por teste isolado): incompatibilidade entre `pytest` 9.2.0 (aceito por `pytest>=9.1.1,<10.0`) e `pytest-asyncio` 0.23.3 (aceito por `pytest-asyncio>=0.23,<1.0`). A versão 0.23 não suporta a API de coleta do pytest 9. Os intervalos do `requirements.txt` permitem essa combinação.
- Observação: mesmo com a coleta corrigida, os testes de `test_models.py`, `test_gabarito.py`, `test_auth.py` e `test_storage.py` dependem de PostgreSQL e/ou MinIO no ar (`04_backend/README.md`). Sem Docker, esses testes não podem passar nesta máquina.
- **Não rodado com resultado válido:** a suíte completa. Nenhum número de testes passou/falhou foi obtido.

### 3.2 Backend — `ruff check .` (em `04_backend`)

- `ruff` do venv não estava instalado. Usado `ruff 0.15.1` do Anaconda.
- Resultado: **falha, 214 erros** (exit code 1). Resumo por regra (`ruff check . --statistics`):

| Regra | Qtd | Corrigível (`--fix`) | Descrição |
|---|---|---|---|
| B008 | 87 | não | `Depends(...)` em valor padrão de argumento (padrão FastAPI; provavelmente regra não adotada pelo projeto) |
| F821 | 38 | não | nome indefinido — ver nota abaixo |
| I001 | 36 | sim | imports desordenados |
| UP007 | 18 | sim | `Union[...]` em vez de `X \| Y` |
| UP017 | 8 | sim | `datetime.timezone.utc` em vez de `datetime.UTC` |
| F401 | 7 | sim | import não usado |
| UP035 | 6 | sim | import deprecated (`typing.Sequence`) |
| B905 | 4 | não | `zip()` sem `strict=` |
| RUF007 | 2 | não | `zip` em vez de `pairwise` |
| RUF022 | 2 | sim | `__all__` desordenado |
| RUF100 | 2 | sim | `noqa` não usado |
| F541 | 1 | sim | f-string sem placeholder |
| RUF003 / RUF005 / UP046 | 1 cada | não | diversos |

- Nota sobre F821: as ocorrências estão em anotações de relacionamento dos modelos em `04_backend/app/models/` (ex.: `Visita`, `Foto`, `Contrato`, `Responsavel`). O padrão sugere referências a classes importadas só sob `TYPE_CHECKING`, o que seria falso positivo. **Não verificado.** Não foi confirmado se algum desses nomes falha em tempo de execução.
- Nota sobre B008: `Depends` em argumentos padrão é o padrão idiomático do FastAPI. Se a regra estiver ativa na configuração do projeto, a CI (`.github/workflows/ci.yml`, step `ruff check .`) falharia nesta base.
- O CI (`.github/workflows/ci.yml`) instala ruff via `pip install ruff` (versão mais recente), o que pode produzir resultado diferente do ruff 0.15.1 usado aqui. Não comparado.

### 3.3 Frontend — `npm run lint` (em `03_frontend`)

- `npm ci` concluído com exit 0. Aviso: 30 vulnerabilidades reportadas pelo `npm audit` (17 moderadas, 11 altas, 2 críticas). Não tratado nesta tarefa.
- `npm run lint` (`next lint`): **passou**. Saída: `✔ No ESLint warnings or errors`. Exit 0.

## 4. Pendências e recomendações

1. **Docker** precisa estar instalado para rodar PostgreSQL/MinIO e a suíte de backend completa.
2. **Python 3.12** precisa ser o interpretador do venv do backend. O Python 3.14 do sistema não instala as dependências.
3. **Alinhar pytest e pytest-asyncio** (ex.: fixar `pytest<9` ou subir `pytest-asyncio` para versão compatível com pytest 9). Proposta de decisão: registrar em `00_docs/projeto/decisoes.md` via integrador, não editar diretamente.
4. **Limpar ruff**: decidir se a regra B008 está ativa (configuração do ruff não encontrada em `04_backend/` nem na raiz) e rodar `ruff check . --fix` nas regras corrigíveis. Investigar F821 antes de qualquer alteração.
5. **Vulnerabilidades do npm** (30): avaliar `npm audit` em tarefa própria.

## 5. Comandos executados (resumo)

```text
python --version                                  -> Python 3.14.6
node --version / npm --version                    -> v26.7.0 / 11.19.0
docker --version                                  -> não encontrado
uv venv --python 3.12 .venv                       (04_backend) -> Python 3.12.4
uv pip install -p .venv/Scripts/python.exe -r requirements.txt  -> OK
.venv/Scripts/python.exe -m pytest -q             -> INTERNALERROR (exit 3), 0 testes
ruff check . (anaconda ruff 0.15.1)               -> 214 erros (exit 1)
npm ci (03_frontend)                              -> OK (30 vulnerabilidades reportadas)
npm run lint (03_frontend)                        -> OK, sem avisos (exit 0)
Test-NetConnection localhost:5433 / :9000         -> fechadas
```
