# RFO: ART de Execução ausente imprime "—" (DEC-47 / DEC-33)

Referência: lacuna registrada em `00_docs/backlog-auto/rfo-validacao-completude.md` (T50), seção "Lacunas para decisão do dono".

## Problema

- `executores[].art_execucao` é nullable em `04_backend/app/models/contrato_executor.py` (`mapped_column(String, nullable=True)`).
- `04_backend/templates/rfo/rfo_template.html.j2` (linha 94) imprime `{{ executor.art_execucao }}` sem fallback, então um NULL aparecia como `None`.
- O DOCX (`rfo_template.docx`, renderizado por `rfo_pipeline.gerar_docx`) herda o mesmo problema.

## O que mudou

- `04_backend/app/services/report_generator/rfo_contexto.py`:
  - novo helper `_texto_ou_traco(valor)`: `None`, `""` ou só espaços viram `"—"`; qualquer outro valor volta inalterado (sem `strip`, o formato não muda).
  - `_executor_ctx` passa `art_execucao` por esse helper. Demais campos sem alteração.
- `04_backend/tests/test_rfo_art_execucao.py` (novo, 13 testes, sem banco e sem WeasyPrint):
  - helper e `_executor_ctx` com nulo, vazio, espaços e valor preenchido;
  - HTML: renderiza o template real com Jinja (`ChainableUndefined`) e confere `ART de Execução:</td><td>—</td>` e ausência de `None`;
  - DOCX: renderiza o template real com docxtpl, salva e lê `word/document.xml`; confere `ART de Execução: —`.
- `rfo_template.html.j2` e `rfo_template.docx` **não foram alterados**; o fallback fica no contexto, então ambos imprimem `—`.
- `01_output-context/` não foi tocado.

## Decisões de implementação

- O fallback fica no contexto (`rfo_contexto`), não no template, para o HTML e o DOCX seguirem a mesma regra (DEC-33: campo vazio vira `—`).
- Não foi incluído `executor.art_execucao` em `CAMPOS_OBRIGATORIOS_RFO`. Isso bloquearia a emissão e exige decisão do dono (ver abaixo).

## Comandos e resultados

Ambiente: Windows, Python do Anaconda, worktree `worktree-backlog-T53`.

Antes da alteração, a branch estava 258 commits atrás de `main` (sem commits próprios). Foi feito `git merge --ff-only main` (14ead2f → 14943e5) para trazer `rfo_contexto.py`, `test_rfo_validacao_contexto.py` e a T50.

- `python -m pytest tests/test_rfo_art_execucao.py -q` → **13 passed**.
- `python -m pytest tests/test_rfo_art_execucao.py tests/test_rfo_templates.py tests/test_rfo_validacao_contexto.py -q -k "not endpoint"` → **40 passed, 3 deselected**.
  - Os 3 deselecionados são os de endpoint (`test_endpoint_*`), que precisam de PostgreSQL.
- `python -m ruff check .` → **7 erros pré-existentes**, nenhum em arquivo tocado por esta tarefa:
  - `alembic/versions/e5a1f0c2b7d4_relatorios_unicidade_versao_dec_48.py` (UP035, I001, UP007 ×3);
  - `tests/test_portal_versoes_relatorio.py` (I001);
  - `tests/test_relatorio_unicidade.py` (I001).
  - `python -m ruff check app/services/report_generator/rfo_contexto.py tests/test_rfo_art_execucao.py` → **All checks passed**.

### Não executado

- `tests/test_rfo_pipeline.py`: **não existe** neste repositório (o pipeline RFO só é coberto indiretamente por `test_rfo_templates.py`). Substituído pelos testes do DOCX em `test_rfo_art_execucao.py`.
- `tests/test_rfo_contexto.py`: **não coleta** neste Windows. Importa o pacote `app.services.report_generator`, que importa WeasyPrint, e as bibliotecas nativas (Pango/GTK) não estão instaladas (`OSError: cannot load library 'libpango-1.0-0'`).
- Endpoints de `test_rfo_validacao_contexto.py` e `test_relatorios_rfo_api.py`: **não rodaram**, PostgreSQL em `localhost:5433` está **fora do ar** (verificado).
- `pytest` completo do backend: não rodado (mesmo motivo, banco e WeasyPrint).

Para fechar a validação completa: subir `05_infra/docker-compose.yml` e rodar, em `04_backend`, `python -m pytest` e `python -m ruff check .` num ambiente com WeasyPrint.

## Para decisão do dono (não alterado aqui)

- Tornar `executores[].art_execucao` obrigatória na emissão do RFO (entrar em `CAMPOS_OBRIGATORIOS_RFO`, com tratamento da lista de executores). O schema de contrato (`app/schemas/contrato.py`, RN-09) já exige `art_execucao` na criação; o NULL só aparece em dados antigos ou importados.
- DEC-33 segue como "Proposta (aguarda confirmação do cliente)" em `00_docs/projeto/decisoes.md`. Esta tarefa aplica o item (2) dela ao campo ART de Execução; a confirmação do cliente fica a cargo do integrador.

## Para o fechamento de lote (00_docs/)

- `backlog-tarefas.md` / `backlog-kanban.md`: marcar a tarefa como feita, com o commit desta branch.
- `status.md`: registrar que o RFO imprime `—` para ART de Execução ausente, testes sem banco passando e suíte com banco pendente.
- `decisoes.md`: nenhuma decisão nova; DEC-33 e DEC-47 continuam como estão.
