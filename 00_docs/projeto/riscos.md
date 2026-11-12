---
title: Registro de Riscos — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-09-17
---

# Registro de Riscos

> Legenda: **Probabilidade** (A=Alta, M=Média, B=Baixa) | **Impacto** (A=Alto, M=Médio, B=Baixo) | **Prioridade** = Prob × Impacto

---

## Riscos Técnicos

### R-01 — Fidelidade visual do PDF não atinge o padrão do cliente

| Campo | Valor |
|---|---|
| **Probabilidade** | M |
| **Impacto** | A |
| **Prioridade** | Alta |
| **Descrição** | O template HTML/CSS gerado pelo WeasyPrint pode ter diferenças sutis de tipografia, espaçamento ou paginação em relação ao documento Word original. |
| **Mitigação** | Criar protótipo do template HTML antes de implementar CRUD completo. Validar com o cliente em ciclos curtos (sprint 1 do frontend). |
| **Gatilho de escalada** | Diferença visual percebida pelo cliente em revisão formal do template. |
| **Responsável** | Engenheiro Backend + revisão do cliente |

---

### R-02 — Clipboard API não funciona em todos os contextos de uso

| Campo | Valor |
|---|---|
| **Probabilidade** | M |
| **Impacto** | M |
| **Prioridade** | Média |
| **Descrição** | `navigator.clipboard.read()` exige HTTPS e permissão explícita do browser. Em campo, o engenheiro pode estar em rede sem HTTPS configurado ou em browser que não suporta. |
| **Mitigação** | Implementar upload manual como fallback obrigatório (Opção B). Deploy sempre em HTTPS. Testar em Chrome Android (browser mais usado em campo). |
| **Gatilho de escalada** | Testes de usabilidade em campo mostrarem que o paste não funciona. |
| **Responsável** | Engenheiro Frontend |

---

### R-03 — Performance de geração de PDF com laudos de 200 páginas e 150+ fotos

| Campo | Valor |
|---|---|
| **Probabilidade** | M |
| **Impacto** | M |
| **Prioridade** | Média |
| **Descrição** | WeasyPrint pode ser lento para documentos grandes. O RNF-06 exige geração em menos de 60 segundos. |
| **Mitigação** | Processamento assíncrono via Celery ou FastAPI BackgroundTasks (ADR-06, ainda não implementado). Compressão de imagens (Pillow) antes de inserir no PDF/DOCX. |
| **Benchmark realizado (BL-22, 2026-08-05)** | Medição real com pipeline mínimo de fidelidade aproximada (ver [relatorio-benchmark-geracao-pdf-docx.md](relatorio-benchmark-geracao-pdf-docx.md)), 191 páginas / 570 fotos (pior caso ≥ RNF-06). Job único gerando PDF+DOCX (dual-pass, ADR-06 Seção 5): **sem otimização de imagem, 112,8s** (viola RNF-06, arquivos de 280 MB/138 MB); **otimizando a imagem a cada geração, 83,2s** (ainda viola RNF-06); **com as fotos já redimensionadas no upload (fix aplicado em BL-11, `MAX_LADO_ARMAZENADO_PX=2000`) + compressão adicional no embed do relatório, 44,2s** — dentro do limite, ~26% de margem. Risco rebaixado de "ação necessária" para **mitigado sob a condição de que BL-12/BL-13 reaproveitem o padrão de fotos já otimizadas no upload**, não a de recomprimir tudo a cada geração. |
| **Re-medição com pipelines finais (T17, 2026-11-04)** | Job PDF+DOCX em sequência, 1 execução por combinação: RFO 21,1 s (201 p., 150 fotos) e Vistoria Cautelar 34,2 s (200 p., 350 fotos) atendem RNF-06; Vistoria Residencial 56,7 s (200 p., 358 fotos) com 5 % de margem; **LTIP 63,2 s com só 137 p. (239 fotos) viola**. Gargalo: conversão do WeasyPrint (98–99,7 % do PDF); no LTIP, o container flex único de fichas (0,455 s/página, 3 a 5 vezes os demais). Medição incompleta (sem 3 execuções, sem cenário de 2000 px, sem LTIP de ~200 páginas) e sem leitura no MinIO nem upload. Ver [benchmark-pipelines-finais.md](../backlog-auto/benchmark-pipelines-finais.md) e DEC-40. **Gatilho de escalada atingido** para o LTIP. |
| **Otimização do LTIP (T20, 2026-11-04)** | Causa: o container `display: flex` único que atravessava as páginas tinha custo quadrático no WeasyPrint 70. Com linhas de fichas e fotos entregues por `url_fetcher`: 239 fotos 72,1 → **11,6 s** (129 p., 286 MB); 382 fotos (~200 p.) 154,5 → **19,3 s** (201 p., 411 MB). Mediana de 3 execuções, só PDF. **O LTIP passa a atender RNF-06 com folga**; o gatilho de escalada fica desarmado para ele. Falta o DOCX com foto (lacuna de BL-17) e a Vistoria Residencial (5 % de margem) seguem. Ver [ltip-desempenho.md](../backlog-auto/ltip-desempenho.md) e DEC-41 (proposta). |
| **Risco residual** | (1) Medição feita com pipeline aproximado, síncrono, sem Celery/Redis — a versão final (BL-12/BL-13, ADR-06) precisa ser re-medida quando implementada; (2) variação observada entre execuções locais (`tempo_registro_final_storage_e_db_s` variou de 1,7s a 9,2s) por contenção de I/O no ambiente de desenvolvimento — recomenda-se nova medição em ambiente de produção/staging dedicado antes do sign-off final de RNF-06. |
| **Gatilho de escalada** | Tempo de geração > 60s em teste de carga da implementação final (BL-12/BL-13) com laudo de 200 páginas. |
| **Responsável** | Engenheiro Backend |

