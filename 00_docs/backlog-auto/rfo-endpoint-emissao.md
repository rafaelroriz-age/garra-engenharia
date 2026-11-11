# Endpoint de emissão do RFO (BL-13)

Tarefa T46. Depende de `montar_contexto_rfo` (tarefa C, [rfo-contexto-banco.md](rfo-contexto-banco.md)).

> Observação: o worktree desta sessão nasceu defasado da `main` (sem `rfo_contexto.py`). A branch foi avançada por `git merge --ff-only main` (`14ead2f..d68a117`) antes de qualquer alteração.

## Arquivos

| Caminho | O quê |
|---|---|
| `04_backend/app/api/v1/relatorios.py` | Router `POST /api/v1/inspecoes/{inspecao_id}/relatorios/rfo` e a dependency `get_renderizador_rfo` |
| `04_backend/app/services/relatorio_service.py` | `emitir_rfo`, `RenderizadorRFO` (Protocol), `RenderizadorRFOPadrao`, `GeradorIndisponivelError` (503), `chave_relatorio`, `proxima_versao` |
| `04_backend/app/schemas/relatorio.py` | + `RelatorioEmitirPayload` (`extra=forbid`) e `RelatorioEmitidoRead` |
| `04_backend/app/main.py` | `app.include_router(relatorios_router)` |
| `04_backend/tests/test_relatorios_rfo_api.py` | 13 testes (4 sem banco, 9 com PostgreSQL) |
| `04_backend/tests/test_rfo_contexto.py` | só `ruff --fix` (I001, ordem de imports da tarefa C), para `ruff check .` passar |

O enunciado pedia registrar o router em `app/api/v1/__init__.py`; esse arquivo está vazio e todos os routers são registrados em `app/main.py`, então segui o padrão real.

Nenhuma migration: `Relatorio` já tem `versao` (String), `tipo`, `status`, `pdf_key`, `docx_key` e `emitido_em`. O campo `criado_em` da resposta vem de `emitido_em`.

## Contrato

`POST /api/v1/inspecoes/{inspecao_id}/relatorios/rfo`

- Autorização: `require_auditor` (RN-18, DEC-27/ADR-14).
- Corpo: opcional. Se enviado, precisa ser `{}`; qualquer campo (ex.: `pdf_key`) → 422 (`extra=forbid`). Tipo, versão e chaves são do servidor.
- Resposta 201:

```json
{
  "id": "uuid", "inspecao_id": "uuid", "tipo": "RFO", "versao": "V02",
  "status": "emitido", "tem_pdf": true, "tem_docx": true,
  "criado_em": "2026-11-10T22:00:00Z"
}
```

As chaves do storage não são devolvidas; o download segue pelo Portal (`GET /portal/relatorios/{id}/download/{pdf|docx}`, URL pré-assinada).

| HTTP | `type` (sufixo) | Quando |
|---|---|---|
| 401 | — | sem token / token inválido |
| 403 | `acesso-negado` | perfil `auxiliar` ou `cliente` |
| 404 | `inspecao-nao-encontrada` | inspeção inexistente |
| 409 | `inspecao-nao-rfo` | `Inspecao.tipo != 'RFO'` |
| 409 | `foto-ausente-no-storage` | foto de visita vinculada no banco mas sem objeto no storage |
| 422 | — | corpo com campo extra |
| 503 | `gerador-relatorio-indisponivel` | WeasyPrint sem GTK/Pango (`ImportError`/`OSError` no import do `rfo_pipeline`) |

## Fluxo

1. `montar_contexto_rfo(db, inspecao_id)` → 404/409.
2. Baixa do storage as fotos das **visitas** (são as únicas que o `rfo_pipeline` embute). Objeto ausente → 409.
3. `renderizador.gerar_pdf` e `gerar_docx` (em `asyncio.to_thread`). O padrão importa `rfo_pipeline` sob demanda, aplica `otimizar_imagem` a cada foto e escreve num diretório temporário.
4. `SELECT ... FOR NO KEY UPDATE` na inspeção: serializa emissões concorrentes da mesma inspeção (versão sem colisão) sem bloquear inserts de visitas/ocorrências, que só pedem `FOR KEY SHARE` no pai. O lock fica fora da renderização.
5. Próxima versão: `V01`, `V02`... a partir das versões `^V\d+$` já existentes do tipo `RFO` da inspeção (valores fora do padrão são ignorados).
6. Upload PDF e DOCX (`max_size_bytes` = 200 MB) e `INSERT` de um **novo** `Relatorio` (`tipo='RFO'`, `status='emitido'`, `emitido_em=now()`); versões anteriores ficam preservadas e continuam visíveis no Portal.
7. Falha no upload ou no commit: rollback e remoção best-effort das chaves já gravadas.

## Convenção de chaves

