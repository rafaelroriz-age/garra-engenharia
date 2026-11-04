---
title: Benchmark dos pipelines finais de PDF/DOCX — re-medição de BL-22 (T17)
type: gestao
status: parcial
owner: Garra Engenharia
related:
  - 00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md
  - 00_docs/estudo-do-contexto.md
  - 00_docs/projeto/riscos.md
tags: [benchmark, performance, rnf-06, r-03, pdf, docx, weasyprint, docxtpl, bl-22]
last_updated: 2026-11-04
---

# Benchmark dos pipelines finais de PDF/DOCX (T17, BL-22)

> Tarefa T17 (origem BL-22) · Data: 2026-11-04 · Branch: `worktree-backlog-T17` · Papel: arquiteto-software.
> Tarefa só de medição: nenhum arquivo de código, template ou dado do repositório foi alterado. O único arquivo novo é este Doc.

## Resumo

| Pipeline | Páginas (PDF) | Fotos | PDF (s) | DOCX (s) | Job PDF+DOCX em sequência (s) | RNF-06 (< 60 s) |
|---|---|---|---|---|---|---|
| RFO | 201 | 150 | 19,04 | 2,09 | **21,1** | ✅ atende (65 % de margem) |
| LTIP | **137** | 239 | **62,59** | 0,58 (sem foto) · ~2,7 com foto¹ | **63,2 a ~65,3** | ❌ **viola, e com só 137 páginas** |
| Vistoria Cautelar | 200 | 350 | 29,08 | 5,10 | **34,2** | ✅ atende (43 %) |
| Vistoria Residencial | 200 | 358 | 49,10 | 7,64 | **56,7** | ⚠️ atende por pouco (5 %) |

Fotos no cenário "otimizado" (1200 px, JPEG q72, 88 KB em média), equivalente ao cenário de 44,2 s de 2026-08-05. Os números medem só o pipeline (render + conversão + escrita em disco). **Leitura das fotos no MinIO e upload/registro do `Relatorio` não entram**, e somavam 11,2 s na medição anterior. Pico de memória (RSS do processo): 319 a 420 MB no PDF e 64 a 124 MB no DOCX.

¹ O template DOCX versionado do LTIP não tem o placeholder `{{ ocorrencia.foto }}` (lacuna já registrada em `ltip-pipeline.md`), então o DOCX sai sem fotos. O custo das 239 fotos foi medido à parte com o template mínimo do teste `test_docx_embute_foto_quando_o_template_tem_o_placeholder`: 2,12 s.

**Medição incompleta: 1 execução por combinação, não 3.** A sessão foi interrompida pelo Claude Code por falta de memória no host (detalhes em "O que ficou sem medir"). Não há mediana. A tabela traz a única execução de cada combinação. Ficaram sem medir: as execuções 2 e 3, o cenário de fotos de 2000 px ("armazenado") e o LTIP com ~200 páginas.

## Ambiente

| Item | Valor |
|---|---|
| Host | Notebook Windows 11 Pro, Intel Core i7-1355U (10 núcleos: 2P + 8E, 12 threads), 15,7 GB de RAM |
| Docker | Docker Desktop, engine 26.1.4, backend WSL2 (kernel 5.15.153.1-microsoft-standard-WSL2). VM com 12 vCPU e 7,6 GiB |
| Imagem | `garra-bench-t17-backend`, construída de `04_backend/Dockerfile` (python:3.12-slim) no commit `4ffe06a` via `docker compose build backend` em `05_infra/` |
| Container | Debian 13.7, Python 3.12.16 |
| Bibliotecas | WeasyPrint **70.0** (era 69.0 em 2026-08-05), pydyf 0.13.0, docxtpl 0.20.2, python-docx 1.2.0, docxcompose 2.2.0, Jinja2 3.1.6, Pillow 10.4.0, libpango 1.56.3, libcairo 1.18.4 |
| Serviços | Só o `backend`, via `docker compose run --no-deps`. Os pipelines não usam PostgreSQL nem MinIO, então nenhum dos dois foi subido para a medição |
| Carga concorrente | Ao iniciar, o Docker Desktop religou containers que já existiam (`garra-frontend`, `garra-backend` antigo, `garra-minio`, `garra-postgres`, `airflow-sgp-postgres-1`, `airflow-sgp-redis-1`): somados, ~1,6 % de CPU e ~465 MiB ociosos (`docker stats`). Outras três tarefas do lote (T14–T16) rodavam em paralelo no mesmo host, e a RAM livre do host chegou a 0,57 GB. **Os números tendem a ser pessimistas e ruidosos** |

Observação de base: o worktree foi criado no commit `14ead2f`, que ainda não tinha `ltip_pipeline.py` nem os pipelines das vistorias. Antes de medir, o branch foi avançado por fast-forward até `4ffe06a` (o commit `main` do disparo de T14–T17). Nenhum commit novo foi criado nesse passo.

## Metodologia