---

### R-04 — Complexidade do modelo de dados para diferentes tipos de serviço

| Campo | Valor |
|---|---|
| **Probabilidade** | B |
| **Impacto** | A |
| **Prioridade** | Média |
| **Descrição** | RFO e LTIP têm estruturas diferentes (Visitas vs. Ocorrências). O modelo unificado pode se tornar complexo de manter, especialmente nas regras de validação por tipo. |
| **Mitigação** | Modelo ER definido em `arquitetura.md` separa claramente as entidades. Usar discriminated unions no Pydantic para schemas de tipo. Testes de validação por tipo de serviço. |
| **Gatilho de escalada** | Bugs de validação cruzando dados de RFO com LTIP. |
| **Responsável** | Arquiteto de Software + Engenheiro Backend |

---

### R-05 — Template do cliente não fornecido ou desatualizado

| Campo | Valor |
|---|---|
| **Probabilidade** | B |
| **Impacto** | B |
| **Prioridade** | Baixa |
| **Descrição** | O risco original assumia que a estratégia docxtpl exigia um `.docx` do cliente que nunca foi entregue. **Revisado em 2026-08-12 (DEC-25/ADR-13):** os originais existem em `01_output-context/` — `.xlsx`/`.xlsm` para RFO e RFIP, PDF final para LTIP e as duas vistorias — e passam a ser a base da derivação dos templates. O risco residual é apenas o cliente estar trabalhando com uma revisão mais recente do que a arquivada, gerando divergência de layout após a entrega. |
| **Mitigação** | Confirmar com o cliente que os arquivos arquivados são a versão vigente (HT-02/BL-19) antes do sign-off de fidelidade (HT-09). Manter o `layout.json` como camada intermediária versionada: uma revisão nova do original exige apenas reexecutar o script de extração, não reescrever os templates à mão. |
| **Gatilho de escalada** | Cliente informar que o modelo em uso difere do arquivado, ou reprovação de fidelidade em HT-09. |
| **Responsável** | Gestor de Projeto |

---

## Riscos de Negócio / Requisitos

### R-06 — Lacunas [A ESCLARECER] não resolvidas antes da implementação — **ENCERRADO (2026-09-17)**

