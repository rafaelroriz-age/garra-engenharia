# Limpeza de lint do backend (DEC-46 / T39)

Tarefa de lote: reduzir os achados de `ruff check .` em `04_backend` e fixar a versão do ruff no CI.
Status ao final desta execução: **parcial**. Os achados listados na DEC-46 foram zerados, mas o `ruff check .` ainda reporta achados de outras regras (ver "Pendências"). Testes **não rodaram** (PostgreSQL de `localhost:5433` estava fechado).

## Achados: antes e depois

Medição com o mesmo ruff local (**0.15.1**) e a mesma configuração auto-descoberta, comando `ruff check . --statistics` a partir de `04_backend`.

| Momento | Total | Observação |
|---|---|---|
| Antes (HEAD, início da tarefa) | 214 | Inclui os 11 citados na DEC-46 e outros que não estavam listados |
| Depois (esta worktree) | 152 | 62 a menos |

Achados restantes depois da execução:

| Regra | Qtd | Corrigível automaticamente | Situação |
|---|---|---|---|
| B008 | 87 | não | `Depends()`/`Query()`/`File()` em valor padrão de parâmetro (idioma do FastAPI). Exige decisão de configuração |
| F821 | 38 | não | nomes de modelos em anotações string (`"Contrato"` etc.) sem import visível para o ruff |
| F401 | 20 | sim (não aplicado) | imports não usados; alguns em `app/models`/repositórios podem existir só por efeito colateral de registro do SQLAlchemy. Não removidos sem revisão |
| B905 | 4 | não | `zip()` sem `strict=` (mudaria comportamento se os tamanhos diferirem) |
| RUF007 | 2 | não | sugestão de `itertools.pairwise()` |
| UP046 | 1 | não | `PaginatedResponse` com `Generic` (`app/schemas/common.py`) |

Regras zeradas nesta execução: I001, UP007, UP035, UP017, RUF022, RUF100, RUF005, RUF003, F541 (e os RUF001/RUF043 citados na DEC-46 não apareceram nesta versão do ruff).

## Arquivos alterados

- Fixes automáticos seguros (`ruff check . --fix --select I001,UP007,UP035,UP017,RUF022,F541`): 78 correções em `04_backend/alembic/`, `04_backend/app/` e `04_backend/tests/`. Foram só reordenação de imports, anotações `X | Y`, `datetime.UTC`, ordenação de `__all__` e remoção de f-string sem placeholder.
- Manuais:
  - `04_backend/app/scripts/bitmap_tracer.py`: `rotacionado + [rotacionado[0]]` virou `[*rotacionado, rotacionado[0]]` (RUF005, mesmo comportamento).
  - `04_backend/app/scripts/ltip_layout_extractor.py`: comentário com travessão mantido por ser texto literal do modelo do cliente; `# noqa: RUF003` com justificativa (RUF003).
  - `04_backend/app/main.py` e `04_backend/app/scripts/benchmark_relatorio_geracao.py`: removido `noqa: BLE001` não usado (RUF100); o comentário explicativo foi mantido.
- `.github/workflows/ci.yml`: `pip install ruff` virou `pip install ruff==0.15.1`. `continue-on-error: true` do passo de lint **mantido**.

Conferido: `py_compile` em todos os arquivos Python alterados (OK). Diffs de import revisados em `main.py`, `conftest.py`, `alembic/env.py` e `storage/__init__.py`: só ordem, sem efeito colateral de import.

## Versão fixada

- ruff **0.15.1** (`ruff --version` local). A DEC-46 citava 0.17.3, mas essa versão não é a usada localmente; prevaleceu a versão local, como pede a tarefa.

## Testes

- `pytest`: **não rodou**. `localhost:5433` (PostgreSQL de `05_infra/docker-compose.yml`) estava fechado no momento da execução. Nada foi subido nem derrubado.
- `ruff check .`: roda, com 152 achados (ver tabela). Não zera.

## Achados de configuração (importante)

- **Não existe `04_backend/ruff.toml`.** A tarefa e a DEC-46 citam esse arquivo, mas ele não está no repositório.
- O ruff local usa `C:\Users\dynatest\OneDrive - Dynatest Engenharia\pyproject.toml`, que fica **fora do repositório**. Por isso o ruff local acusa regras como B008, UP e I001 que um checkout limpo não vê.
- Consequência: no CI (checkout limpo, sem essa configuração) o ruff roda só com as regras padrão (E4/E7/E9/F). Pela medição com o diretório do HEAD exportado e sem configuração, o total era 46 (F821 38, F401 7, F541 1). Após esta execução, com as regras padrão, sobram cerca de 45 (F821 38, F401 7); o F541 foi corrigido.
- Ou seja: o número de achados que o CI vê é diferente do que o ruff local mostra. A limpeza real depende de a configuração ser versionada.

## Pendências para o dono (não resolvidas aqui)

1. **Remover `continue-on-error: true`** do passo de lint em `.github/workflows/ci.yml` e tornar o status check obrigatório. Depende da aprovação da DEC-46. Só faz sentido depois que o ruff zerar com a configuração versionada.
2. **Versionar a configuração do ruff dentro do repositório** (ex.: `04_backend/ruff.toml` ou `pyproject.toml` em `04_backend`). Sem isso, CI e máquina local aplicam regras diferentes. Decisão proposta para a DEC-46: definir o conjunto de regras oficial e onde ele fica.
3. **B008 (87):** decidir se o padrão FastAPI `Depends()` em defaults é aceito. Proposta: ignorar B008 para `app/api/**` na configuração versionada, em vez de 87 `noqa`.
4. **F821 (38):** modelos com anotações string dependem de import em `TYPE_CHECKING` ou de `from __future__`. Mudança em `app/models/`; precisa de revisão e de testes de mapeamento do SQLAlchemy antes de mexer.
5. **F401 (20):** revisar caso a caso; alguns imports em `app/models` e em repositórios podem ser necessários para registrar mapeamentos.
6. **B905 (4), RUF007 (2), UP046 (1):** decidir se entram na limpeza; B905 muda comportamento se `strict=True` for aplicado a listas de tamanhos diferentes.
7. **Testes:** rodar `pytest` com o PostgreSQL no ar para confirmar que os fixes de import não quebraram nada. Não feito nesta execução.

## Decisões propostas (para o integrador levar à DEC-46)

- Configuração do ruff versionada em `04_backend` (não fora do repositório).
- Ruff fixado em 0.15.1 no CI até a próxima revisão deliberada (versão igual à local).
- Ignorar B008 em `app/api/**`, com justificativa de idioma FastAPI.