`relatorios/{inspecao_id}/rfo-{versao em minúsculas}.{pdf|docx}`, ex.: `relatorios/3f.../rfo-v01.pdf`. Determinística e só do servidor: nenhum dado da requisição entra na chave.

## Testes

`tests/test_relatorios_rfo_api.py` (storage e renderizador fakes via `dependency_overrides`):

- sem banco: `proxima_versao`, `chave_relatorio`, renderizador padrão sem WeasyPrint → `GeradorIndisponivelError` 503, sem token → 401;
- com PostgreSQL: auditor 201 (chaves gravadas, content-type, contexto e bytes da foto chegam ao renderizador), segunda emissão → `V02` com `V01` preservada, auxiliar 403, cliente 403, inspeção 404, inspeção LTIP 409, corpo com campo extra 422, foto ausente no storage 409 sem renderizar, cliente do contrato vê o relatório em `GET /portal/relatorios` e baixa o PDF.

### Resultado nesta sessão

- `ruff check .` em `04_backend`: **All checks passed!**
- PostgreSQL de `05_infra/docker-compose.yml` **fora do ar**: `localhost:5433` recusa conexão e o Docker não está instalado nesta máquina (`docker: command not found`). Os 9 testes de integração **não rodaram de fato** (erro de conexão nos fixtures).
- Python: o `python` do PATH (Anaconda) não tem `python-jose`; usei `04_backend/.venv` do checkout principal. Nele, `greenlet` está quebrado (`No module named 'greenlet._greenlet'`), o que derruba qualquer sessão async do SQLAlchemy, inclusive o fechamento da sessão em `get_db`.
- `python -m pytest tests/test_relatorios_rfo_api.py`: **3 passed** (`proxima_versao`, `chave_relatorio`, 503). O teste de 401 recebe o 401, mas falha no teardown de `get_db` por causa do `greenlet` (mesma causa dos demais erros).
- Suíte completa (`python -m pytest -q`, 375 testes coletados): **interrompida na coleta**: `ERROR tests/test_rfo_contexto.py - OSError: cannot load library 'libpango-1.0'` (1 error in 288.27s). Esse arquivo é da tarefa C e importa `rfo_pipeline` (WeasyPrint) no topo; não foi alterado aqui além do `ruff --fix`. Sem o PostgreSQL, rodar o resto com `--ignore` só produziria erros de conexão, então não há número de aprovados da suíte a registrar.
- Sugestão para o fechamento: em `test_rfo_contexto.py`, trocar o import do topo por `pytest.importorskip` ou import local, como o `report_generator/__init__.py` já faz (PEP 562).

Para rodar: `docker compose up -d` em `05_infra/`; em `04_backend/`, `pip install --force-reinstall greenlet` no venv, `alembic upgrade head` e `python -m pytest tests/test_relatorios_rfo_api.py`.

## Pendente

- Frontend: botão «Emitir relatório» na tela da inspeção (perfil auditor), com estados de carregamento, 409/503 e lista de versões.
- Emissão de LTIP, RFIP e vistorias (cautelar e residencial): os pipelines existem em `report_generator/`, mas falta montar o contexto do banco e os endpoints. O router e o serviço foram escritos para receber um endpoint por tipo.
- Geração assíncrona (fila/worker + `status` `gerando`/`erro`) para relatórios de ~200 páginas: hoje a emissão é síncrona e o tempo do request cresce com o número de fotos (RNF-06; ver `benchmark-pipelines-finais.md`).
- Endpoint interno para listar versões emitidas por inspeção (hoje só o Portal lista, e só para o cliente).
- O template do RFO ainda não imprime ocorrências: as fotos de ocorrência não são baixadas (lacuna 2 de `rfo-contexto-banco.md`).
- `rfo_contexto.legenda_aprovada` continua permissiva (DEC-47, item 1); o `rfo_pipeline` já aplica `legenda_para_relatorio` na renderização, então a IA não vaza para o documento.

## Propostas de decisão

- **P1 — Versionamento:** cada emissão cria um `Relatorio` novo (`V01`, `V02`...) por inspeção e tipo; nada é sobrescrito. O Portal mostra todas as versões; avaliar se o cliente deve ver só a mais recente.
- **P2 — Chaves:** `relatorios/{inspecao_id}/{tipo}-v{NN}.{ext}` para todos os tipos de relatório.
- **P3 — Unicidade no banco:** migration futura com `UNIQUE (inspecao_id, tipo, versao)` em `relatorios`, depois de conferir que os dados existentes não violam a regra. Hoje a unicidade depende do lock `FOR NO KEY UPDATE`.
- **P4 — 503 para motor indisponível:** `gerador-relatorio-indisponivel` como contrato para todo endpoint de geração.
- **P5 — Teto de 200 MB** por arquivo de relatório no storage (`MAX_RELATORIO_SIZE_BYTES`), a revisar com o benchmark de 200 páginas.