- **Script**: `bench_pipelines.py`, escrito fora do Git, em `%CLAUDE_JOB_DIR%\tmp\bench\` (montado em `/bench` no container) e reproduzido integralmente no Apêndice A. Ele chama a API pública de cada pipeline (`gerar_pdf(contexto, fotos_bytes, destino)` e `gerar_docx(...)`) exatamente como os testes `tests/test_*_pipeline.py` fazem.
- **Isolamento**: cada medição roda num subprocesso Python novo. O tempo é o `perf_counter` em volta da chamada `gerar_*` (parede), e as métricas internas de cada pipeline também são registradas. A memória é o pico de RSS do subprocesso (`resource.getrusage(RUSAGE_SELF).ru_maxrss`), que inclui as alocações em C do WeasyPrint/Pango/cairo, invisíveis ao `tracemalloc`. `rss_antes_mb` é o RSS depois de importar as bibliotecas e carregar contexto e fotos, imediatamente antes da geração.
- **Pré-condições fora do tempo medido**: imports (como num worker aquecido), montagem do contexto e leitura das fotos do disco. Os arquivos de saída vão para `/tmp/saida`, no FS do container, porque o bind mount do Windows distorceria a escrita.
- **Fotos sintéticas** (`fotos --n 700`): 700 JPEGs distintos de 2000×1500 px (o teto `MAX_LADO_ARMAZENADO_PX` do BL-11), q85, com gradiente, formas, traços e ruído gaussiano para a taxa de compressão ficar próxima da de foto de campo real. Média de 622 KB ("armazenado"). Cada uma foi passada por `rfo_pipeline.otimizar_imagem` (1200 px, q72): média de 88 KB ("otimizado"). Para comparar, as fotos otimizadas de 2026-08-05 davam ~118 KB por foto embutida.
- **Volume (~200 páginas e 150+ fotos)**: `calibrar` gera o PDF com n = 10 e n = 40 e ajusta uma reta de páginas × n.

| Pipeline | Unidade (n) | Fotos por unidade | Páginas n=10 / n=40 | n escolhido | Páginas obtidas |
|---|---|---|---|---|---|
| RFO | visita (4 itens de serviço, 3 de mão de obra, 3 medições, 2 observações) | 3 | 41 / 161 | 50 | 201 |
| LTIP | ocorrência (ficha GUT completa, 8 sistemas, 5 subsistemas) | 1 | 17 / 41 | 239 | **137** (a reta superestimou, ver Gargalos) |
| Vistoria Cautelar | figura (+ todas as ~33 seções de `conteudo` com 2 parágrafos, 8 sistemas, 8 + 15 linhas de tabela, assinatura e fundo de capa) | 1 (+2) | 31 / 46 | 348 | 200 |
| Vistoria Residencial | foto (+ todas as 31 chaves de `textos` com 2 parágrafos, 8 sistemas) | 1 | 26 / 41 | 358 | 200 |

- **Ordem**: o laço de repetição é o mais externo (rep → cenário → pipeline → formato), para que deriva térmica ou de I/O se espalhe entre as combinações. A rodada 1 do cenário "otimizado" terminou inteira, e a interrupção ocorreu logo depois.

## Resultados (cenário "otimizado", execução 1)

| Pipeline | Formato | n | Fotos | Fotos (MB) | Páginas | Tempo parede (s) | Etapas (s) | RSS antes → pico (MB) | Arquivo (MB) |
|---|---|---|---|---|---|---|---|---|---|
| RFO | PDF | 50 | 150 | 12,9 | 201 | **19,04** | render_html 0,10 · conversao_pdf 18,85 | 77,6 → **318,7** | 14,8 |
| RFO | DOCX | 50 | 150 | 12,9 | — | **2,09** | montagem_subdocs 1,67 · render_e_salvar 0,41 | 77,8 → 124,3 | 13,0 |
| LTIP | PDF | 239 | 239 | 20,6 | 137 | **62,59** | render_html 0,18 · conversao_pdf 62,39 | 79,3 → **398,8** | 21,1 |
| LTIP | DOCX (template versionado, sem foto) | 239 | 239 | 20,6 | — | **0,58** | montagem_fotos 0,00 · render_e_salvar 0,57 | 53,9 → 73,8 | 0,1 |
| LTIP | DOCX (template mínimo com `{{ ocorrencia.foto }}`) | 239 | 239 | 20,6 | — | **2,12** | montagem_fotos 0,00 · render_e_salvar 2,07 | 54,1 → 64,4 | 20,6 |
| Vistoria Cautelar | PDF | 348 | 350 | 30,2 | 200 | **29,08** | render_html 0,33 · conversao_pdf 28,74 | 88,9 → **419,7** | 36,9 |
| Vistoria Cautelar | DOCX | 348 | 350 | 30,2 | — | **5,10** | montagem_fotos 0,00 · render_e_salvar 5,10 | 63,5 → 77,7 | 30,2 |
| Vistoria Residencial | PDF | 358 | 358 | 30,9 | 200 | **49,10** | render_html 0,49 · conversao_pdf 48,59 | 89,6 → **419,9** | 37,6 |
| Vistoria Residencial | DOCX | 358 | 358 | 30,9 | — | **7,64** | montagem_fotos 0,00 · render_e_salvar 7,63 | 63,9 → 78,7 | 31,0 |

O DOCX não tem contagem de páginas porque a imagem não tem LibreOffice/Word para paginar. Ele usa a mesma entrada do PDF da mesma linha.

### Custo unitário

| Pipeline | PDF: s por página | DOCX: ms por foto |
|---|---|---|
| RFO | 0,094 | 13,9 |
| LTIP | **0,455** | 8,6 (template mínimo) |
| Vistoria Cautelar | 0,144 | 14,6 |
| Vistoria Residencial | 0,243 | 21,3 |

## Comparação com a meta (RNF-06) e com 2026-08-05

RNF-06 (`00_docs/estudo-do-contexto.md`, linha 187): "relatórios de até 200 páginas com 150+ fotos devem ser gerados em menos de 60 segundos".

| Pipeline | Job em sequência, só pipeline (s) | + leitura/registro de 2026-08-05 (2,0 + 9,2 s)² | PDF e DOCX em paralelo (máx., s)³ | Veredito |
|---|---|---|---|---|
| RFO | 21,1 | ~32,3 | 19,0 | ✅ atende |
| LTIP (137 p.) | 63,2 a ~65,3 | ~76 | 62,6 | ❌ viola |
| LTIP (~200 p., **estimado**)⁴ | ~97 | ~108 | ~93 | ❌ viola (estimativa, não medido) |
| Vistoria Cautelar | 34,2 | ~45,4 | 29,1 | ✅ atende |
| Vistoria Residencial | 56,7 | ~68 | 49,1 | ⚠️ atende só o pipeline; viola com I/O em sequência |

² Soma ilustrativa, não medida aqui: leitura de 570 fotos no MinIO (2,01 s) e upload + `UPDATE Relatorio` (9,16 s, com variação de 1,7 a 9,2 s), números de 2026-08-05 com outro volume de fotos e de bytes.
³ Se o worker gerar PDF e DOCX em dois processos simultâneos, o tempo do job cai para o maior dos dois. Isso não foi medido em paralelo: o valor é o máximo das medições isoladas.
⁴ Extrapolação linear, não medida: a ~0,536 página por ocorrência acima das ~9 páginas fixas, 200 páginas pedem ~357 ocorrências. A 0,261 s por ocorrência, isso dá ~93 s de PDF. Se o custo de layout crescer de forma superlinear (ver Gargalos), o tempo real é maior.

**Contra 2026-08-05 (44,2 s por job: 191 páginas, 570 fotos, template aproximado):**

- **RFO**: o template final rende 4 páginas por visita, e o aproximado rendia 1. Por isso 200 páginas agora correspondem a 150 fotos, não a 570. O custo por página do PDF ficou idêntico: 0,094 s (18,03 s / 191 p. em 2026-08-05 contra 18,85 s / 201 p. agora). O DOCX caiu de 15,02 s para 2,09 s, mas com 150 fotos em vez de 570 (26 contra 14 ms por foto, com fotos ~25 % menores). O job do pipeline (21,1 s) fica bem abaixo dos 33,1 s equivalentes de 2026-08-05 (PDF 18,03 + DOCX 15,02).
- A conclusão de 2026-08-05 ("RNF-06 atingível desde que a foto seja reduzida uma vez, no upload") **continua valendo para RFO e Vistoria Cautelar**. Ela **não vale para o LTIP** e fica **no limite para a Vistoria Residencial**. Nos quatro pipelines finais, o gargalo é o layout do WeasyPrint (`conversao_pdf` = 98 a 99,7 % do tempo do PDF), não mais o tamanho das fotos.
- A medição anterior não incluía nenhum template fiel ao cliente, e esta não inclui o RFIP (pipeline ainda inexistente).

## Gargalos observados

1. **LTIP: conversão do PDF 3 a 5 vezes mais cara por página que os demais (0,455 s/página).** No template `04_backend/templates/ltip/ltip_template.html.j2` (linhas 57–58), as fichas de cada sistema ficam num único container `.fichas { display: flex; flex-wrap: wrap }` que atravessa dezenas de páginas, com `.ficha { width: 48%; page-break-inside: avoid }`. É o único dos quatro templates com esse padrão. Hipótese (não verificada por profiling): a paginação de flex com quebra no WeasyPrint refaz o layout das linhas a cada página, com custo que cresce com o tamanho do container. Isso também explicaria por que a reta de calibração (n = 10 e 40) superestimou as páginas: com poucas ocorrências por sistema, cada sistema começa página nova.
2. **Vistoria Residencial: 0,243 s/página, a 5 % da meta.** O template usa 5 `position: absolute` (capa e folha de rosto) e `break-inside: avoid` nas figuras de 160 mm (~2 por página). Não foi investigado mais a fundo.
3. **Conversão WeasyPrint domina tudo**: `render_html` (Jinja2 + base64) fica entre 0,1 e 0,5 s. O pico de RSS do PDF (320 a 420 MB) cresce com o volume de fotos embutidas (13 a 31 MB de JPEG, e o HTML em base64 ocupa ~33 % a mais).
4. **DOCX está longe de ser gargalo** (0,6 a 7,6 s, ≤ 125 MB). O custo é o `render_e_salvar` do docxtpl, proporcional ao número de imagens. No RFO, o `new_subdoc` por visita ainda responde por 80 % do DOCX (1,67 de 2,09 s).
5. **Artefatos acima do limite de upload**: Vistoria Cautelar e Residencial geram PDF de 37 a 38 MB e DOCX de 30 a 31 MB, acima dos 25 MB de `MAX_UPLOAD_SIZE_BYTES` por objeto. Em 2026-08-05 o benchmark contornou isso com `max_size_bytes` explícito (150 MB). O worker final precisa fazer o mesmo.
6. **Nenhum pipeline novo redimensiona fotos**: os docstrings deixam isso para o chamador. Os números acima só valem se o chamador entregar fotos de ~1200 px. Com fotos de 2000 px (622 KB), o volume embutido seria ~7 vezes maior (425 MB contra 60 MB para 700 fotos). Isso não foi medido (ver abaixo), mas em 2026-08-05 esse fator triplicou o tempo do PDF.

## Recomendações

1. **LTIP (prioridade alta, bloqueia RNF-06)**: trocar o container flex único por linhas explícitas de duas fichas (`<table>` ou um bloco por par, com `break-inside: avoid` na linha) e re-medir. É uma mudança de template, a fazer pelo gerador `app/scripts/build_ltip_templates.py` (ADR-13), fora do escopo desta tarefa. Vale também incluir no mesmo trabalho o placeholder `{{ ocorrencia.foto }}` no DOCX.
2. **Gerar PDF e DOCX em paralelo no worker** (dois processos, ADR-06): o job cai para o máximo dos dois (Residencial: de 56,7 s para 49,1 s), ao custo de somar os picos de memória (~500 MB).
3. **Dimensionar o worker com ≥ 1 GB de RAM**: um PDF de 200 páginas chega a 420 MB de RSS, e PDF + DOCX em paralelo a ~500 MB, mais a base do processo. Uma instância de 512 MB não comporta isso com folga.
4. **Garantir fotos de ~1200 px na entrada dos pipelines**: guardar no upload (BL-11) uma derivada `otimizar_imagem` (1200 px, q72) ao lado da foto de 2000 px, para não pagar o redimensionamento a cada emissão (39 s para 570 fotos em 2026-08-05).
5. **Investigar a Vistoria Residencial** com profiling do WeasyPrint antes de declarar RNF-06 atendido, porque a margem de 5 % está dentro do ruído de uma execução única.
6. **Completar esta medição** num host dedicado (sem tarefas paralelas, VM Docker ≥ 8 GB e host com RAM livre), usando os comandos de "Como reproduzir": 3 execuções, cenário "armazenado" e LTIP com ~357 ocorrências.

### Propostas de decisão (só neste Doc; o registro em `decisoes.md` fica para o fechamento de lote)

- **Proposta DEC-T17-a**: RNF-06 passa a ser verificado por tipo de relatório e por job completo (leitura das fotos, PDF, DOCX e upload), com o worker gerando PDF e DOCX em processos paralelos e com ≥ 1 GB de RAM.
- **Proposta DEC-T17-b**: os pipelines recebem sempre a derivada de 1200 px/q72 gerada uma única vez no upload (BL-11), nunca a foto de 2000 px. O limite de upload dos artefatos finais (PDF/DOCX) fica separado do limite de foto (25 MB).

## O que ficou sem medir, e por quê

- **Execuções 2 e 3 (mediana)**: o comando `medir --reps 3` foi encerrado pelo Claude Code ("stopped because the system is running low on memory"). A RAM livre do host estava em 0,57 GB de 15,7 GB, com outras três tarefas do lote rodando ao mesmo tempo. O container da medição sobreviveu ao encerramento e foi parado manualmente (`docker stop`) logo depois de concluir a 9ª medição da rodada 1, para não agravar a falta de memória. Pela regra da sessão, a medição não foi reiniciada automaticamente.
- **Cenário "armazenado"** (fotos de 2000 px, 622 KB): seria o próximo da fila e não chegou a rodar.
- **LTIP com ~200 páginas**: a calibração indicou 239 ocorrências, que renderam 137 páginas. Com 239 fotos, o critério "150+ fotos" está cumprido, mas o de "~200 páginas" não. A estimativa para 200 páginas está na tabela de comparação, marcada como extrapolação.
- **RFO com o mesmo volume de 2026-08-05** (190 visitas / 570 fotos, que no template final dariam ~760 páginas): fora do teto de RNF-06, não foi rodado.
- **I/O de produção** (MinIO e registro do `Relatorio`) e **RFIP** (pipeline inexistente): fora do escopo, conforme o enunciado.

## Testes e verificações

Não houve mudança de código, então só foi rodado o que não depende do PostgreSQL, a partir de `04_backend/` no host Windows (`.venv` do repositório):

```text
$ python -m pytest -q tests/test_ltip_pipeline.py tests/test_vistoria_cautelar_pipeline.py tests/test_vistoria_residencial_pipeline.py -p no:cacheprovider
...........s........s........s                                           [100%]
27 passed, 3 skipped in 9.71s
```

Os 3 testes pulados são os de PDF (WeasyPrint indisponível no Windows). O PDF dos três pipelines foi exercitado de fato no container pelo próprio benchmark (arquivos `%PDF` de 137 a 201 páginas).

```text
$ ruff --version && ruff check . --output-format concise
ruff 0.15.1
app\repositories\ocorrencia_repository.py:25:25: F821 Undefined name `Inspecao`
app\repositories\ocorrencia_repository.py:28:67: F821 Undefined name `SistemaPredial`
app\repositories\ocorrencia_repository.py:29:25: F821 Undefined name `SistemaPredial`
app\repositories\ocorrencia_repository.py:32:73: F821 Undefined name `Subsistema`
app\repositories\ocorrencia_repository.py:33:25: F821 Undefined name `Subsistema`
app\scripts\vistoria_cautelar_layout_extractor.py:81:56: RUF001 String contains ambiguous `–` (EN DASH). Did you mean `-` (HYPHEN-MINUS)?
app\scripts\vistoria_cautelar_layout_extractor.py:86:44: RUF001 String contains ambiguous `–` (EN DASH). Did you mean `-` (HYPHEN-MINUS)?
tests\test_ocorrencias_regras.py:6:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_vistoria_cautelar_pipeline.py:133:40: RUF043 Pattern passed to `match=` contains metacharacters but is neither escaped nor raw
tests\test_vistoria_cautelar_pipeline.py:163:40: RUF043 Pattern passed to `match=` contains metacharacters but is neither escaped nor raw
tests\test_vistoria_cautelar_templates.py:11:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_vistoria_cautelar_templates.py:219:22: RUF005 Consider iterable unpacking instead of concatenation
tests\test_vistoria_cautelar_templates.py:228:15: RUF005 Consider iterable unpacking instead of concatenation
tests\test_vistoria_cautelar_templates.py:290:20: RUF005 Consider iterable unpacking instead of concatenation
Found 14 errors.
```

Os 14 erros já existiam em `4ffe06a` (`main`), em arquivos que esta tarefa não tocou. Ficam como achado para o integrador. Os `F821` de `ocorrencia_repository.py` (nomes não importados) parecem bug real, não só estilo. O ruff usado foi o 0.15.1 do Anaconda; a CI faz `pip install ruff` sem fixar versão. O `pytest` completo (que exige o PostgreSQL de `05_infra` em localhost:5433) não foi rodado: nenhum código mudou, e o host estava sem memória. `npm run lint`/`build` não se aplicam (nada em `03_frontend/`).

## Como reproduzir (comandos usados)

O auxiliar `run.ps1` (fora do Git, no mesmo diretório do script) só preenche as variáveis exigidas pela interpolação `${VAR:?}` do compose. Nenhum `.env` foi criado, e o pipeline não usa banco nem MinIO.

```powershell
# run.ps1 — chamar a partir da raiz do worktree
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Cmd)
$env:Path = "C:\Program Files\Docker\Docker\resources\bin;" + $env:Path
$env:POSTGRES_PASSWORD = 'bench-dummy'; $env:MINIO_ROOT_USER = 'bench-dummy'
$env:MINIO_ROOT_PASSWORD = 'bench-dummy'; $env:JWT_SECRET_KEY = 'bench-dummy'
if ((Split-Path -Leaf (Get-Location).Path) -ne '05_infra') { Set-Location (Join-Path (Get-Location).Path '05_infra') }
$b = 'C:\Users\dynatest\.claude\jobs\d04c6bd3\tmp\bench'
docker compose -p garra-bench-t17 run --rm --no-deps -T -v "${b}:/bench" backend sh -c ($Cmd -join ' ')
```

```powershell
# 0. Docker Desktop estava parado; foi iniciado e conferido
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker version          # Server 26.1.4
docker info --format '{{.ServerVersion}} {{.NCPU}}cpu {{.MemTotal}} {{.OperatingSystem}}'
#   26.1.4 12cpu 8167555072 Docker Desktop

