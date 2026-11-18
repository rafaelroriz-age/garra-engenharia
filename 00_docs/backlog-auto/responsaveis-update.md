# PUT /responsaveis/{id} — atualização de Responsável (DEC-50)

Tarefa: consequência de DEC-50, «`ResponsavelUpdate` existe sem rota». Papel: backend.

## Contrato da rota

`PUT /api/v1/responsaveis/{responsavel_id}` (`04_backend/app/api/v1/responsaveis.py`, `atualizar_responsavel`).

- **Corpo:** `ResponsavelUpdate` (schema já existente, sem alteração). Todos os campos são opcionais.
- **Autorização:** `require_auditor` (RN-18, DEC-27). `auxiliar` e `cliente` recebem 403.
- **Atualização parcial:** `model_dump(exclude_unset=True)`. Campo omitido não muda. Corpo `{}` retorna 200 sem alterar nada.
- **Resposta:** 200 com `ResponsavelRead`, após `commit` e `refresh`.

| Situação | Status | Tipo RFC 7807 |
|---|---|---|
| Sucesso (auditor) | 200 | — |
| Sem token | 401 | — |
| Perfil `auxiliar` ou `cliente` | 403 | `acesso-negado` |
| `responsavel_id` inexistente | 404 | `recurso-nao-encontrado` |
| Payload inválido (ex.: `qualificacoes` não é lista) | 422 | validação do FastAPI |
| `nome` ou `tipo` com `null` explícito | 422 | `regra-de-negocio` |
| `usuario_id` de usuário inexistente | 422 | `regra-de-negocio` |
| `usuario_id` já vinculado a outro Responsável | 409 | `conflito` |

## Decisões tomadas (propostas para `decisoes.md`, não aplicadas)

**P1: `usuario_id` segue a regra do `POST`.** O vínculo `Responsavel.usuario_id` é o que dá ao usuário do Portal do Cliente acesso aos dados (DEC-18, `app/services/portal_service.py`, `app/api/deps.py:120`). Como o `POST` já aceita `usuario_id` e só o auditor pode chamá-lo, a rota `PUT` não abre escalada de privilégio nova. Mantive o campo, em vez de bloqueá-lo, porque sem ele não há como corrigir um vínculo errado. A rota exige:
- usuário existente (422 caso contrário);
- um usuário em no máximo um Responsável (409 caso contrário), checado antes do `commit` e com `IntegrityError` capturado como rede de segurança (a coluna tem `unique=True`);
- `null` desfaz o vínculo e remove o acesso do Portal.

**P2: `nome` e `tipo` não aceitam `null`.** São `NOT NULL` no banco. Sem essa checagem, `{"nome": null}` daria 500 por `IntegrityError`. A checagem fica na rota, sem alterar o schema.

**P3: sem checagem de unicidade de e-mail ou CPF/CNPJ.** O `POST` também não tem, e o modelo não declara `unique` nesses campos. Não criei regra nova. Se o dono quiser unicidade, é decisão de produto, e vale aplicá-la nos dois verbos juntos.

**Lacuna pré-existente (fora do escopo, não alterada):** o `POST` com `usuario_id` já vinculado a outro Responsável cai num `IntegrityError` não tratado e vira 500. Sugestão: aplicar a mesma checagem do `PUT` no `POST` em tarefa própria.

## Arquivos alterados

- `04_backend/app/api/v1/responsaveis.py`: rota `PUT`, docstring do módulo, imports (`ConflictError`, `DomainError`, `IntegrityError`, `ResponsavelUpdate`).
- `04_backend/tests/test_responsaveis_update.py`: 11 testes novos.
- `00_docs/backlog-auto/responsaveis-update.md`: este documento.

Nenhum schema foi alterado. Nenhuma migration foi criada. Nenhuma variável de ambiente foi criada.

## Testes

### Execução isolada (passou)

```text
cd 04_backend
POSTGRES_DB=garra_engenharia_t95 (PostgreSQL localhost:5433, usuário garra)
alembic upgrade head   -> exit 0 (até c6f2a8d4e1b9)
pytest tests/test_responsaveis_update.py -q   -> 11 passed
pytest tests/test_responsaveis.py tests/test_responsaveis_update.py -q -> 15 passed
ruff check .   -> All checks passed! (exit 0)
```

Os 11 testes: auditor atualiza e persiste; parcial preserva campos; corpo vazio não altera nada; `null` em `nome` retorna 422; payload inválido retorna 422; id inexistente retorna 404 RFC 7807; auxiliar retorna 403 e nada muda; cliente retorna 403; sem token retorna 401; auditor vincula `usuario_id` e um segundo vínculo ao mesmo usuário retorna 409; `usuario_id` inexistente retorna 422.

### Execução conjunta `pytest tests -k "responsave or rbac"` (não passou)

Resultado: 9 falhas, 21 passaram, 1 skipped (`--ignore` de `test_rfo_contexto.py` e `--deselect` do teste de foto, ver ambiente abaixo). Com o arquivo novo ausente, a mesma seleção dá 2 falhas, 17 passaram, 1 skipped.

- **Pré-existentes, não causadas por esta mudança:**
  - `test_rbac_auxiliar.py::test_auxiliar_vincula_foto_a_visita_com_autoria`: `HeadBucket 403 Forbidden` no storage S3 (ambiente sem bucket acessível).
  - `test_responsaveis.py::test_listar_responsaveis_filtra_por_tipo` e `test_visitas_lacunas.py::test_correcao_rbac_endpoints_novos`: também falham sem o arquivo novo.
- **Contaminação entre módulos:** depois de uma falha assíncrona anterior, os testes seguintes levam `RuntimeError: Event loop is closed` e `'NoneType' object has no attribute 'send'`. Os testes novos, que rodam depois, herdam esse erro. Quando rodados isoladamente ou só com `test_responsaveis.py`, passam 100%. A causa está no padrão de engine e `dependency_overrides` global compartilhado pelos módulos de teste, e corrigi-la está fora desta tarefa.

Conclusão honesta: os 11 testes novos passam isoladamente e com o arquivo de responsáveis existente. Na suíte conjunta eles falham pelo mesmo problema de contaminação que já derruba testes existentes.

## Ambiente (o que foi feito e o que não foi)

- **Banco `garra_engenharia_test` não usado.** Ele tem `alembic_version = d3e7a1c5f9b2`, revisão que não existe em nenhum commit deste repositório (`git log --all -S` vazio). Não o alterei (Regra de pronto §4). Criei o banco isolado `garra_engenharia_t95` com `CREATE DATABASE` e apliquei `alembic upgrade head` nele. Sugestão: o dono confirma se `garra_engenharia_test` deve ser recriado.
- **`04_backend/.venv` criado** (não existia em nenhum worktree). `pip install -r requirements.txt`, e `ruff` e `pytest` instalados nele. O `.venv` está fora do git.
- **Credencial:** a senha do Postgres foi lida de `05_infra/.env` da checkout principal e passada só por variável de ambiente nos comandos. Não foi gravada em arquivo nem commitada.
- **`tests/test_rfo_contexto.py` não importa no Windows** (`OSError: cannot load library 'libpango-1.0'`, falta lib nativa do WeasyPrint). Ignorado nas execuções de `-k`.
- **Docker** não está no PATH do bash. O Postgres respondeu direto na porta 5433.

## Próximo passo

- Dono: aprovar P1 a P3 e decidir sobre o `garra_engenharia_test` com revisão desconhecida.
- Em tarefa própria: tratar o 500 do `POST` com `usuario_id` duplicado e a contaminação entre módulos de teste.
