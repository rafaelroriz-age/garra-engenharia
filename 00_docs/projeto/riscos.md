---
title: Registro de Riscos — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-27
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
| **Mitigação** | Processamento assíncrono via Celery ou FastAPI BackgroundTasks. Compressão de imagens (Pillow) antes de inserir no PDF. Benchmark antes do release. |
| **Gatilho de escalada** | Tempo de geração > 60s em testes de carga com laudo de 200 páginas. |
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

### R-05 — Template DOCX do cliente não fornecido ou desatualizado

| Campo | Valor |
|---|---|
| **Probabilidade** | M |
| **Impacto** | M |
| **Prioridade** | Média |
| **Descrição** | A estratégia docxtpl exige o arquivo `.docx` original como template. Se o cliente não fornecer ou fornecer versão desatualizada, o DOCX gerado não será fiel. |
| **Mitigação** | Solicitar todos os templates Word ao cliente na fase de kickoff. Incluir no checklist de onboarding. |
| **Gatilho de escalada** | Início da fase de implementação sem os arquivos template. |
| **Responsável** | Gestor de Projeto |

---

## Riscos de Negócio / Requisitos

### R-06 — Lacunas [A ESCLARECER] não resolvidas antes da implementação

| Campo | Valor |
|---|---|
| **Probabilidade** | A |
| **Impacto** | M |
| **Prioridade** | Alta |
| **Descrição** | Existem 10 itens `[A ESCLARECER]` em `estudo-do-contexto.md`. Se não forem resolvidos antes da implementação, pode ocorrer retrabalho significativo (ex.: suporte offline muda toda a arquitetura frontend). |
| **Mitigação** | Sessão de validação com o cliente antes de iniciar cada fase de implementação. Os 10 itens devem ser priorizados por impacto arquitetural. |
| **Gatilho de escalada** | Início de sprint de implementação sem resolver lacunas de alto impacto (especialmente offline, multi-usuário, assinatura digital). |
| **Responsável** | Gestor de Projeto |

---

### R-07 — Requisito de offline completo descoberto tardiamente

| Campo | Valor |
|---|---|
| **Probabilidade** | M |
| **Impacto** | A |
| **Prioridade** | Alta |
| **Descrição** | Se confirmado que o engenheiro precisa registrar ocorrências sem internet (campo sem 4G), toda a estratégia de PWA precisa de Service Worker + IndexedDB + estratégia de sync, aumentando o escopo significativamente. |
| **Mitigação** | Resolver lacuna #3 de `estudo-do-contexto.md` na primeira reunião com o cliente. Se necessário, planejar offline como fase 2. |
| **Gatilho de escalada** | Confirmação de necessidade offline após início da implementação do frontend. |
| **Responsável** | Gestor de Projeto + Engenheiro Frontend |

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
| R-06 — Lacunas não resolvidas | Alta | **Ação imediata** |
| R-07 — Offline descoberto tarde | Alta | **Ação imediata** |
| R-01 — Fidelidade visual PDF | Alta | Mitigado (protótipo antecipado) |
| R-02 — Clipboard API | Média | Mitigado (fallback upload manual) |
| R-03 — Performance PDF | Média | Mitigado (processamento async) |
| R-04 — Complexidade modelo | Média | Mitigado (modelo ER definido) |
| R-05 — Template DOCX ausente | Média | Ação necessária (kickoff) |
| R-08 — Escopo crescente | Média | Mitigado (congelamento v1.0) |
| R-09 — Hospedagem indefinida | Baixa | Mitigado (Docker Compose agnóstico) |
| R-10 — Dados enviados a IA externa (RF-15) | Média | Ação necessária (escolher provedor — lacuna #13, B-04) |