# 1. Imagem do backend (a partir de 05_infra/, com as variáveis dummy do run.ps1)
docker compose -p garra-bench-t17 build backend      # -> garra-bench-t17-backend

# 2. Fotos sintéticas, calibração e medição
.\run.ps1 "rm -rf /bench/fotos; python /bench/bench_pipelines.py fotos --n 700 && python /bench/bench_pipelines.py calibrar"
.\run.ps1 "rm -f /bench/bruto.jsonl; python /bench/bench_pipelines.py medir --reps 3 --n rfo=50 ltip=239 ltip_foto=239 vistoria_cautelar=348 vistoria_residencial=358"

# 3. Para completar (host dedicado): LTIP com ~200 páginas e o cenário de 2000 px
.\run.ps1 "python /bench/bench_pipelines.py medir --reps 3 --n ltip=357 ltip_foto=357"
.\run.ps1 "python /bench/bench_pipelines.py medir --reps 3 --cenarios armazenado --n rfo=50 ltip=239 vistoria_cautelar=348 vistoria_residencial=358"

# Limpeza (a imagem do benchmark ocupa ~416 MB)
docker image rm garra-bench-t17-backend
```

## Saída bruta

Versões (dentro do container):

```text
Python 3.12.16
{'weasyprint': '70.0', 'docxtpl': '0.20.2', 'python-docx': '1.2.0', 'pillow': '10.4.0', 'jinja2': '3.1.6', 'pydyf': '0.13.0', 'docxcompose': '2.2.0'}
Package: libpango-1.0-0
Version: 1.56.3-1
Package: libcairo2
Version: 1.18.4-1+b1
12
13.7
5.15.153.1-microsoft-standard-WSL2
```

`fotos --n 700` e `calibrar`:

```text
{"cenario": "otimizado", "n": 700, "media_kb": 88.2, "total_mb": 60.3}
{"cenario": "armazenado", "n": 700, "media_kb": 622.2, "total_mb": 425.3}
geracao_s=352.8
{"pipeline": "rfo", "pag_n10": 41, "pag_n40": 161, "pag_por_unidade": 4.0, "pag_fixas": 1.0, "n_para_200_pag": 50}
{"pipeline": "ltip", "pag_n10": 17, "pag_n40": 41, "pag_por_unidade": 0.8, "pag_fixas": 9.0, "n_para_200_pag": 239}
{"pipeline": "vistoria_cautelar", "pag_n10": 31, "pag_n40": 46, "pag_por_unidade": 0.5, "pag_fixas": 26.0, "n_para_200_pag": 348}
{"pipeline": "vistoria_residencial", "pag_n10": 26, "pag_n40": 41, "pag_por_unidade": 0.5, "pag_fixas": 21.0, "n_para_200_pag": 358}
```

`medir` (`/bench/bruto.jsonl`, conteúdo integral; tempos em s, memória em MB, `tamanho_bytes` em bytes):

```text
{"rep": 1, "pipeline": "rfo", "formato": "pdf", "cenario": "otimizado", "n": 50, "n_fotos": 150, "fotos_mb": 12.9, "parede_s": 19.035, "rss_antes_mb": 77.6, "rss_pico_mb": 318.7, "render_html": 0.096, "conversao_pdf": 18.851, "total": 18.947, "n_paginas": 201, "tamanho_bytes": 15549286}
{"rep": 1, "pipeline": "rfo", "formato": "docx", "cenario": "otimizado", "n": 50, "n_fotos": 150, "fotos_mb": 12.9, "parede_s": 2.086, "rss_antes_mb": 77.8, "rss_pico_mb": 124.3, "montagem_subdocs": 1.668, "render_e_salvar": 0.408, "total": 2.075, "tamanho_bytes": 13630946}
{"rep": 1, "pipeline": "ltip", "formato": "pdf", "cenario": "otimizado", "n": 239, "n_fotos": 239, "fotos_mb": 20.6, "parede_s": 62.588, "rss_antes_mb": 79.3, "rss_pico_mb": 398.8, "render_html": 0.176, "conversao_pdf": 62.387, "total": 62.563, "n_paginas": 137, "tamanho_bytes": 22081762}
{"rep": 1, "pipeline": "ltip", "formato": "docx", "cenario": "otimizado", "n": 239, "n_fotos": 239, "fotos_mb": 20.6, "parede_s": 0.577, "rss_antes_mb": 53.9, "rss_pico_mb": 73.8, "montagem_fotos": 0.001, "render_e_salvar": 0.566, "total": 0.567, "tamanho_bytes": 98249}
{"rep": 1, "pipeline": "ltip_foto", "formato": "docx", "cenario": "otimizado", "n": 239, "n_fotos": 239, "fotos_mb": 20.6, "parede_s": 2.119, "rss_antes_mb": 54.1, "rss_pico_mb": 64.4, "montagem_fotos": 0.001, "render_e_salvar": 2.065, "total": 2.066, "tamanho_bytes": 21617497}
{"rep": 1, "pipeline": "vistoria_cautelar", "formato": "pdf", "cenario": "otimizado", "n": 348, "n_fotos": 350, "fotos_mb": 30.2, "parede_s": 29.077, "rss_antes_mb": 88.9, "rss_pico_mb": 419.7, "render_html": 0.33, "conversao_pdf": 28.74, "total": 29.07, "n_paginas": 200, "tamanho_bytes": 38730305}
{"rep": 1, "pipeline": "vistoria_cautelar", "formato": "docx", "cenario": "otimizado", "n": 348, "n_fotos": 350, "fotos_mb": 30.2, "parede_s": 5.101, "rss_antes_mb": 63.5, "rss_pico_mb": 77.7, "montagem_fotos": 0.002, "render_e_salvar": 5.097, "total": 5.098, "tamanho_bytes": 31693700}
{"rep": 1, "pipeline": "vistoria_residencial", "formato": "pdf", "cenario": "otimizado", "n": 358, "n_fotos": 358, "fotos_mb": 30.9, "parede_s": 49.101, "rss_antes_mb": 89.6, "rss_pico_mb": 419.9, "render_html": 0.493, "conversao_pdf": 48.587, "total": 49.079, "n_paginas": 200, "tamanho_bytes": 39427418}
{"rep": 1, "pipeline": "vistoria_residencial", "formato": "docx", "cenario": "otimizado", "n": 358, "n_fotos": 358, "fotos_mb": 30.9, "parede_s": 7.64, "rss_antes_mb": 63.9, "rss_pico_mb": 78.7, "montagem_fotos": 0.002, "render_e_salvar": 7.631, "total": 7.633, "tamanho_bytes": 32500302}
```

## Apêndice A — `bench_pipelines.py` (integral, fora do Git)

Roda no container com o código de produção em `/app` e fotos e saída bruta em `/bench`. Usa só dados sintéticos e não lê `01_output-context/`.

```python
"""Benchmark dos pipelines finais de relatório (BL-22, re-medição).

Roda DENTRO do container do backend (WeasyPrint só carrega lá), com o código
de produção em /app e este script + fotos sintéticas em /bench:

    python /bench/bench_pipelines.py fotos --n 700
    python /bench/bench_pipelines.py calibrar
    python /bench/bench_pipelines.py medir --reps 3 --n rfo=190 ltip=190 ...

Cada medição roda num subprocesso novo: o pico de RSS (`ru_maxrss`) é do
processo inteiro e inclui as alocações em C do WeasyPrint/Pango/cairo, que o
tracemalloc não enxerga. Só dados sintéticos; nada de 01_output-context/.
"""
from __future__ import annotations