| Campo | Valor |
|---|---|
| **Probabilidade** | — |
| **Impacto** | — |
| **Prioridade** | Encerrado |
| **Descrição** | O risco cobria o retrabalho decorrente de implementar sobre requisitos ambíguos. **Não se materializou:** as três lacunas de maior impacto arquitetural (offline #3, multiusuário #2 e assinatura digital #9) foram resolvidas com o cliente em 2026-09-10 (DEC-26/27/28) e as seis restantes (#1, #4, #5, #7, #8, #10) foram fechadas em 2026-09-17 por [DEC-29](decisoes.md#dec-29--fechamento-das-lacunas-remanescentes-blocos-2-e-3-encerramento-do-bloqueio-b-01), adotando em cada caso a posição de menor impacto sobre o que já estava entregue — nenhuma exigiu refazer código. O bloqueio **B-01 foi encerrado**. |
| **Mitigação** | Encerrada. Permanece aberta apenas a escolha do provedor de IA (lacuna #13), tratada em **R-10/B-04**, e o destino externo do backup (RNF-08), que é escolha operacional. Se o cliente revisar alguma das posições de DEC-29, o impacto é localizado: só #10 gerou campos novos (BL-15). |
| **Gatilho de escalada** | — |
| **Responsável** | — |

---

### R-07 — Requisito de offline completo descoberto tardiamente — **ENCERRADO (2026-09-10)**

| Campo | Valor |
|---|---|
| **Probabilidade** | — |
| **Impacto** | — |
| **Prioridade** | Encerrado |
| **Descrição** | O risco cobria a possibilidade de o cliente exigir registro sem internet, o que obrigaria a reescrever a camada de dados do frontend (Service Worker de escrita + IndexedDB + fila de sincronização). **Não se materializou:** o cliente confirmou em 2026-09-10 (lacuna #3) que há cobertura 4G/Wi-Fi em todas as edificações inspecionadas. |
| **Mitigação** | Encerrada. A posição online-first virou decisão definitiva da v1.0 (DEC-26/ADR-15, Seção 10.8 de `arquitetura.md`). Uma eventual necessidade futura entra como incremento arquitetural dedicado, com replanejamento de escopo e cronograma. |
| **Gatilho de escalada** | — |
| **Responsável** | — |

---

### R-08 — Escopo de tipos de documento cresce durante desenvolvimento

| Campo | Valor |
|---|---|
| **Probabilidade** | M |
| **Impacto** | M |
| **Prioridade** | Média |
| **Descrição** | O cliente pode solicitar novos tipos de relatório (ex.: Relatório de Patologias, Orçamento Técnico) não previstos no escopo inicial. |
| **Mitigação** | Congelar escopo da v1.0 formalmente. Novos tipos entram como v1.1 com estimativa separada. |
| **Responsável** | Gestor de Projeto |

---

## Riscos de Infraestrutura / Deploy

### R-09 — Preferência de hospedagem não definida

| Campo | Valor |
|---|---|
| **Probabilidade** | B |
| **Impacto** | M |
| **Prioridade** | Baixa |
| **Descrição** | [A ESCLARECER] O cliente ainda não definiu se quer o sistema local (notebook) ou em nuvem. Docker Compose é suficiente para local; nuvem requer Railway/Render ou VPS. |
| **Mitigação** | Resolver na reunião de kickoff. O Docker Compose produzido funciona em ambos os cenários sem mudança de código. |
| **Responsável** | Gestor de Projeto + Engenheiro de Software |

---

### R-10 — Envio de dados a provedor externo de IA para geração de legendas técnicas (RF-15)

| Campo | Valor |
|---|---|
| **Probabilidade** | M |
| **Impacto** | M |
| **Prioridade** | Média |
| **Descrição** | A geração assistida de legendas (RF-15, DEC-21) envia fotos/descrições de imóveis de clientes a um provedor de IA (LLM) externo. Isso levanta questões de privacidade/LGPD (retenção e uso dos dados pelo provedor), custo recorrente por chamada e risco de a legenda sugerida conter erro factual ("alucinação") caso seja aceita sem revisão criteriosa. |
| **Mitigação** | RN-16/RN-17 exigem que toda legenda gerada por IA seja sempre uma minuta revisável, nunca incluída automaticamente no relatório; escolher provedor com política de retenção/privacidade adequada e, se possível, sem uso dos dados para treinamento (lacuna #13); prompt-sistema já instrui a IA a não inventar dados e a sinalizar incerteza (`necessita_revisao_profissional`). |
| **Gatilho de escalada** | Provedor de LLM não oferecer garantias contratuais de privacidade, ou custo por chamada inviabilizar o uso em volume (150+ fotos por laudo). |
| **Responsável** | Gestor de Projeto + Engenheiro Backend |

---

## Resumo de Prioridades

| Risco | Prioridade | Status |
|---|---|---|
| R-06 — Lacunas não resolvidas | — | **Encerrado (2026-09-17)** — todas as lacunas de requisito fechadas (DEC-26/27/28 e DEC-29) |
| R-07 — Offline descoberto tarde | — | **Encerrado (2026-09-10)** — cliente confirmou cobertura 4G/Wi-Fi (DEC-26) |
| R-01 — Fidelidade visual PDF | Alta | Mitigado (protótipo antecipado) |
| R-02 — Clipboard API | Média | Mitigado (fallback upload manual) |
| R-03 — Performance PDF | Alta | **Reduzido (2026-11-04, T20)** — o LTIP caiu para 11,6 s (239 fotos) e 19,3 s (~200 páginas); resta a Vistoria Residencial com 5 % de margem (T28, 2026-11-05, estendeu o `url_fetcher` a RFO/Cautelar/Residencial sem medir), o DOCX do LTIP sem foto e a medição em host dedicado. Histórico: **reaberto** pela re-medição T17 com os pipelines finais: LTIP viola RNF-06 (63,2 s com 137 páginas) e a Vistoria Residencial passa por 5 %; RFO e Cautelar atendem. Ver [benchmark-pipelines-finais.md](../backlog-auto/benchmark-pipelines-finais.md) e DEC-40 |
| R-04 — Complexidade modelo | Média | Mitigado (modelo ER definido) |
| R-05 — Original do cliente desatualizado | Baixa | Mitigado (templates e marca derivados dos originais arquivados — DEC-25/DEC-30); resta confirmar versão vigente (HT-02) |
| R-08 — Escopo crescente | Média | Mitigado (congelamento v1.0) |
| R-09 — Hospedagem indefinida | Baixa | Mitigado (Docker Compose agnóstico) |
| R-10 — Dados enviados a IA externa (RF-15) | Média | Ação necessária (escolher provedor — lacuna #13, B-04; T29 (2026-11-05) soma como bloqueio de produção: sem limite de taxa/custo e sem limite da saída do LLM, DEC-42). Em 2026-11-04 (T23) o contrato `LegendaIAClient` e o Fake isolam o provedor, mas nenhum cliente real existe **Atualização (T63/T65, 2026-11-11, DEC-49 proposta):** cliente DeepSeek implementado, só texto e contexto minimizado (regex para CPF, CNPJ, e-mail e telefone, sem nome de pessoa); política de retenção do provedor ainda indefinida e nenhuma chamada real feita **Atualização (T68, 2026-11-12, DEC-52 proposta):** custo agora medido por `chamadas_ia` e `GET /ia/uso`, e o cache local evita regeração; preços reais pendentes (IA-07) e a coluna `resposta` sem política de retenção |
| R-11 — Ambiente de desenvolvimento não reproduzível (pytest × pytest-asyncio, ruff, Docker, Python 3.12) | Média → Baixa | Parcialmente mitigado (T02 e T04); restam o ruff na CI e a suíte de integração (DEC-31) |
| R-12 — Vulnerabilidades de dependências do frontend (Next.js 14.2.35 crítico em produção) | Alta | Ação necessária (DEC-32 proposta; T03) |
| R-13 — Lacunas de validação no CRUD de Ocorrências (enums, existência, `PUT`) | Média | Em mitigação: correção aplicada na T08, testes ainda não executados (DEC-34 proposta) |
| R-14 — PDF dos templates e pipelines nunca renderizado de verdade; suíte completa sem PostgreSQL | Média | Ação necessária (rodar no container de `05_infra/`) T45 (2026-11-10): `test_rfo_contexto.py` também não rodou (sem PostgreSQL e sem Pango no Windows); T46 (2026-11-10): os 9 testes de integração de `test_relatorios_rfo_api.py` também não rodaram e a coleta da suíte completa cai em `test_rfo_contexto.py` (import de WeasyPrint no topo); T47–T51 (2026-11-11): testes de banco/endpoint de T48, T49 e T50 também não rodaram **Atualização (T64, 2026-11-12):** primeira suíte completa no container: 697 passed, 15 failed, 14 errors, 3 skipped, 5 xfailed; PDFs reais dos 5 tipos gerados, **conferência visual (HT-09) ainda pendente** |
| R-15 — Lacunas de regra e segurança em Visitas e Fotos | Média | **Reduzido (2026-11-04, T19/T21)** — correções aplicadas e testadas; abertos: L15 (vínculo usuário↔contrato), `UNIQUE(storage_key)`, URL pré-assinada, limite de corpo, suíte completa numa só execução (T22: 34 falhas anteriores, 14 delas testes de banco que falham por `asyncio.run` derrubar o event loop em 7 arquivos; proposta: helper único em `tests/conftest.py`); DEC-38/DEC-39 ainda propostas. T25 (2026-11-05) confirmou a falha de `asyncio.run` em `test_fotos.py` e `test_rbac_auxiliar.py` (22 falhas ao rodar junto dos testes `async`, que passam isolados) e que a suíte completa estoura a memória neste Windows **Atualização (T64, 2026-11-12):** na suíte única do container, 6 dos 29 itens com falha passam isolados (efeito R-15) e 23 persistem em testes antigos (ver R-21) |

### R-11 — Ambiente de desenvolvimento não reproduzível

| Campo | Valor |
|---|---|
| **Origem** | Diagnóstico T01 (2026-11-04), em [00_docs/backlog-auto/diagnostico.md](../backlog-auto/diagnostico.md) |
| **Descrição** | `requirements.txt` aceita `pytest>=9.1.1,<10` com `pytest-asyncio>=0.23,<1.0`; a combinação resolvida (pytest 9.2.0 + pytest-asyncio 0.23.3) falha na coleta (`INTERNALERROR`, 0 testes executados — causa provável, não isolada). `ruff check .` acusa 214 achados (B008 87, F821 38, I001 36…), sem configuração de ruff encontrada; a CI instala o ruff sem fixar versão. Python 3.14 do sistema não instala as dependências (Pillow); exige 3.12. Docker ausente na máquina diagnosticada, então PostgreSQL/MinIO e a suíte de integração não rodam. |
| **Probabilidade / Impacto** | Média / Média — a CI (`ci.yml`) pode divergir do que roda localmente |
| **Mitigação** | **Feito:** T02 alinhou `pytest-asyncio>=1.4.1,<1.5` (coleta: 0 para 139 testes); T04 versionou `04_backend/ruff.toml` e zerou os 214 achados (os F821 eram falsos positivos). **Pendente:** remover `continue-on-error` do ruff e fixar a versão no `ci.yml` (arquivo `.yml`, tarefa de código); instalar Docker e rodar a suíte de integração (as 2 falhas e 85 erros das duas tarefas vinham de banco sem schema, não de código); usar venv Python 3.12. Ver DEC-31. |

### R-12 — Vulnerabilidades de dependências do frontend

| Campo | Valor |
|---|---|
| **Origem** | Tarefa T03 (2026-11-04), em [00_docs/backlog-auto/npm-audit.md](../backlog-auto/npm-audit.md) |
| **Descrição** | `npm audit` em `03_frontend`: 30 pacotes vulneráveis (2 críticos, 11 altos, 17 moderados); 13 em produção. O crítico relevante é `next` 14.2.35 (RCE em Image Optimization, DoS em Server Components, SSRF, cache poisoning), exposto no container `node:20-alpine`; a correção está só em 15.5.x/16.x (major, possível React 19). `fabric` 6.9.1 (XSS em exportação SVG) e a cadeia `canvas`/`tar` têm exposição baixa/média. Se `/_next/image` fica acessível: não determinado sem teste. |
| **Probabilidade / Impacto** | Média / Alta |
| **Atualização (T07, 2026-11-04)** | Item 1 da DEC-32 aplicado: achados 30 → 26 (produção 13 → 10), mas Next 14.2.35 crítico, fabric e `brace-expansion` 1.1.16 permanecem. Risco continua aberto. |
| **Mitigação** | DEC-32 (proposta): `npm audit fix` sem `--force` nos 5 pacotes sem major; upgrade do Next antes do próximo deploy; fabric 7 com teste do editor (RF-14); nunca `--force`. |

### R-13 — Lacunas de validação no CRUD de Ocorrências

| Campo | Valor |
|---|---|
| **Origem** | Tarefa T06 (2026-11-04), em [revisao-regras-ocorrencias.md](revisao-regras-ocorrencias.md) |
| **Descrição** | O backend aceita situação e classificação fora do enum (RN-05), não verifica a existência de sistema, subsistema e inspeção (erro 500 em vez de 404/422), aceita subsistema de outro sistema e deixa o `PUT` mover a ocorrência para outra inspeção ou apagar o `seq_numero`. Os testes que cobrem as lacunas ainda não rodaram por falta de PostgreSQL. |
| **Probabilidade / Impacto** | Média / Média — dados inconsistentes e relatórios (LTIP) agrupados de forma errada |
| **Mitigação** | DEC-34 (proposta). **Feito (T08, 2026-11-04):** correções L1–L7 no service, repositório e endpoint. **Pendente:** rodar `test_ocorrencias_regras.py` e a suíte de Ocorrências com PostgreSQL no ar (nenhum teste foi executado na T08); só então fechar o risco. |

### R-14 — PDF nunca renderizado de verdade; suíte completa não executada nos lotes recentes

| Campo | Valor |
|---|---|
| **Origem** | Lote T05–T13 (2026-11-04), em [vistoria-cautelar-pipeline.md](../backlog-auto/vistoria-cautelar-pipeline.md), [vistoria-residencial-pipeline.md](../backlog-auto/vistoria-residencial-pipeline.md) e [rfip-templates.md](../backlog-auto/rfip-templates.md) |
| **Descrição** | Os templates e pipelines de LTIP, Vistoria Cautelar, Vistoria Residencial e RFIP foram testados só em HTML (Jinja2) e DOCX. O teste de PDF é pulado porque o WeasyPrint não roda no Windows (sem Pango/GTK) e não há Docker nem PostgreSQL (`localhost:5433`) nas máquinas dos jobs. Por isso a conferência visual (HT-09) não aconteceu e a suíte completa não foi validada: T12 relatou 6 falhas e 104 erros e T13 6 falhas e 91 erros, todos em testes que dependem de banco (e de um `greenlet` funcional no venv local); nenhum foi diagnosticado um a um. Pontos específicos do RFIP: logo reduzida para caber na margem e escala de impressão não aplicada às fontes (2,6% de diferença). |
| **Probabilidade / Impacto** | Alta / Média — defeitos de layout só apareceriam na entrega ao cliente |
| **Atualização T17 (2026-11-04)** | O benchmark de T17 renderizou PDFs reais dos 4 pipelines em container Docker (WeasyPrint), o que mostra que a conversão roda e fornece tempos, mas **não houve conferência visual** contra os originais nem `pytest` completo; o risco continua aberto para fidelidade. |
| **Mitigação** | Subir `05_infra/docker-compose.yml`, rodar o `pytest` completo e os testes de PDF no container e fazer a conferência visual lado a lado com os originais (HT-09). Só então fechar o risco. |

### R-15 — Lacunas de regra e segurança em Visitas e Fotos; testes de lacuna não executados

| Campo | Valor |
|---|---|
| **Origem** | Lote T14–T17 (2026-11-04), em [revisao-regras-visitas.md](../backlog-auto/revisao-regras-visitas.md) e [revisao-regras-fotos.md](../backlog-auto/revisao-regras-fotos.md) |
| **Descrição** | A revisão de BL-10 achou 18 lacunas (RN-01/RN-02: sem unicidade de `seq_numero` nem de visita por dia, data futura, tipo de inspeção, quantidades) e a de BL-11 achou 9, entre elas uma de segurança: o vínculo de foto aceita `storage_key` do cliente, permitindo apontar para objeto de outro contrato e apagá-lo (A01), e a foto de celular em pé sai deitada no relatório (sem `exif_transpose`). Os testes de lacuna (`test_visitas_lacunas.py`, `test_fotos_lacunas.py`) afirmam o comportamento correto, foram só coletados e **nunca executados**: a coluna "falha hoje" dos Docs é análise estática. |
| **Probabilidade / Impacto** | Alta / Média (Alta para a falha de segurança de fotos) |
| **Mitigação** | Subir `05_infra/docker-compose.yml`, aplicar `alembic upgrade head`, rodar os dois arquivos e confirmar quais falham; corrigir conforme DEC-38 e DEC-39 (a falha de `storage_key` primeiro). Confirmar com o dono as interpretações de RN-01/RF-03 (data futura, só RFO) antes de corrigir. |
| **Atualização (T19/T21, 2026-11-04)** | T19 corrigiu 8 das 9 lacunas de fotos, inclusive a de segurança: `storage_key` só no padrão `fotos/<uuid>.<ext>`, existente no bucket e ainda não vinculada (422/409), mais `exif_transpose` e `DELETE /fotos/upload`; testes `test_fotos*`/`test_rbac_auxiliar`: 44 passed, 1 skipped. T21 corrigiu as 18 lacunas de Visitas exceto L15 (`xfail`), com migration `e5a1c3f7b9d2` (aborta se houver data duplicada, renumera `seq_numero` duplicado). **Resta:** `UNIQUE(storage_key)` (hoje só na aplicação, com janela de corrida), vínculo usuário↔contrato (DEC-27, qualquer membro da equipe ainda edita foto/visita de qualquer contrato), URL pré-assinada, limite de corpo no proxy, teste do teto de 50 Mpx, aplicar a migration em produção e rodar a suíte completa (36 falhas/18 erros reportados pela T19 vêm de event loop e dependências ausentes, sem relação com fotos, mas sem linha de base). Docs: [fotos-correcoes.md](../backlog-auto/fotos-correcoes.md), [visitas-correcoes.md](../backlog-auto/visitas-correcoes.md). |
| **Atualização (T26, 2026-11-05)** | O frontend (`foto-upload.tsx`, `OrigemFoto` em `lib/types.ts`) vincula upload manual com `origem: "upload"`, mas o backend aceita só `upload_manual`, `lightshot` e `clipboard` (DEC-39 C). Pela leitura do código, o vínculo de upload por arquivo recebe 422; não testado contra a API. Corrigir no frontend e cobrir com o spec de stack real |
| **Atualização (T27/T29, 2026-11-05)** | T27 corrigiu o frontend para `upload_manual` e constatou que o backend **não valida** `origem` (sem 422; a leitura da T26 estava errada; DEC-43). T29 confirmou L15 como IDOR entre contratos (SEG-IA-07): qualquer membro da equipe lê, edita, aprova e remove fotos de qualquer contrato, e agora também dispara IA paga. 9 achados novos de segurança em legenda IA (DEC-42), nenhum corrigido; 9 testes da T29 não rodaram sem MinIO |
| **Atualização (T30, 2026-11-05)** | O storage foi confirmado compatível com artefatos de IA e ganhou `exists`/`list_keys`/`listar_orfaos` (só leitura). Uploads sem vínculo ainda se acumulam: não há job de limpeza (política proposta em DEC-44). Testes de integração com MinIO não foram executados. |
| **Atualização (T31/T32, 2026-11-06)** | `origem` do vínculo agora é enum fechado no backend (422), mas registros antigos fora do enum continuam sem normalização nem CHECK (DEC-43). O relatório de órfãos em dry-run existe (`app.scripts.relatorio_orfaos`, idade > 24 h), porém ninguém o agenda nem o executou contra o storage real; nada é apagado e uploads sem vínculo ainda se acumulam (DEC-44). Testes de endpoint do T31 pularam sem PostgreSQL |
| **Atualização (T33–T35, 2026-11-06)** | Legenda IA: o `auxiliar` não aprova mais (403) e editar/regerar legenda aprovada invalida a aprovação (T33/T34); `gerar` tem limite de taxa e a saída do LLM é truncada e saneada (T35). **Riscos que ficam:** (1) o limite é por usuário e em memória por processo, então com vários workers o teto efetivo é multiplicado e não há orçamento global de custo; (2) os testes com banco real e MinIO desses pontos não rodaram; (3) SEG-IA-06 e L15/SEG-IA-07 seguem abertos; (4) o campo «Legenda da foto» no card é uma segunda porta de edição sem o aviso de invalidação. |
| **Atualização (T37/T38, 2026-11-07)** | Cautelar e Residencial não imprimem mais sugestão de IA (T37). **Riscos que ficam:** (1) LTIP e RFIP ainda sem a regra (T36 bloqueada); (2) nenhum pipeline avisa ao gerar relatório com fotos IA em rascunho; (3) o caminho PDF dos testes novos não rodou (sem WeasyPrint/GTK no Windows); (4) a anotação cria foto nova e a invalidação da aprovação só reage a mudança de `legenda`, não de imagem; (5) CORS do bucket para `toDataURL` não verificado em MinIO real. |
| **Gatilho de escalada** | Qualquer uso de BL-10/BL-11 com dados reais antes de aplicar a migration e conferir os dados duplicados de produção. |
| **Responsável** | Engenheiro Backend |

### R-17 — Alembic com duas heads (T49 × T36) — **mitigado, migration ainda não aplicada**

| Campo | Valor |
|---|---|
| **Origem** | Lote T47–T51 (2026-11-11), em [relatorio-unicidade.md](../backlog-auto/relatorio-unicidade.md); confirmado com `alembic heads` na `main` mesclada |
| **Descrição** | `e5a1f0c2b7d4` (UNIQUE de `relatorios`, T49) e `f7c2a9d4e6b1` (legendas IA, T36, via `e5a1c3f7b9d2`) partem da mesma base `d3b7c9e4f1a2`. `alembic upgrade head` falha com múltiplas heads. A migration da T49 também nunca rodou upgrade/downgrade/upgrade e aborta se houver duplicatas em `relatorios` |
| **Probabilidade / Impacto** | Alta / Alta (deploy e CI com banco bloqueados) |
| **Mitigação** | Criar migration de merge (`alembic merge`) ou religar `down_revision` da T49 a `f7c2a9d4e6b1`; depois testar upgrade/downgrade/upgrade num banco limpo e conferir duplicatas antes de aplicar em produção |
| **Gatilho de escalada** | Qualquer `alembic upgrade head` em ambiente compartilhado ou deploy. |
| **Atualização (2026-11-11)** | A migration de merge `e5a1c7d9b3f4` (T55) unificou as duas; com a `a9c3e5f7b1d2` (T57) a head é única (`alembic upgrade`/`downgrade`/`check` limpos num banco descartável). Falta aplicar em dev: o banco de `05_infra` segue em `f7c2a9d4e6b1` e a UNIQUE de `relatorios` não existe nele. |
| **Responsável** | Engenheiro Backend |

### R-16 — Deploy por VPS e rotina de backup com falhas conhecidas

| Campo | Valor |
|---|---|
| **Origem** | Lote T39–T42 (2026-11-07), em [legenda-ia-env-deploy.md](../backlog-auto/legenda-ia-env-deploy.md), [backup-verificacao.md](../backlog-auto/backup-verificacao.md) e [ci-lint-bloqueante.md](../backlog-auto/ci-lint-bloqueante.md) |
| **Descrição** | (1) `05_infra/docker-compose.prod.yml` linha 89 (`image:` do backend, `${IMAGE_TAG:?… ex.: …}`) não é YAML válido; o compose de produção por VPS não sobe até corrigir (o Render não é afetado). (2) O script de restore segue para o `pg_restore --clean` mesmo se o dump `pre-restore` falhar (DEC-45). (3) O lint do backend não bloqueia o CI (`continue-on-error: true`); os erros foram zerados em 2026-11-10 pela T43, falta a aprovação da DEC-46 para torná-lo bloqueante. (4) `docker compose config` e `shellcheck` não rodaram por falta de Docker/ferramenta; as 8 variáveis `LEGENDA_IA_*` talvez precisem ser definidas à mão no serviço real do Render. |
| **Probabilidade / Impacto** | Média / Alta (restore sem rede de segurança); Média / Média (demais) |
| **Mitigação** | Pôr a `image:` entre aspas e validar com `docker compose config`; aprovar DEC-45 antes de qualquer uso real do restore; tarefa de limpeza do ruff e DEC-46; conferir as variáveis no Dashboard do Render. |
| **Gatilho de escalada** | Primeiro restore em produção, ou primeiro deploy por VPS, sem as correções acima. |
| **Responsável** | Engenheiro DevOps |

### R-20 — Lacunas do frontend de relatório: responsável sem edição e assinatura órfã

| Campo | Valor |
|---|---|
| **Origem** | T62, em [v1-frontend-relatorio.md](../backlog-auto/v1-frontend-relatorio.md) |
| **Descrição** | (1) Não há `PUT/PATCH /responsaveis/{id}`: a tela só cadastra, então título, qualificações e assinatura não podem ser acrescentados a um responsável existente. (2) A imagem da assinatura sobe por `POST /fotos/upload`, fica sob o prefixo `fotos/` e não é uma `Foto`: o relatório de órfãos (DEC-44) a lista como órfã, e o backend não valida `assinatura_storage_key`. (3) O frontend envia o conteúdo completo (PUT substitui), o que congela os textos padrão no primeiro salvamento. (4) `window.open` após `await` pode ser bloqueado no iOS/Safari. (5) O teste `(e)` de `portal.spec.ts` espera o comportamento anterior à T54. |
| **Probabilidade / Impacto** | Média / Baixa |
| **Mitigação** | Criar a rota de edição de responsável (auditor); rota própria de assinatura com prefixo `assinaturas/` ou incluí-la no conjunto de chaves vinculadas do script de órfãos; testar o download no celular e, se preciso, trocar por `window.location.assign`; reescrever o teste `(e)`. |
| **Gatilho de escalada** | Limpeza de órfãos real (sem dry-run) ou o cliente pedir assinatura em responsável já cadastrado |
| **Responsável** | Engenheiro Backend + Engenheiro Frontend |

### R-21 — Testes antigos falhando na suíte completa e migration que falha no banco de desenvolvimento

| Campo | Valor |
|---|---|
| **Origem** | T64, em [v1-amostras-ht09.md](../backlog-auto/v1-amostras-ht09.md) |
| **Descrição** | 23 itens persistem isolados, todos em testes ou comportamento já existentes: `test_ocorrencias_prioridade.py` (5; `headers=auth["Authorization"]` não serve ao `httpx` 0.28), `test_ocorrencias_regras.py` (13 erros; o fixture cria 2 inspeções para o mesmo contrato, mas `inspecoes.contrato_id` é UNIQUE), `test_seguranca_legenda_ia.py` (4; causa só analisada em um), `test_relatorio_unicidade.py` (1 erro de teardown, `MissingGreenlet`). Há 2 skips desatualizados. Além disso a migration `e5a1f0c2b7d4` falha no banco `garra_engenharia` (2 linhas `BENCH-01` duplicadas em `relatorios`, inspeção `22db6dc2-...`), que está em `f7c2a9d4e6b1`. |
| **Probabilidade / Impacto** | Alta / Média (a suíte não pode ser porta de qualidade enquanto falhar, e o dev não sobe de revisão) |
| **Mitigação** | Corrigir os fixtures e os testes citados; analisar os 3 testes de `seguranca_legenda_ia` restantes; remover ou renumerar as 2 linhas `BENCH-01` com aval do dono e rodar `alembic upgrade head` no dev; remover os bancos temporários `garra_bl34_tmp2`, `garra_tmp_v105` e `garra_demo_v1` quando não forem mais necessários. |
| **Gatilho de escalada** | Primeiro deploy ou primeira exigência de CI com a suíte completa |
| **Responsável** | Engenheiro Backend |

### R-18 — T66 e T67 marcadas `done` com entrega parcial; golden set inexistente

| Campo | Valor |
|---|---|
| **Origem** | Fechamento do lote T57–T67 (2026-11-11). As integrações de T66 e T67 trouxeram só os commits `wip(backend)` |
| **Descrição** | T66: prompt compacto em 37,3% do original (alvo ≤ 35%) e seed sem teste nem Doc. T67: só o harness `avaliar_legenda_ia.py` (597 linhas), sem extrator, sem `golden_legenda.jsonl`, sem teste nem Doc. T68 (telemetria e cache) foi entregue (2026-11-12) sem depender delas na prática; T69 ainda depende. Sem golden set não há como medir se prompt compacto, RAG ou troca de modelo melhora ou piora a legenda |
| **Probabilidade / Impacto** | Alta / Média (o prompt compacto pode ir ao seed sem avaliação, com risco de regressão na qualidade técnica da legenda) |
| **Mitigação** | Reabrir T66 e T67 (o BACKLOG é do integrador) e concluir: testes do seed, ruff, Doc, extrator, golden set ≥ 60 casos anonimizados e teste do replay. Não ativar o prompt compacto em produção antes disso |
| **Gatilho de escalada** | Qualquer execução do seed em ambiente compartilhado, ou o início de T68/T69 sobre T66/T67 |
| **Responsável** | Engenheiro Backend |

### R-19 — Testes de legenda IA e emissão sem execução completa no ambiente Windows

| Campo | Valor |
|---|---|
| **Origem** | Lote T57–T67, em [ia-contexto-legenda.md](../backlog-auto/ia-contexto-legenda.md), [v1-legenda-ia-deepseek.md](../backlog-auto/v1-legenda-ia-deepseek.md) e [v1-emissao-generica.md](../backlog-auto/v1-emissao-generica.md) |
| **Descrição** | No Python do Windows, `passlib`×`bcrypt` quebra as fixtures de usuário (`password cannot be longer than 72 bytes`), então de 32 a 38 testes de endpoint de legenda IA (`endpoints`, `aprovacao`, parte de `seguranca`, `fotos`) deram erro de *setup* em T63 e T65 e não rodaram. WeasyPrint sem `libpango` impede coletar `test_rfo_contexto.py`. T57, T58 e T60 rodaram em container descartável da imagem `05_infra-backend`; a tag é compartilhada entre worktrees e a imagem não traz `pytest-asyncio` compatível. Na `main`, a T58 viu 12 falhas e 19 erros pré-existentes na suíte completa. Sem chave, a DeepSeek nunca foi chamada de verdade |
| **Probabilidade / Impacto** | Alta / Média |
| **Mitigação** | Rodar a suíte completa em container com `bcrypt<4.1` e `pytest-asyncio` (`docker compose build backend`; uma tag por worktree); reexecutar os testes de endpoint de legenda IA; um teste manual com chave real antes de ligar `deepseek` fora de desenvolvimento. `ruff check .` ainda acusa 10 erros em `e5a1f0c2b7d4_*`, `test_fotos_storage_key_unico.py`, `test_portal_versoes_relatorio.py` e `test_relatorio_unicidade.py` (DEC-46 pede zero antes do CI bloquear) |
| **Gatilho de escalada** | Deploy de legenda IA ou de emissão em produção sem a suíte completa verde |
| **Responsável** | Engenheiro DevOps |
