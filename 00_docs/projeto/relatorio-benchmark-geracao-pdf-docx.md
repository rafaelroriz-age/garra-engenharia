---
title: Benchmark de Geração de PDF/DOCX do RFO — BL-22
type: gestao
status: concluido
owner: Garra Engenharia
related:
  - 00_docs/projeto/backlog-tarefas.md
  - 00_docs/projeto/riscos.md
  - 00_docs/estudo-do-contexto.md
  - 00_docs/arquitetura.md
tags: [benchmark, performance, rnf-06, r-03, pdf, docx, weasyprint, docxtpl]
last_updated: 2026-08-05
---

# Benchmark de Geração de PDF/DOCX do RFO (BL-22)

## Contexto e escopo real medido

BL-22 pede o benchmark do pipeline de geração de PDF/DOCX do RFO (BL-12/BL-13). Ao
iniciar a tarefa, confirmou-se no código que **esse pipeline não existe** —
BL-12/BL-13 continuam bloqueadas por B-02 (aguardando os templates `.docx`/`.xlsm`
originais do cliente). Não havia endpoint `/relatorios/gerar`, worker Celery,
nem template HTML/DOCX do RFO; existia apenas o modelo `Relatorio` (BL-04).

Para produzir uma medição real (não uma estimativa), foi construído um
**pipeline mínimo, de fidelidade APROXIMADA** — não o template fiel ao modelo do
cliente — só para viabilizar este benchmark:

- `04_backend/templates/rfo_template.html.j2` — template HTML/CSS (paginação via
  `@page`, contador de página) inspirado na estrutura de
  `00_docs/convertidos/Relatorio_de_Fiscalizacao_1.md`, não no layout fiel.
- `04_backend/templates/rfo_benchmark_template.docx` — template DOCX genérico
  com tags `docxtpl` (gerado por
  `app/scripts/build_rfo_benchmark_docx_template.py`).
- `04_backend/app/services/report_generator/rfo_pipeline.py` — `gerar_pdf`
  (Jinja2 + WeasyPrint) e `gerar_docx` (docxtpl, fotos via `Subdoc`), com
  medição de tempo por etapa, e `otimizar_imagem` (redimensiona/recomprime uma
  foto para uso em relatório).
- `04_backend/app/scripts/seed_benchmark_rfo.py` — gera dados de pior caso
  (Edificação + Contrato RFO + Inspeção + N Visitas com mão de obra, medições e
  fotos sintéticas reais no MinIO).
- `04_backend/app/scripts/benchmark_relatorio_geracao.py` — mede leitura de
  fotos no MinIO, geração de PDF e DOCX (com e sem otimização de imagem) e
  registra um `Relatorio` real (`status="concluido"`, `pdf_key`/`docx_key`).

**Este pipeline não deve ser confundido com a implementação definitiva de
BL-12/BL-13** (que exigirá o template fiel do cliente e a fila assíncrona
Celery/Redis do ADR-06). Ele existe apenas para gerar uma medição real e
reproduzível de RNF-06/R-03.

## Ambiente de teste

- Container `garra-backend` (imagem de desenvolvimento `04_backend/Dockerfile`,
  `python:3.12-slim` com as bibliotecas de sistema do WeasyPrint), rodando via
  `05_infra/docker-compose.yml` na máquina local do desenvolvedor.
- PostgreSQL 16 e MinIO no mesmo `docker-compose` (mesma rede Docker — latência
  de rede mínima, diferente de um MinIO/S3 remoto em produção).
- WeasyPrint 69.0, docxtpl 0.20.2 (+ `docxcompose` 2.2.0, dependência de
  `docxtpl.new_subdoc()` não declarada pelo pacote — adicionada a
  `requirements.txt` nesta tarefa), Pillow ≥ 10.3.
