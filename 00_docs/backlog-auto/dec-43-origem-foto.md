# DEC-43 — Enum fechado de `origem` da foto (payload de vínculo)

Doc da tarefa (proposta da T27). Gerado pela execução em background do worktree `backlog-T31`.
Não altera os documentos de gestão (`backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`) nem `BACKLOG.md`: o integrador atualiza o status no fechamento de lote.

## 1. Divergências encontradas na entrada

- **DEC-43 não existe em `00_docs/projeto/decisoes.md`.** A última decisão registrada é a DEC-30. A tarefa foi executada seguindo a especificação do próprio prompt (valores `upload_manual|lightshot|clipboard`). A DEC-43 precisa ser formalizada pelo integrador antes do fechamento.
- **`00_docs/backlog-auto/frontend-origem-foto.md` não existe.** Ficaram em `00_docs/backlog-auto/` apenas `BACKLOG-MANUAL.md` e `CELULAR.md`. Este doc (`dec-43-origem-foto.md`) passa a ser o registro da tarefa.
- **O contrato do frontend não coincide com o pedido.** `03_frontend/lib/types.ts:185` define `OrigemFoto = "lightshot" | "upload" | "camera"`, e `types.ts:210` usa esse tipo no payload de vínculo. Não há `upload_manual` nem `clipboard` no frontend. O frontend passa `origem` livre (`03_frontend/components/foto-upload.tsx:70-75`). Com o enum backend novo, esse envio retorna 422 para `upload` e `camera`. **Pendência de integração**: alinhar o frontend (ou o enum) antes de publicar.

## 2. Levantamento de valores de `origem` em 04_backend (`grep -rn origem`)

| Local | Valor | Dentro do enum? | Situação |
|---|---|---|---|
| `app/scripts/seed_benchmark_rfo.py:209` | `upload_manual` | sim | ok (seed, não passa pelo schema de vínculo) |
| `tests/test_fotos.py:209, 230, 265` | `upload_manual` | sim | ok |
| `tests/test_fotos.py:246` | `lightshot` | sim | ok |
| `tests/test_rbac_auxiliar.py:196` | `upload` | **não** | **quebra**: `POST /visitas/{id}/fotos` passa a retornar 422 onde o teste espera 201 |
| `tests/test_models.py:158, 202` | `upload` | n/a | não quebra: grava o modelo ORM direto, sem schema de vínculo |

`app/models/foto.py:30`, `app/repositories/foto_repository.py` e `app/services/foto_service.py` recebem `origem: str` e não validam. Continuam assim: a validação fica só na borda (payload).

**Pendência (fora de `toca`, não editada)**: `tests/test_rbac_auxiliar.py:196` envia `"origem": "upload"`. Esse valor não está no enum. Corrigir para `upload_manual` é trivial, mas o arquivo estava fora da lista permitida, então ficou para o integrador. Até lá, `test_auxiliar_vincula_foto_a_visita_com_autoria` falha com 422.

`tests/test_fotos_lacunas.py` citado no prompt **não existe** no repositório. Não há testes de lacunas de foto para verificar.

## 3. Mudança aplicada

- `04_backend/app/schemas/foto.py`:
  - novo alias `OrigemFoto = Literal["upload_manual", "lightshot", "clipboard"]`;
  - `FotoVincularPayload.origem` passa de `str` para `OrigemFoto` (continua obrigatório; não havia default);
  - `FotoBase.origem` e `FotoRead` **permanecem `str`**, então registros antigos (ex.: `upload`) continuam legíveis na saída (sem validação de saída).
- `04_backend/tests/test_foto_origem_enum.py` (novo):
  - schema (Pydantic puro): valores válidos, 6 inválidos, ausente e `None`, e leitura de origem antiga;
  - endpoint: `POST /ocorrencias/{id}/fotos` e `/visitas/{id}/fotos` com `origem` inválida devem dar 422. Usa `auth_headers`/`client` de `tests/test_fotos.py`. **Pula com motivo explícito** se `localhost:5433` não responder.

## 4. Pendências (não feitas, por decisão)

- **Sem migration e sem CHECK no banco.** Dados antigos com `origem` fora do enum (ex.: `upload`) continuam gravados. A normalização é tarefa à parte.
- Alinhar `OrigemFoto` do frontend com o enum do backend (ver seção 1).
- Corrigir `tests/test_rbac_auxiliar.py:196` (ver seção 2).
- Formalizar DEC-43 em `decisoes.md` (integrador).

## 5. Comandos e saídas

Ambiente: Windows; o venv `garra-engenharia\.venv` está na raiz do repositório principal. `docker` **não está instalado** nesta máquina, então `docker compose ps` não pôde ser executado. `Test-NetConnection localhost -Port 5433` → `TcpTestSucceeded: False`: PostgreSQL não está no ar. Nada foi subido nem derrubado.

Os resultados dos comandos abaixo são preenchidos a seguir.

### 5.1 pytest (a partir de `04_backend`)

Observação: `tests/test_fotos_lacunas.py` não existe; o comando foi executado sem ele.

Execução 1 (`tests/test_foto_origem_enum.py tests/test_fotos.py`, 264 s):

```
SKIPPED [2] tests\test_foto_origem_enum.py:62: PostgreSQL de 05_infra indisponível em localhost:5433; teste de endpoint não rodou
8 failed, 12 passed, 2 skipped in 264.16s
botocore.exceptions.EndpointConnectionError: Could not connect to the endpoint URL: "http://localhost:9000/relatorios-prediais"
```

- **12 passed**: todos os testes de schema de `test_foto_origem_enum.py`.
- **2 skipped**: teste de endpoint (422), por falta do PostgreSQL.
- **8 failed**: todos em `tests/test_fotos.py`, por `EndpointConnectionError` no MinIO (`localhost:9000`), que também não está no ar. **Falha de ambiente, não da mudança**, mas significa que `test_fotos.py` **não foi verificado** aqui. Não pude comparar com a versão anterior do enum.

Execução 2 (somente schema, após `ruff --fix` de ordenação de imports): `12 passed, 2 deselected`.

Não rodei `pytest tests/test_fotos_lacunas.py` (arquivo inexistente).

### 5.2 ruff check . (a partir de `04_backend`)

`ruff` não está no venv do projeto; usei o `ruff.exe` do anaconda (`C:\Users\dynatest\anaconda3\Scripts\ruff.exe`).

Arquivos tocados: `All checks passed!` (exit 0, após `ruff --fix` de ordenação em `test_foto_origem_enum.py`).

`ruff check .` no backend inteiro: **216 erros** em arquivos existentes (ex.: `app/api/v1/fotos.py` 14, `edificacoes.py` 13, `portal.py` 11, `ocorrencias.py` 10). Não são do diff desta tarefa, mas **o gate `ruff check .` do checklist não está verde no repositório**; não corrigi por estar fora de `toca`.
