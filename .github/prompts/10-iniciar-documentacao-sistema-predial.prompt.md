---
description: "Prompt mestre para iniciar a documentação e arquitetura do sistema de automação de relatórios prediais da Garra Engenharia. Ativa os agentes Estudo do Contexto e Arquiteto de Software em sequência."
---
## Contexto

O cliente é o **Eng. Civil Esp. Roniel Ribeiro Costa** (CREA-GO nº 1020613386/D-GO), profissional autônomo que presta serviços de:

- **Relatórios de Fiscalização** de obras — acompanhamento diário de serviços, mão de obra, medições e registros fotográficos
- **Laudos Técnicos de Inspeção Predial** (NBR 16747) — avaliação de sistemas prediais com classificação de anomalias, falhas, grau de risco e prioridade de intervenção
- **Vistorias Cautelares de Recebimento** — avaliação do estado de imóveis antes/após reformas
- **Vistorias de Imóvel Residencial** — diagnóstico de patologias, medições e parecer técnico
- **Relatórios Fotográficos de Inspeção Predial** — documentação fotográfica com legendas técnicas

Os documentos de referência já foram convertidos para `.md` e estão em `00_docs/convertidos/`:
- `Relatorio_de_Fiscalizacao_1.md` — formulário xlsm com abas diárias, dados da obra, mão de obra, medições e NBRs de referência
- `Relatorio_de_Fiscalizacao.md` — modelo de relatório de fiscalização de obra
- `Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md` — laudo de 199 páginas com sumário completo
- `Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md` — vistoria cautelar de reforma
- `Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md` — vistoria residencial
- `Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md` — relatório fotográfico
- `RFO_INSPECAO.md` — gabarito de inspeção predial com todos os sistemas prediais, classificações, prioridades, tipos de anomalia/falha, graus de risco e localizações
- `COND.md` — dados de condomínios

