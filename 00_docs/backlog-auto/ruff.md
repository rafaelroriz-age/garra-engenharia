# Ruff no backend: configuração e limpeza (Tarefa C, DEC-31 / R-11)

## Resultado

`ruff check .` em `04_backend` passou de **214 erros** para **0** (exit 0). Versão usada: **ruff 0.17.3**, Python 3.12.4, venv em `04_backend/.venv` (ignorado pelo git; criado com `python -m venv` e `pip install -r requirements.txt ruff`).

## Configuração adotada: `04_backend/ruff.toml`

Antes não havia config no repositório. O ruff resolvia um `pyproject.toml` **fora do repositório** (`C:\Users\dynatest\OneDrive - Dynatest Engenharia\pyproject.toml`, de outro projeto, visto em `ruff check . --show-settings`), o que tornava o resultado dependente da máquina. Os 214 erros vinham dessa config externa; o CI (sem ela) usaria só as regras padrão (E4, E7, E9, F). Decisão: fixar no repositório o mesmo conjunto que já vinha sendo aplicado localmente e que a descrição da tarefa lista.

| Chave | Valor | Motivo |
|---|---|---|
| `line-length` / `target-version` | 100 / `py312` | Dockerfiles usam `python:3.12-slim`; o CI usa 3.12. |
| `select` | `E, F, I, B, UP, RUF` | Erros reais (F), imports ordenados (I), bugbear (B), modernização (UP), regras ruff (RUF). |
| `ignore` | `E501` | Linhas longas em strings, SQL e templates; não há formatter configurado. Único ignore. |
| `extend-exclude` | `.venv` | Evita lintar dependências instaladas. |
| `flake8-bugbear.extend-immutable-calls` | `fastapi.Depends/Query/Security/Header/Path/Body/File/Form` | B008 em `x = Depends(...)` é o idioma do FastAPI. Em vez de ignorar B008 globalmente, essas chamadas são declaradas imutáveis; a regra segue valendo para o resto do código. Isso eliminou os 87 B008. |

`alembic/versions` **não** foi excluído do lint: nas migrations só mudaram imports (ordenação, `Sequence` de `collections.abc`) e anotações (`Union[...]` → `X | Y`). Não houve mudança em `upgrade()`/`downgrade()`.

## F821 (38): todos falsos positivos

Todos são anotações em string (`Mapped["Edificacao"]`, `Mapped[list["Visita"]]`) usadas em `relationship()`. As classes existem (todas importadas em `app/models/__init__.py`) e o SQLAlchemy as resolve pelo registry. O ruff não as vê porque não havia import nos arquivos. Correção: `from typing import TYPE_CHECKING` + bloco `if TYPE_CHECKING:` com o import da classe, o que não cria import circular em runtime. **Nenhum nome realmente inexistente.**

| Arquivo | Nomes (ocorrências) | Veredito |
|---|---|---|
| `contrato.py` | Edificacao, Responsavel (×3), ContratoExecutor, ContratoNbr, Inspecao | falso positivo |
| `contrato_executor.py` | Contrato, Responsavel (×2) | falso positivo |
| `contrato_nbr.py` | Contrato | falso positivo |
| `edificacao.py` | Contrato | falso positivo |
| `foto.py` | Ocorrencia, Visita | falso positivo |
| `inspecao.py` | Contrato, Visita, Ocorrencia, Relatorio | falso positivo |
| `ocorrencia.py` | Inspecao, SistemaPredial, Subsistema, Foto | falso positivo |
| `relatorio.py` | Inspecao | falso positivo |
| `responsavel.py` | Usuario, Contrato (×2), ContratoExecutor (×2) | falso positivo |
| `sistema_predial.py` | Subsistema, Ocorrencia | falso positivo |
| `subsistema.py` | SistemaPredial, Ocorrencia | falso positivo |
| `usuario.py` | Responsavel | falso positivo |
| `visita.py` | Inspecao, VisitaMaoObra, VisitaMedicao, Foto | falso positivo |
| `visita_mao_obra.py` | Visita | falso positivo |
| `visita_medicao.py` | Visita | falso positivo |

Validação: `python -c 'import app.main, app.models'` + `configure_mappers()` sem erro; `alembic heads` → `d3b7c9e4f1a2 (head)` (um só head).

## Antes / depois por regra