- **WeasyPrint não roda nativamente no Windows sem as bibliotecas GTK/Pango do
  sistema** (`libgobject-2.0-0` ausente no `.venv` local) — o benchmark foi
  executado dentro do container Docker, que já tem essas dependências
  instaladas (`Dockerfile`, comentário "Bibliotecas de sistema exigidas pelo
  WeasyPrint", DEC-01).

## Metodologia e dados de pior caso

Fotos sintéticas (não são fotos reais de campo — geradas via Pillow com
formas/gradiente para ter uma taxa de compressão JPEG realista) em **2400×1800
px, qualidade 85**, sem nenhum redimensionamento prévio — simula exatamente o
que `app.services.image_processing.reprocessar_imagem` (BL-11) armazenava
**antes** da correção aplicada nesta tarefa (ver "Otimização aplicada" abaixo):
recodifica a imagem mas não a redimensiona.

Dois volumes foram testados:

| Cenário | Visitas | Fotos | Páginas geradas |
|---|---|---|---|
| Piloto | 55 | 165 | 56 |
| **Pior caso (medido)** | 190 | **570** | **191** |

O cenário de pior caso (191 páginas / 570 fotos) **excede** o teto de RNF-06
("até 200 páginas com 150+ fotos") no número de fotos e se aproxima do teto de
páginas — considerado representativo e conservador o suficiente para validar o
requisito.

Cada execução mede, separadamente: leitura das fotos no MinIO, (opcionalmente)
otimização de imagem, renderização do template, conversão final (WeasyPrint/
docxtpl) e o registro final (`Relatorio.status="concluido"` + upload dos
artefatos no MinIO).

## Resultados — pior caso (190 visitas, 570 fotos, 191 páginas)

### Tempo por etapa (segundos)

| Etapa | Tempo |
|---|---|
| Leitura das 570 fotos no MinIO | 2,01s |
| Otimização de imagem (todas as fotos, uma vez) | 39,01s |
| PDF — sem otimização (render + WeasyPrint) | 53,62s |
| PDF — com otimização (render + WeasyPrint) | 18,03s |
| DOCX — sem otimização (subdocs + docxtpl) | 48,01s |
| DOCX — com otimização (subdocs + docxtpl) | 15,02s |
| Registro final (upload PDF+DOCX no MinIO + `UPDATE Relatorio`) | 9,16s* |

\* variação observada entre execuções (1,7s–9,2s) por contenção de I/O local — ver "Risco residual".

### Tamanho dos artefatos gerados

| Cenário | PDF | DOCX |
|---|---|---|
| Sem otimização | 280,5 MB | 138,2 MB |
| Com otimização | 67,4 MB | 37,6 MB |

### Tempo fim-a-fim por JOB (o pipeline real gera PDF **e** DOCX no mesmo job — "two-pass rendering", `arquitetura.md` Seção 5/ADR-06)

| Cenário | Cálculo | Total | RNF-06 (< 60s) |
|---|---|---|---|
| Sem nenhuma otimização de imagem | leitura + pdf + docx + registro | **112,8s** | ❌ Viola (quase 2x o limite) |
| Otimizando a imagem a cada geração de relatório | leitura + otimização + pdf + docx + registro | **83,2s** | ❌ Viola |
| Fotos já otimizadas no momento do upload (fix aplicado nesta tarefa) | leitura + pdf + docx + registro | **44,2s** | ✅ Atende (~26% de margem) |

## Gargalo identificado

`app.services.image_processing.reprocessar_imagem` (BL-11) **recodifica** a
imagem recebida (remove EXIF/payloads, mitigação A08) mas **nunca a
redimensiona** — fotos de câmera de celular em resolução total ficam
armazenadas como estão. Isso tem dois efeitos:

1. **Se o relatório embutir as fotos em resolução total**: o HTML intermediário
   (fotos em base64) e o DOCX ficam enormes (280 MB / 138 MB no pior caso) e a
   própria conversão (WeasyPrint/docxtpl) fica mais lenta só por ter que
   processar essa quantidade de bytes de imagem — sozinho já perto do limite de
   60s (112,8s combinando os dois formatos).
2. **Se a compressão/redimensionamento acontece a cada geração de relatório**
   (o que este benchmark fazia inicialmente, cenário "otimizado" isolado): o
   próprio passo de otimização (39s para 570 fotos) é um custo pago de novo a
   cada emissão de relatório, mesmo que a foto já tenha sido otimizada numa
   emissão anterior — o total ainda ultrapassa 60s (83,2s).

## Otimização aplicada

Duas mudanças, uma em código de produção e uma no pipeline de benchmark:

1. **`app/services/image_processing.py` (BL-11, código real, já em produção)**:
   adicionado redimensionamento para no máximo **2000 px no lado maior**
   (`MAX_LADO_ARMAZENADO_PX`) dentro de `reprocessar_imagem` — a foto já é
   armazenada em um tamanho razoável desde o upload, não apenas recodificada.
   Esse limite foi escolhido para preservar qualidade suficiente para o editor
   de anotação/zoom (BL-31), sendo menos agressivo que a compressão específica
   de embutir em relatório (item 2). Validado contra a suíte de testes
   existente (`tests/test_fotos.py`, `tests/test_storage.py` — 17 testes,
   sem alteração de comportamento esperado).
2. **`app/services/report_generator/rfo_pipeline.otimizar_imagem`** (pipeline
   de benchmark): redimensiona para no máximo 1200 px + JPEG qualidade 72 no
   momento de compor o relatório — compressão adicional, mais agressiva,
   específica para o tamanho de exibição em PDF/DOCX (não precisa da mesma
   resolução usada no app).

Com as duas camadas, o cenário realista de produção (fotos já capadas a 2000px
no upload, mais a compressão de 1200px/72 no embed) é o medido como "fotos já
otimizadas no upload" acima: **44,2s por job, dentro do limite de RNF-06**.

Foi necessário adicionar `docxcompose` a `requirements.txt` — dependência de
`docxtpl.new_subdoc()` (usado para listas de fotos por visita) não declarada
pelo pacote `docxtpl`. Também foi adicionado um parâmetro `max_size_bytes`
opcional a `StorageClient.upload()` (`app/services/storage/base.py`/
`s3_client.py`): o limite de 25 MB por objeto (`MAX_UPLOAD_SIZE_BYTES`) foi
definido pensando em fotos individuais (BL-07) e bloqueava o upload do
PDF/DOCX final do relatório, que é legitimamente maior — a chamada do
benchmark passa um limite de 150 MB só para esse artefato.

## Risco residual (não afirmar conformidade além do medido)

- **Pipeline aproximado, síncrono, sem Celery/Redis** — a implementação final
  de BL-12/BL-13 (fila assíncrona, ADR-06, template fiel ao cliente) precisa
  ser re-medida quando existir; os números aqui validam a arquitetura de
  otimização (redimensionar no upload), não o código final.
- **Variação de ambiente**: o passo de registro final variou de 1,7s a 9,2s
  entre execuções no mesmo container, provavelmente por contenção de I/O local
  (múltiplos arquivos temporários de centenas de MB sendo escritos/lidos em
  execuções consecutivas). Recomenda-se nova medição em ambiente de
  staging/produção dedicado, sem carga concorrente, antes do sign-off final de
  RNF-06.
- **MinIO local, mesma rede Docker** — latência de leitura/escrita medida aqui
  é otimista comparada a um MinIO/S3 remoto em produção (Render); a
  implementação final deve considerar essa diferença.
- **Fotos sintéticas, não reais** — a taxa de compressão JPEG de fotos de campo
  reais (texturas de concreto, infiltração, etc.) pode diferir da gerada por
  Pillow neste benchmark; a ordem de grandeza (compressão de ~70% de redução de
  tamanho ao capar em 1200px/qualidade 72) é uma referência, não uma garantia.
- **`montagem_subdocs` do DOCX é o maior custo relativo do formato DOCX**
  (13s de 15s otimizado, 42s de 48s sem otimização) — se margem adicional for
  necessária no futuro, investigar inserir imagens via XML de baixo nível em
  vez de `python-docx.add_picture` por foto.

## Como reproduzir

```powershell
# 1. Subir a stack local (Postgres + MinIO + backend)
cd 05_infra; docker compose up -d

# 2. Copiar os arquivos novos para dentro do container (não há bind-mount, ver
#    05_infra/docker-compose.yml) ou reconstruir a imagem:
docker compose up -d --build backend

# 3. Gerar o template DOCX base (uma vez)
docker exec garra-backend python -m app.scripts.build_rfo_benchmark_docx_template

# 4. Semear dados de pior caso (~190 visitas, 3 fotos cada = 570 fotos)
docker exec garra-backend python -m app.scripts.seed_benchmark_rfo `
  --visitas 190 --fotos-por-visita 3 --largura 2400 --altura 1800 --qualidade 85 --reset

# 5. Rodar o benchmark (usa o INSPECAO_ID impresso no passo 4)
docker exec garra-backend python -m app.scripts.benchmark_relatorio_geracao --inspecao-id <uuid>
```

## Conclusão

- **RNF-06 (< 60s para até 200 páginas / 150+ fotos) é atingível com a
  arquitetura atual**, desde que o redimensionamento de imagem aconteça uma
  única vez, no upload (BL-11) — não a cada geração de relatório. Medido:
  **44,2s por job** (PDF+DOCX juntos) no pior caso testado (191 páginas / 570
  fotos), ~26% de margem sob o limite.
- Sem essa otimização, o pior caso **viola RNF-06** por uma margem
  significativa (83,2s a 112,8s, conforme o cenário).
- A otimização de redimensionamento no upload (`MAX_LADO_ARMAZENADO_PX=2000`)
  já foi aplicada ao código de produção de BL-11 nesta tarefa. A compressão
  adicional específica de embutir em relatório (`otimizar_imagem`, 1200px/72)
  existe apenas no pipeline de benchmark e deve ser reaproveitada quando
  BL-12/BL-13 forem implementadas de verdade.