import argparse
import io
import json
import random
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")
BENCH = Path("/bench")
FOTOS = BENCH / "fotos"
SAIDA = Path("/tmp/saida")  # FS do container: o bind mount do Windows distorceria a escrita
PIPELINES = ("rfo", "ltip", "ltip_foto", "vistoria_cautelar", "vistoria_residencial")
CENARIOS = ("otimizado", "armazenado")
LOREM = (
    "Constatou-se, durante a vistoria, a presença de fissuras de pequena abertura no revestimento "
    "argamassado, com indícios de infiltração por capilaridade junto ao rodapé e manchas de umidade. "
    "Recomenda-se o acompanhamento da evolução e a correção conforme a NBR 13749 e a NBR 16747."
)


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux: KiB


# --- fotos sintéticas ---------------------------------------------------------


def _foto(indice: int) -> bytes:
    """2000x1500 (teto MAX_LADO_ARMAZENADO_PX do BL-11), q85, com textura/ruído
    para a taxa de compressão JPEG se aproximar da de uma foto real de campo."""
    from PIL import Image, ImageDraw, ImageFilter

    rnd = random.Random(indice)
    w, h = 2000, 1500
    base = Image.linear_gradient("L").resize((w, h)).convert("RGB")
    cor = Image.new("RGB", (w, h), (rnd.randint(60, 200), rnd.randint(60, 200), rnd.randint(60, 200)))
    img = Image.blend(base, cor, 0.6)
    d = ImageDraw.Draw(img)
    for _ in range(40):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        d.ellipse([x, y, x + rnd.randint(40, 400), y + rnd.randint(40, 300)],
                  fill=tuple(rnd.randint(0, 255) for _ in range(3)))
    for _ in range(25):
        d.line([(rnd.randint(0, w), rnd.randint(0, h)), (rnd.randint(0, w), rnd.randint(0, h))],
               fill=(30, 30, 30), width=rnd.randint(1, 4))
    ruido = Image.effect_noise((w, h), 28).convert("RGB")
    img = Image.blend(img.filter(ImageFilter.GaussianBlur(1.2)), ruido, 0.22)
    d = ImageDraw.Draw(img)
    d.text((30, 30), f"Foto sintetica #{indice}", fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def cmd_fotos(n: int) -> None:
    from app.services.report_generator.rfo_pipeline import otimizar_imagem

    for cenario in CENARIOS:
        (FOTOS / cenario).mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    for i in range(n):
        bruto = _foto(i)
        (FOTOS / "armazenado" / f"{i:04d}.jpg").write_bytes(bruto)
        (FOTOS / "otimizado" / f"{i:04d}.jpg").write_bytes(otimizar_imagem(bruto))  # 1200 px / q72
    for cenario in CENARIOS:
        tamanhos = [p.stat().st_size for p in (FOTOS / cenario).glob("*.jpg")]
        print(json.dumps({"cenario": cenario, "n": len(tamanhos),
                          "media_kb": round(statistics.mean(tamanhos) / 1024, 1),
                          "total_mb": round(sum(tamanhos) / 2**20, 1)}))
    print(f"geracao_s={time.perf_counter() - t0:.1f}")


# --- contextos sintéticos -------------------------------------------------------


def _par(n: int = 2) -> list[str]:
    return [LOREM] * n


def contexto(pipeline: str, n: int) -> tuple[dict, list[str]]:
    """Devolve (contexto, storage_keys usadas). `n` = unidade que escala o laudo."""
    keys: list[str] = []

    def k() -> str:
        keys.append(f"{len(keys):04d}.jpg")
        return keys[-1]

    sistemas = [f"Sistema {i + 1}" for i in range(8)]
    if pipeline == "rfo":  # n visitas x 3 fotos (mesmo desenho do pior caso de 2026-08-05)
        ctx = {
            "contrato": {"numero": "CT-0001/2026", "tipo_servico": "RFO", "objeto": "Reforma de fachada",
                         "art_fiscalizacao": "ART-0001", "data_inicio": "2026-01-05", "prazo_dias": 365},
            "edificacao": {"nome": "Condomínio Sintético", "endereco": "Rua Sintética, 100"},
            "fiscal": {"nome": "Eng. Sintético", "crea": "0000000000/D-XX", "email": "x@example.com"},
            "executores": [{"razao_social": "Construtora Sintética", "cnpj": "00.000.000/0001-00"}],
            "nbrs": [{"codigo_nbr": "NBR 5674", "descricao": "Manutenção de edificações"}],
            "visitas": [
                {"seq_numero": v + 1, "data": "2026-03-10",
                 "servicos_executados": "\n".join(f"Serviço executado {j}: {LOREM[:90]}" for j in range(4)),
                 "observacoes": f"Observação A da visita {v + 1}.\nObservação B.",
                 "mao_obra": [{"funcao": f, "quantidade": 3} for f in ("Pedreiro", "Servente", "Pintor")],
                 "medicoes": [{"descricao": f"Item {j}", "quantidade": 10.5, "unidade": "m²"} for j in range(3)],
                 "fotos": [{"storage_key": k(), "legenda": f"Foto {f + 1} da visita {v + 1}"} for f in range(3)]}
                for v in range(n)
            ],
        }
    elif pipeline in ("ltip", "ltip_foto"):  # n ocorrências, 1 foto cada (ficha do LTIP)
        ctx = {
            "edificacao": {"nome": "Condomínio Sintético"}, "fiscal": {"nome": "Eng. Sintético", "crea": "0/D-XX"},
            "contrato": {"art_fiscalizacao": "ART-0001"}, "data_emissao": "2026-11-04",
            **{f"{s}_paragrafos": _par(3) for s in ("introducao", "objetivo", "objeto", "metodologia",
                                                    "documentacao_analisada", "consideracoes_preliminares",
                                                    "conclusao")},
            "ocorrencias": [
                {"seq_numero": i + 1, "sistema": sistemas[i % 8], "sistema_ordem": i % 8,
                 "subsistema": f"Subsistema {i % 5}", "subsistema_ordem": i % 5, "situacao": "Não conforme",
                 "classificacao": "Anomalia", "tipo_anomalia": "Endógena", "grau_risco": "MEDIO",
                 "prioridade": 3, "gut_gravidade": 3.0, "gut_urgencia": 3.0, "gut_tendencia": 2.0,
                 "localizacao": f"Pavimento {i % 12}", "descricao": LOREM, "recomendacao": LOREM[:160],
                 "fotos": [{"storage_key": k()}]}
                for i in range(n)
            ],
        }
    elif pipeline == "vistoria_cautelar":  # n figuras + 8 sistemas + todas as seções de texto
        from app.services.report_generator import vistoria_cautelar_pipeline as p

        html = (p.TEMPLATES_DIR / p.HTML_TEMPLATE_NAME).read_text(encoding="utf-8")
        import re

        secoes = set(re.findall(r"conteudo\.get\('(\w+)'", html))
        ctx = {
            "responsavel": {"nome": "Eng. Sintético", "titulo_profissional": "Engenheiro Civil",
                            "crea": "0/D-XX", "email": "x@example.com", "telefone": "(00) 0000-0000",
                            "qualificacoes": ["Especialista em Patologia"]},
            "obra": {"descricao": "Obra Sintética"}, "edificacao": {"nome": "Condomínio Sintético"},
            "data_emissao": "2026-11-04", "local_emissao": "Cidade Sintética",
            "conteudo": {s: _par(2) for s in secoes},
            "complementos": {"parecer_tecnico": "Recebimento com ressalvas"},
            "tabelas": {"identificacao": [{"aspecto_tecnico": f"Aspecto {i}", "descricao_detalhada": LOREM[:120]}
                                          for i in range(8)],
                        "plano_de_correcoes_remanescentes": [
                            {"item": str(i), "localizacao": "Garagem", "descricao_da_pendencia": LOREM[:120],
                             "metodologia_corretiva_indicada": LOREM[:120]} for i in range(15)]},
            "sistemas": [{"nome": s, "constatacoes": _par(3), "fundamentacao_tecnica": _par(1)} for s in sistemas],
            "figuras": [{"legenda": f"Figura sintética {i + 1}", "storage_key": k()} for i in range(n)],
            "assinatura_storage_key": k(), "capa_fundo_storage_key": k(),
        }
    elif pipeline == "vistoria_residencial":  # n fotos + 8 sistemas + todas as seções de texto
        from app.services.report_generator import vistoria_residencial_pipeline as p

        ctx = {
            "imovel": {"unidade": "Ap. 101"}, "edificacao": {"nome": "Residencial Sintético"},
            "fiscal": {"nome": "Eng. Sintético", "crea": "0/D-XX", "email": "x@example.com",
                       "telefone": "(00) 0000-0000", "qualificacoes": ["Engenheiro Civil"]},
            "data_emissao": "2026-11-04", "local_emissao": "Goiânia",
            "textos": {c: _par(2) for c in p.TEXTOS_CHAVES},
            "fotos": [{"legenda": f"Foto sintética {i + 1}", "storage_key": k()} for i in range(n)],
            "sistemas": [{"nome": s, "constatacoes": _par(3), "fundamentacao_tecnica": _par(1)} for s in sistemas],
        }
    else:
        raise ValueError(pipeline)
    return ctx, keys


def _template_ltip_com_foto(destino: Path) -> Path:
    """Mesmo template mínimo de tests/test_ltip_pipeline.py: isola o custo da foto no DOCX."""
    from docx import Document

    doc = Document()
    for linha in ("{%p for sistema in sistemas %}", "{%p for ocorrencia in sistema.ocorrencias %}",
                  "{{ ocorrencia.descricao }}", "{{ ocorrencia.foto }}", "{%p endfor %}", "{%p endfor %}"):
        doc.add_paragraph(linha)
    doc.save(str(destino))
    return destino


# --- uma medição (subprocesso) --------------------------------------------------


def cmd_uma(pipeline: str, formato: str, cenario: str, n: int) -> None:
    import importlib

    modulo = "ltip" if pipeline == "ltip_foto" else pipeline
    p = importlib.import_module(f"app.services.report_generator.{modulo}_pipeline")
    if formato == "pdf":
        import weasyprint  # noqa: F401  (importa antes da medição, como num worker já aquecido)
    else:
        import docxtpl  # noqa: F401
    ctx, keys = contexto(pipeline, n)
    fotos = {key: (FOTOS / cenario / key).read_bytes() for key in keys}
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / f"{pipeline}_{cenario}_{n}.{formato}"
    rss_antes = _rss_mb()
    t0 = time.perf_counter()
    if formato == "pdf":
        m = p.gerar_pdf(ctx, fotos, destino)
    elif pipeline == "ltip_foto":
        m = p.gerar_docx(ctx, fotos, destino, template_path=_template_ltip_com_foto(SAIDA / "ltip_foto_tpl.docx"))
    else:
        m = p.gerar_docx(ctx, fotos, destino)
    parede = time.perf_counter() - t0
    print(json.dumps({"pipeline": pipeline, "formato": formato, "cenario": cenario, "n": n,
                      "n_fotos": len(keys), "fotos_mb": round(sum(map(len, fotos.values())) / 2**20, 1),
                      "parede_s": round(parede, 3), "rss_antes_mb": round(rss_antes, 1),
                      "rss_pico_mb": round(_rss_mb(), 1),
                      **{c: (round(v, 3) if isinstance(v, float) else v) for c, v in m.items()}}))


def _sub(pipeline: str, formato: str, cenario: str, n: int) -> dict:
    out = subprocess.run([sys.executable, __file__, "uma", pipeline, formato, cenario, str(n)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def cmd_calibrar() -> None:
    for pipeline in ("rfo", "ltip", "vistoria_cautelar", "vistoria_residencial"):
        a, b = _sub(pipeline, "pdf", "otimizado", 10), _sub(pipeline, "pdf", "otimizado", 40)
        por_unidade = (b["n_paginas"] - a["n_paginas"]) / 30
        fixo = a["n_paginas"] - 10 * por_unidade
        n200 = round((200 - fixo) / por_unidade)
        print(json.dumps({"pipeline": pipeline, "pag_n10": a["n_paginas"], "pag_n40": b["n_paginas"],
                          "pag_por_unidade": round(por_unidade, 3), "pag_fixas": round(fixo, 1),
                          "n_para_200_pag": n200}))


def cmd_medir(reps: int, ns: dict[str, int], cenarios: list[str]) -> None:
    linhas = []
    with (BENCH / "bruto.jsonl").open("a", encoding="utf-8") as bruto:
        for rep in range(1, reps + 1):  # repetição por fora: espalha deriva térmica/IO entre combinações
            for cenario in cenarios:
                for pipeline, n in ns.items():
                    formatos = ("docx",) if pipeline == "ltip_foto" else ("pdf", "docx")
                    for formato in formatos:
                        r = {"rep": rep, **_sub(pipeline, formato, cenario, n)}
                        bruto.write(json.dumps(r) + "\n")
                        bruto.flush()
                        print(json.dumps(r), flush=True)
                        linhas.append(r)
    print("\n| Cenário | Pipeline | Formato | n | Fotos | Páginas | Tempo mediano (s) | min–máx (s) | RSS pico mediano (MB) | Tamanho (MB) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    grupos: dict[tuple, list[dict]] = {}
    for r in linhas:
        grupos.setdefault((r["cenario"], r["pipeline"], r["formato"]), []).append(r)
    for (cenario, pipeline, formato), rs in grupos.items():
        t = [r["parede_s"] for r in rs]
        print(f"| {cenario} | {pipeline} | {formato} | {rs[0]['n']} | {rs[0]['n_fotos']} | "
              f"{rs[0].get('n_paginas', '—')} | {statistics.median(t):.2f} | {min(t):.2f}–{max(t):.2f} | "
              f"{statistics.median(r['rss_pico_mb'] for r in rs):.0f} | {rs[0]['tamanho_bytes'] / 2**20:.1f} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("fotos").add_argument("--n", type=int, default=700)
    sp.add_parser("calibrar")
    u = sp.add_parser("uma")
    for nome in ("pipeline", "formato", "cenario"):
        u.add_argument(nome)
    u.add_argument("n", type=int)
    m = sp.add_parser("medir")
    m.add_argument("--reps", type=int, default=3)
    m.add_argument("--n", nargs="+", required=True, help="pipeline=n ...")
    m.add_argument("--cenarios", nargs="+", default=list(CENARIOS))
    a = ap.parse_args()
    if a.cmd == "fotos":
        cmd_fotos(a.n)
    elif a.cmd == "calibrar":
        cmd_calibrar()
    elif a.cmd == "uma":
        cmd_uma(a.pipeline, a.formato, a.cenario, a.n)
    else:
        cmd_medir(a.reps, {kv.split("=")[0]: int(kv.split("=")[1]) for kv in a.n}, a.cenarios)
```
