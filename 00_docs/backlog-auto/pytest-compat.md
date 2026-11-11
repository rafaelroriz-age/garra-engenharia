# Compatibilidade pytest 9 × pytest-asyncio (DEC-31 / R-11)

Registro da tarefa A do lote `backlog-auto`. Ambiente: Windows 11, Python 3.12.4 (venv em `04_backend/.venv`, criado com `uv venv --python 3.12`). Python do sistema (3.14) não usado, pois não instala o pillow.

## Problema

`python -m pytest --collect-only -q` em `04_backend` aborta na coleta:

```text
INTERNALERROR>   File ".../pytest_asyncio/plugin.py", line 626, in pytest_collectstart
INTERNALERROR>     pyobject = collector.obj
INTERNALERROR> AttributeError: 'Package' object has no attribute 'obj'
no tests collected in 0.06s
```

Versões antes da correção (instaladas a partir de `requirements.txt` original):

| Pacote | Antes |
|---|---|
| pytest | 9.2.0 |
| pytest-asyncio | 0.23.3 |
| pillow | 10.4.0 |

Causa: `pytest-asyncio` 0.23.3 acessa `collector.obj` em `pytest_collectstart`, atributo removido de `Package` no pytest 9. Confirmado pelo traceback acima.

## Verificação de compatibilidade

Dry-run com `uv pip install --dry-run`:

- `pytest-asyncio==1.2.0` + `pytest==9.2.0` → **insatisfazível**: 1.2.0 exige `pytest>=8.2,<9`.
- `pytest-asyncio>=1.0,<2` + `pytest>=9.1.1,<10` → resolve para **pytest-asyncio 1.4.1.post1**.

Escolhido o intervalo estreito `pytest-asyncio>=1.4.1,<1.5` (não `pytest<9`, pois o pytest 9 é a versão já declarada e a 1.4.x suporta-a).

## Mudança

Único arquivo alterado: `04_backend/requirements.txt`.

```diff
-pytest-asyncio>=0.23,<1.0
+pytest-asyncio>=1.4.1,<1.5
```

Versões depois:

| Pacote | Depois |
|---|---|
| pytest | 9.2.0 (inalterado) |
| pytest-asyncio | 1.4.1.post1 |
| pillow | 10.4.0 (inalterado) |

## Comandos e resultados

1. Coleta após a correção:
   `python -m pytest --collect-only -q` → **139 tests collected in 29.15s** (antes: INTERNALERROR, 0 coletados).

2. Módulos sem banco pedidos:
   `python -m pytest -q tests/test_health.py tests/test_brand_assets.py tests/test_rfo_templates.py tests/test_ltip_templates.py`
   → **42 passed, 1 warning in 23.57s**. O warning é `StarletteDeprecationWarning` do `TestClient` (não bloqueante).

3. Suíte completa (`python -m pytest -q`), **sem PostgreSQL**:
   → **2 failed, 52 passed, 1 warning, 85 errors in 192.37s**.
   - As 2 falhas (`tests/test_seguranca.py::test_login_bloqueia_apos_tentativas_malsucedidas_consecutivas` e `::test_registro_publico_bloqueado_quando_ja_existem_usuarios`) e os 85 erros são de banco: `relação "usuarios" não existe` / `ProgrammingError`.
   - Motivo: Docker não existe nesta máquina; `localhost:5433` (PostgreSQL de `05_infra/docker-compose.yml`) está recusando conexão (verificado). **A suíte de integração não foi executada.** Nenhum resultado foi inventado.

4. Lint: `uvx ruff check .` em `04_backend` → **214 erros** (B008 87, F821 38, I001 36, UP007 18, outros). Não há configuração de ruff no repositório (`pyproject.toml`/`ruff.toml` não encontrados em `04_backend`). Esses erros são **pré-existentes**: a única alteração do lote é `requirements.txt`, sem nenhum `.py` tocado. Ruff não está em `requirements.txt`; usado via `uvx`.

Frontend (`npm run lint`/`build`): não aplicável, nenhum arquivo de `03_frontend` foi alterado.

## Pendências

- Suíte de integração (`pytest` completo) precisa de PostgreSQL em `localhost:5433` (e MinIO, para os testes de storage). Rodar em máquina com Docker ou com `docker compose up -d` em `05_infra/`.
- Ruff: 214 erros pré-existentes; decidir se o projeto adota uma configuração própria (hoje não há) ou se o checklist precisa de tratamento separado. Fora do escopo desta tarefa.
- `R-11` e `DEC-31` **não existem** em `00_docs/projeto/riscos.md` nem em `decisoes.md` (busca por `DEC-31` e `R-11` sem resultado). A proposta abaixo assume o conteúdo descrito no enunciado da tarefa.
- `00_docs/backlog-auto/diagnostico.md` (citado como §3.1) não existe no repositório.

## Proposta de DEC-31 (para revisão do integrador; não aplicada em `decisoes.md`)

> **DEC-31 — Compatibilidade do stack de testes do backend.** O backend fixa `pytest>=9.1.1,<10.0` e `pytest-asyncio>=1.4.1,<1.5` em `04_backend/requirements.txt`. O `pytest-asyncio` 0.23.x é incompatível com o pytest 9 (falha de coleta `'Package' object has no attribute 'obj'`) e não deve ser reintroduzido. Ao atualizar qualquer um dos dois, validar com `python -m pytest --collect-only -q` antes de integrar. Referência: `00_docs/backlog-auto/pytest-compat.md`.

Sugestão para R-11: registrar o risco "suíte de testes não coleta com pytest 9 + pytest-asyncio 0.23" como mitigado por esta mudança, com dependência de PostgreSQL para a suíte completa.
