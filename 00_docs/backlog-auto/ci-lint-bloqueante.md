# BL-26 — Lint do backend bloqueante no CI (proposta da T04)

## Resultado

**Não aplicado.** `ruff check .` em `04_backend`, com a versão de ruff usada na T04 (0.17.3) e a config versionada em `04_backend/ruff.toml`, acusa **11 erros** no estado atual do `main`. Pelo passo 4 da tarefa, o passo «Lint (ruff)» não foi tornado bloqueante e `.github/workflows/ci.yml` ficou **inalterado**. Nenhum código foi corrigido nesta tarefa.

## Por que os erros aparecem agora

A T04 (commit `1999f9e`, `chore(backend): configura ruff e zera 214 erros de lint (DEC-31)`) deixou `ruff check .` limpo na época. Depois disso entraram commits com arquivos novos que não passam nas regras selecionadas (`E, F, I, B, UP, RUF`). Os erros estão nos arquivos novos das vistorias cautelar e residencial e nos testes novos de legenda IA e fotos:

| Regra | Qtde | Arquivo:linha |
|---|---|---|
| RUF001 | 2 | `app/scripts/vistoria_cautelar_layout_extractor.py:81`, `:86` (travessão/en dash em regex) |
| I001 | 4 | `tests/test_foto_origem_enum.py:8`, `tests/test_ocorrencias_regras.py:6`, `tests/test_storage_legenda_ia.py:3`, `tests/test_vistoria_cautelar_templates.py:11` |
| RUF043 | 2 | `tests/test_vistoria_cautelar_pipeline.py:133`, `:163` (`match=` sem `re.escape`/raw string) |
| RUF005 | 3 | `tests/test_vistoria_cautelar_templates.py:219`, `:228`, `:290` (concatenação de listas) |
| **Total** | **11** | |

Parte deles é corrigível com `--fix` (4 seguras); RUF005 e RUF043 pedem correções manuais ou `--unsafe-fixes`. Isso fica para uma tarefa própria de limpeza, para não misturar com a mudança de CI.

## Versão do ruff

- `ruff.md` registra **ruff 0.17.3** como versão da T04.
- Ruff global desta máquina: **0.15.1** (`ruff --version` a partir de `04_backend`). Não usado para a decisão.
- Não existe `04_backend/.venv` neste worktree. Para reproduzir, instalei **ruff==0.17.3** num venv temporário fora do repositório (`$CLAUDE_JOB_DIR/tmp/ruffvenv`).
- **Versão a fixar no CI, quando o passo for tornado bloqueante: `ruff==0.17.3`** (`pip install "ruff==0.17.3"` no lugar de `pip install ruff`, linha 77 de `ci.yml`).

## Comandos e saídas

Versão (venv temporário):

```text
$ ruff --version
ruff 0.17.3
```

Lint, a partir de `04_backend`:

```text
$ ruff check .
Found 11 errors.
[*] 4 fixable with `--fix` (3 unsafe fixes available with `--fix --unsafe-fixes`).
exit=1
```

Validação do YAML, a partir da raiz (arquivo sem alteração):

```text
$ python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
YAML OK
```

## Passo do CI: antes e depois (proposta, não aplicada)

Antes (estado atual, mantido):

```yaml
      # Lint ainda não é bloqueante: o backend foi escrito antes deste workflow existir
      # (BL-26). Tornar `continue-on-error: false` após uma primeira passada de limpeza.
      - name: Lint (ruff)
        run: ruff check .
        continue-on-error: true
```

Depois (a aplicar **somente** após `ruff check .` retornar exit 0 com `ruff==0.17.3`):

```yaml
      - name: Lint (ruff)
        run: ruff check .
```

E em `pip install ruff` (linha 77): trocar por `pip install "ruff==0.17.3"`.

## Passo «Lint (next lint)» do frontend (linha 109)

O `continue-on-error: true` da linha 109 **não** é o mesmo lint do backend. É o passo `npm run lint` em `03_frontend`, que roda `next lint` do frontend. Não foi tocado, conforme o passo 3 da tarefa. Não há comentário no CI explicando por que ele não é bloqueante. Decisão a tomar em outra tarefa: avaliar se o lint do frontend pode ser bloqueante e, se sim, registrar os erros atuais antes de remover o `continue-on-error`.

## Pendências

1. Limpeza dos 11 erros acima (regras RUF005/RUF043/RUF001/I001), em tarefa própria, sem misturar com o CI.
2. Depois de `ruff check .` limpo com 0.17.3: aplicar o «Depois» acima e fixar a versão no `pip install`.
3. Verificar o passo de lint no GitHub Actions (**o workflow não foi executado no GitHub**; a validação acima é só local).
4. Proposta de decisão (para o integrador levar a `decisoes.md`, não editada aqui): o lint do backend só vira bloqueante com `ruff.toml` versionado + ruff fixado em 0.17.3 + `ruff check .` limpo no `main`.

## Observações de escopo

- `04_backend/requirements.txt` e outros workflows não foram alterados.
- `00_docs/projeto/*` e `backlog-tarefas.md`/`backlog-kanban.md` não foram editados.
- Pytest não foi executado: a tarefa não alterou código do backend, e a verificação relevante aqui é o lint.
- Este worktree foi avançado por fast-forward para `main` (`46ddb74`) antes da tarefa, porque o `ruff.toml` e o `ruff.md` da T04 só existiam em `main`. Nenhum commit próprio foi perdido.
