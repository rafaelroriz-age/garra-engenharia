# T28 — `url_fetcher` de fotos nos demais pipelines (DEC-41, item B)

## O que foi feito

- Novo módulo `04_backend/app/services/report_generator/foto_fetcher.py`
  (`RegistroDeFotos`, `criar_url_fetcher`, `mime_da_imagem`, `UrlNaoPermitida`).
  Extraído porque a lógica serve a três pipelines; o `ltip_pipeline.py` **não foi alterado**
  (mantém sua cópia local; unificar fica como sugestão abaixo).
- `rfo_pipeline.py`, `vistoria_cautelar_pipeline.py` e `vistoria_residencial_pipeline.py`:
  `gerar_pdf` registra cada foto (e, na cautelar, assinatura e fundo da capa) no registro e
  escreve `garra-foto:<n>` no HTML; o WeasyPrint recebe `url_fetcher`.
  Sem `URLFetcher` (WeasyPrint antigo) volta ao data URI.
- `renderizar_html` (cautelar, residencial) continua **autocontido com data URI**; ambos ganharam
  um `_renderizar(..., registro)` interno. O RFO não tem `renderizar_html`; só `gerar_pdf` mudou.
- `rfip_pipeline.py` e LTIP intocados.
- Segurança (A10/SSRF): o fetcher só resolve `garra-foto:<n>` registrados e `data:`; `file:`,
  `http(s):`, índices não registrados/negativos/não numéricos levantam `UrlNaoPermitida`.
- Efeito colateral no RFO: o data URI de fallback agora usa o MIME detectado (antes fixo `image/jpeg`).
- Testes: `04_backend/tests/test_pipelines_url_fetcher.py` (20 testes).

## Resultado dos testes (Windows, sem GTK/Pango)

- `pytest tests/test_pipelines_url_fetcher.py`: 18 passed, 2 skipped (os 2 que exercitam a classe
  `URLFetcher` do WeasyPrint, indisponível aqui: `OSError libgobject-2.0-0`).
- `test_vistoria_cautelar_pipeline.py`, `test_vistoria_residencial_pipeline.py`, `test_ltip_pipeline.py`:
  passam, exceto os testes de PDF, **pulados** (sem WeasyPrint).
- `tests/test_rfo_templates.py` e demais `test_*_templates.py` **não rodaram**: `openpyxl` não está
  instalado neste ambiente (erro de coleta). Nenhum teste de PDF foi executado, portanto o caminho
  real `gerar_pdf` + fetcher **não foi verificado de ponta a ponta**; precisa rodar no container de `05_infra/`.
- `ruff check` nos arquivos tocados: ok.
- Suíte completa (PostgreSQL em localhost:5433 respondia; MinIO/storage não), ignorando os `test_*_templates.py`
  por falta de `openpyxl`: **81 failed, 185 passed, 7 skipped, 35 errors** (10 min). Os erros vistos são
  `botocore` em `test_storage.py` (storage indisponível); as demais falhas não foram investigadas e não
  foram comparadas com a `main` sem a mudança. Nenhum teste dos pipelines tocados falhou.

## Medições

Nenhuma (sem WeasyPrint local). O ganho esperado vem do LTIP (T20: parse do HTML ~2,3 s → ~0,3 s;
RSS ~380 → ~290 MB com 239 fotos); para estes pipelines, com poucas fotos, o ganho deve ser menor.
Medir no container antes de afirmar.

## Decisões propostas

1. Aceitar o módulo `foto_fetcher.py` como helper oficial e, em tarefa própria, migrar o
   `ltip_pipeline.py` para ele (hoje `_fetcher_de_fotos` ali aceita outras URLs via fetcher padrão;
   o novo é estrito).
2. `rfip_pipeline.py` permanece de fora até medição com dados reais.
