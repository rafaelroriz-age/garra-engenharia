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
| R-03 — Performance PDF | Média | Mitigado sob condição — benchmark real em 2026-08-05, ver [relatorio-benchmark-geracao-pdf-docx.md](relatorio-benchmark-geracao-pdf-docx.md) |
| R-04 — Complexidade modelo | Média | Mitigado (modelo ER definido) |
| R-05 — Original do cliente desatualizado | Baixa | Mitigado (templates e marca derivados dos originais arquivados — DEC-25/DEC-30); resta confirmar versão vigente (HT-02) |
| R-08 — Escopo crescente | Média | Mitigado (congelamento v1.0) |
| R-09 — Hospedagem indefinida | Baixa | Mitigado (Docker Compose agnóstico) |
| R-10 — Dados enviados a IA externa (RF-15) | Média | Ação necessária (escolher provedor — lacuna #13, B-04) |