**Ferramenta essencial de captura de imagem:** o cliente usa o **Lightshot** (https://app.prntscr.com/pt-br/index.html) para capturar e anotar prints de tela durante as vistorias. O sistema deve integrar-se a esse fluxo (upload, organização e vinculação de imagens aos ativos inspecionados).

**Vocabulário técnico identificado nos documentos:**
- **Sistemas prediais inspecionados:** Aberturas e Fechamentos, Acessibilidade, Circulações, Cobertura e Telhamento, Elementos Estruturais, Impermeabilização, Instalações de Gás, Telecomunicação, Revestimentos, Esquadrias, Prevenção e Combate a Incêndios (SPDA), Sistemas Elétricos, Hidrossanitários, Vedações Verticais
- **Classificação de conformidade:** Conforme / Não Conforme
- **Prioridade:** 0 a 5
- **Tipo de anomalia:** Endógena, Exógena, Natural, Funcional (e combinações)
- **Tipo de falha:** De Execução, De Planejamento, Gerencial, Operacional (e combinações)
- **Grau de risco:** Mínimo, Médio, Crítico
- **NBRs de referência:** NBR 5670, 5671, 5674, 5675, 5682, 9575, 13752, 15575, 16747

---

## Tarefa

Execute as seguintes etapas **em sequência**, documentando cada entrega:

### ETAPA 1 — Estudo do Contexto
Assuma o papel de **Estudo do Contexto** e produza `00_docs/estudo-do-contexto.md` com:

1. **Visão geral do domínio** — o que o engenheiro faz, para quem e qual o valor entregue
2. **Tipos de serviço e documentos** — descreva cada tipo de relatório/laudo e suas diferenças
3. **Atores** — engenheiro fiscal, cliente/contratante, empresa executora, responsável técnico, síndico, morador
4. **Entidades e glossário** — Edificação, Ativo/Sistema Predial, Ocorrência/Item Inspecionado, Relatório, Visita, Foto, Responsável Técnico, Contrato, Medição
5. **Regras de negócio (RN-XX)** — extraídas dos documentos (ex.: um relatório diário por dia de visita; foto obrigatória por ocorrência; classificação de risco determina prazo de intervenção; etc.)
6. **Requisitos funcionais (RF-XX)** — pelo menos:
   - RF-01: Cadastro de edificação/ativo com seus sistemas prediais
   - RF-02: Criação e edição de relatórios de fiscalização por obra
   - RF-03: Registro de ocorrências com sistema, classificação, anomalia, falha, grau de risco, prioridade e localização
   - RF-04: Upload e vinculação de imagens (Lightshot) a ocorrências
   - RF-05: Geração automática de relatório em PDF/Word a partir de template fiel ao modelo atual
   - RF-06: Dashboard de ativos com indicadores de saúde por sistema predial (mínimo/médio/crítico)
   - RF-07: Histórico de inspeções por edificação
   - RF-08: Controle de múltiplos clientes e obras simultâneas
7. **Requisitos não funcionais (RNF-XX)** — usabilidade mobile em campo, exportação PDF, autenticação, performance
8. **Fluxos principais** — Fiscalização de Obra, Inspeção Predial, Vistoria Cautelar, Relatório Fotográfico
9. **Lacunas [A ESCLARECER]**

---

### ETAPA 2 — Arquitetura de Software
Após concluir o estudo do contexto, assuma o papel de **Arquiteto de Software** e produza `00_docs/arquitetura.md` com:

1. **Stack tecnológica** justificada (considere: Next.js + FastAPI + PostgreSQL + S3/MinIO para imagens, ou alternativa adequada para uso em campo + geração de PDF)
2. **Diagrama de arquitetura** (Mermaid) — camadas: frontend web/mobile, API, banco de dados, armazenamento de arquivos, gerador de relatórios
3. **Modelo de dados** (diagrama ER em Mermaid) cobrindo as entidades:
   - `Edificacao` (cliente, endereço, tipologia, sistemas)
   - `Inspecao` / `Fiscalizacao` (tipo, data, engenheiro, contrato)
   - `Visita` (data, relatório diário por dia de obra)
   - `AtivoSistema` (sistema predial, subsistema, localização)
   - `Ocorrencia` (item inspecionado, situação, classificação, anomalia, falha, risco, prioridade)
   - `Foto` (url, legenda, ocorrência vinculada, fonte Lightshot)
   - `Responsavel` (engenheiro fiscal, RTE, contratante)
   - `Relatorio` (tipo, versão, PDF gerado, template usado)
4. **Contratos de API** — tabela de endpoints principais (CRUD de edificações, inspeções, ocorrências, upload de fotos, geração de relatório)
5. **Estratégia de geração de relatório** — como o sistema converte dados + fotos em PDF/DOCX fiel ao template do cliente
6. **Estratégia de integração com Lightshot** — como imagens capturadas com Lightshot são importadas (upload manual, clipboard, ou pasta monitorada)
7. **Estrutura de pastas** do repositório
8. **ADRs** — pelo menos: ADR-01 (escolha do gerador de PDF), ADR-02 (armazenamento de imagens), ADR-03 (mobile vs PWA)

---

## Saída Esperada

| Arquivo | Responsável | Localização |
|---|---|---|
| `estudo-do-contexto.md` | Estudo do Contexto | `00_docs/` |
| `arquitetura.md` | Arquiteto de Software | `00_docs/` |

---

## Restrições

- Baseie TODAS as decisões nos documentos de `00_docs/convertidos/` — não invente entidades ou regras.
- O sistema deve ser capaz de reproduzir fielmente o layout dos relatórios atuais do cliente.
- A captura de imagens via Lightshot é fluxo mandatório — não pode ser ignorada.
- Marque com `[A ESCLARECER]` qualquer informação que precise ser confirmada com o cliente antes de implementar.
- Não comece a implementação (código) — apenas documentação nesta etapa.