| Regra | Antes (config externa) | Depois de `ruff.toml` | Final |
|---|---|---|---|
| B008 | 87 | 0 (extend-immutable-calls) | 0 |
| F821 | 38 | 38 | 0 (TYPE_CHECKING) |
| I001 | 36 | 20 (a diferença: `.venv` e config) | 0 (`--fix`) |
| UP007 | 18 | 18 | 0 (`--fix`) |
| UP017 | 8 | 8 | 0 (`--fix`) |
| F401 | 7 | 7 | 0 (`--fix`; imports não usados em `ocorrencia_repository.py` etc.) |
| UP035 | 6 | 6 | 0 (`--fix`) |
| B905 | 4 | 4 | 0 (manual) |
| RUF007 | 2 | 2 | 0 (manual) |
| RUF022 | 2 | 2 | 0 (`--fix`) |
| RUF100 | 2 | 2 | 0 (`--fix`, `# noqa: BLE001` inútil: BLE não está selecionado) |
| F541 | 1 | 1 | 0 (`--fix`) |
| RUF003 | 1 | 1 | 0 (manual) |
| RUF005 | 1 | 1 | 0 (manual) |
| UP046 | 1 | 1 | 0 (manual) |
| **Total** | **214** | **111** | **0** |

(O passo intermediário de 111 erros é só `ruff.toml` aplicado; I001 cai de 36 para 20 só por trocar a config externa pela `ruff.toml`; não investiguei a causa exata da diferença.)

Correções manuais (sem mudança de comportamento):
- B905 `bitmap_tracer.py`: `zip(pontos, manter, strict=True)` (`manter` é criado com `[False] * total`, mesmo tamanho). `tests/test_brand_assets.py`: `strict=False` (preserva o comportamento exato do teste).
- RUF007 `build_brand_assets.py` e `rfo_layout_extractor.py`: `zip(x, x[1:])` → `itertools.pairwise(x)` (resultado idêntico; elimina também o B905).
- RUF005 `bitmap_tracer.py`: `rotacionado + [rotacionado[0]]` → `[*rotacionado, rotacionado[0]]`.
- RUF003 `ltip_layout_extractor.py`: en dash em comentário trocado por hífen (só comentário).
- UP046 `app/schemas/common.py`: `PaginatedResponse(BaseModel, Generic[T])` → `class PaginatedResponse[T](BaseModel)` (PEP 695, válido no 3.12 do Docker/CI; verificado `PaginatedResponse[int](...)` instancia e `response_model=PaginatedResponse[ContratoRead]` continua importando).

## Testes

- `pytest` (04_backend, venv 3.12): **52 passed, 2 failed, 85 errors** (3m34s). **Os testes de integração não puderam ser validados:** há um PostgreSQL respondendo em `localhost:5433`, mas sem schema (`relação "usuarios" não existe`, `UndefinedTableError`); não apliquei `alembic upgrade head` para não mutar um banco compartilhado entre worktrees, e `docker` não existe no PATH. Os 85 errors são desse banco sem tabelas (e `tests/test_storage.py` precisa de MinIO, `botocore`); os 2 failed (`test_seguranca.py::test_login_bloqueia_apos_tentativas_malsucedidas_consecutivas` e `::test_registro_publico_bloqueado_quando_ja_existem_usuarios`) falham pela mesma causa (`usuarios` inexistente). Não há baseline sem a mudança para comparar; a alteração tocou só imports e anotações, então **o resultado de integração permanece não verificado**: rodar `alembic upgrade head` + `pytest` com a stack de `05_infra` no ar.
- Ambiente: `pip install -r requirements.txt` resolveu `pytest-asyncio 0.23.3`, que quebra com `pytest 9.2.0` (`AttributeError: 'Package' object has no attribute 'obj'` na coleta). Usei `pytest-asyncio 0.26.0` (dentro de `>=0.23,<1.0`). Sugestão: subir o piso para `pytest-asyncio>=0.26,<1.0` em `requirements.txt` (não alterei).

## Comandos executados (a partir de `04_backend`)

```text
python312 -m venv .venv ; .venv/Scripts/python -m pip install -r requirements.txt ruff   # ruff 0.17.3
ruff check . --statistics                    # 214 (config externa) -> 111 (com ruff.toml)
ruff check . --select F821                   # 38 falsos positivos (script one-off adicionou os blocos TYPE_CHECKING)
ruff check app/models --select F821,I001 --fix
ruff check . --fix                           # regras seguras
ruff check .                                 # All checks passed! (exit 0)
python -c "import app.main, app.models; configure_mappers()" ; alembic heads
pip install "pytest-asyncio>=0.26,<1.0" ; python -m pytest -q    # 52 passed, 2 failed, 85 errors (sem schema no PG)
```

## Proposta para o CI (não aplicada)

Em `.github/workflows/ci.yml`, passo "Lint (ruff)": remover `continue-on-error: true` e o comentário "Lint ainda não é bloqueante"; opcionalmente fixar a versão (`pip install "ruff==0.17.3"`) para o resultado ser reprodutível, e subir o piso do `pytest-asyncio` em `requirements.txt` (ver acima). Proposta de decisão: DEC-31 concluída para o lint (config versionada em `04_backend/ruff.toml`, lint bloqueante).
