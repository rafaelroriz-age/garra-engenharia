---
description: "Prompt mestre completo para projetar o sistema de automação de relatórios prediais da Garra Engenharia: estudo do contexto, arquitetura, prototipagem para o cliente, especificação de backend, especificação de frontend e plano de implementação faseado. Ativa todos os agentes de engenharia e arquitetura em sequência."
---
## Contexto do Projeto

**Cliente:** Eng. Civil Esp. Roniel Ribeiro Costa (CREA-GO nº 1020613386/D-GO) — profissional autônomo de inspeção predial e fiscalização de obras.

**Problema:** O engenheiro produz manualmente relatórios complexos no Excel/Word (templates com layout sofisticado, tabelas, fotos anotadas com Lightshot), o que consome horas de trabalho repetitivo por relatório. Precisa de um sistema que automatize a geração, dinamize a edição e entregue dashboards de saúde predial para os clientes.

**Serviços prestados e documentos de referência em `00_docs/convertidos/`:**

| Serviço | Documento de referência |
|---|---|
| Relatório de Fiscalização de Obra | `Relatorio_de_Fiscalizacao_1.md`, `Relatorio_de_Fiscalizacao.md` |
| Laudo de Inspeção Predial (NBR 16747) | `Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md` |
| Vistoria Cautelar de Recebimento | `Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md` |
| Vistoria de Imóvel Residencial | `Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md` |
| Relatório Fotográfico de Inspeção | `Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md` |
| Gabarito de Inspeção (sistemas, classificações, riscos) | `RFO_INSPECAO.md` |

**Ferramenta mandatória de imagem:** [Lightshot](https://app.prntscr.com/pt-br/index.html) — o engenheiro captura e anota prints durante vistorias. O sistema deve integrar este fluxo.

**Vocabulário técnico central:**
- **Sistemas prediais:** Aberturas, Acessibilidade, Circulações, Cobertura/Telhamento, Elementos Estruturais, Impermeabilização, Gás, Telecomunicação, Revestimentos, Esquadrias, Incêndio/SPDA, Elétrica, Hidrossanitário, Vedações Verticais
- **Classificação:** Conforme / Não Conforme | Prioridade 0–5 | Grau de risco: Mínimo / Médio / Crítico
- **Anomalia:** Endógena, Exógena, Natural, Funcional | **Falha:** Execução, Planejamento, Gerencial, Operacional
- **NBRs:** 5670, 5671, 5674, 5675, 5682, 9575, 13752, 15575, 16747

---

## Etapas de Execução

Execute **todas as etapas em sequência**. Não avance para a próxima sem concluir e registrar a anterior.

---

### ETAPA 1 — Estudo do Contexto
**Agente:** Estudo do Contexto | **Saída:** `00_docs/estudo-do-contexto.md`

Leia todos os documentos em `00_docs/convertidos/` e produza:

1. **Visão geral do domínio** e proposta de valor do sistema
2. **Tipos de serviço** — diferenças estruturais entre Fiscalização, Inspeção Predial, Vistoria Cautelar, Vistoria Residencial e Relatório Fotográfico
3. **Atores:** engenheiro fiscal, cliente/contratante, empresa executora, responsável técnico de execução, síndico, morador
4. **Entidades e glossário:** Edificação, AtivoSistema, Inspecao/Fiscalizacao, Visita, Ocorrencia, Foto, Responsavel, Contrato, Medicao, Relatorio, Template
5. **Regras de negócio (RN-01...N):** extraídas dos documentos — ex.: um registro diário por dia de visita; foto obrigatória por ocorrência crítica; classificação de risco define prazo máximo de intervenção; relatório deve conter ART; etc.
6. **Requisitos funcionais (RF-01...N)** — mínimo obrigatório:
   - RF-01 Cadastro de edificação com sistemas prediais e ativos
   - RF-02 Criação e edição de relatórios de fiscalização por obra (diário de obra)
   - RF-03 Criação e edição de laudos de inspeção predial
   - RF-04 Registro de ocorrências com sistema, subsistema, localização, situação, anomalia, falha, risco, prioridade
   - RF-05 Upload e vinculação de imagens Lightshot a ocorrências, com legenda técnica
   - RF-06 Geração automática de PDF/DOCX fiel ao template atual do cliente
   - RF-07 Dashboard de saúde predial por edificação (scorecard por sistema, mapa de calor de riscos)
   - RF-08 Histórico cronológico de inspeções e evolução por edificação
   - RF-09 Gestão de múltiplos clientes, obras e contratos simultâneos
   - RF-10 Assinatura digital / QR Code de autenticidade no relatório gerado
7. **Requisitos não funcionais (RNF-01...N):** usabilidade em campo (mobile/tablet), geração de PDF < 30s, exportação Word editável, autenticação segura, backup automático de fotos
8. **Fluxos de trabalho principais** (passo a passo de cada tipo de serviço)
9. **Lacunas [A ESCLARECER]**

---

### ETAPA 2 — Arquitetura de Software
**Agente:** Arquiteto de Software | **Saída:** `00_docs/arquitetura.md`

Com base no estudo do contexto, defina:

1. **Stack tecnológica** justificada para o cenário (uso em campo + geração de documentos + dashboard):
   - Sugestão base para análise: **Next.js 14 (PWA)** + **FastAPI** + **PostgreSQL** + **MinIO/S3** (fotos) + **WeasyPrint ou Puppeteer** (PDF) + **python-docx** (DOCX)
   - Justifique cada escolha contra os RNFs

2. **Diagrama de arquitetura** (Mermaid) — camadas: PWA/Mobile → API Gateway → Serviços (Auth, Relatório, Inspeção, Gerador de Doc) → Banco → Storage

3. **Modelo de dados completo** (diagrama ER Mermaid):
   ```
   Edificacao → Inspecao/Fiscalizacao → Visita → Ocorrencia → Foto
   Edificacao → AtivoSistema → Ocorrencia
   Ocorrencia → Classificacao (anomalia, falha, risco, prioridade)
   Relatorio → Template → Relatorio gerado (PDF/DOCX)
   Usuario/Responsavel → Inspecao
   Cliente → Edificacao → Contrato
   ```

4. **Contratos de API REST** (tabela completa: método, rota, payload, response, status codes):
   - CRUD: edificações, inspeções, visitas, ocorrências, fotos, relatórios
   - Ações: `POST /relatorios/{id}/gerar-pdf`, `POST /fotos/upload`, `GET /edificacoes/{id}/dashboard`

5. **Estratégia de geração de documento:**
   - Como os dados do banco + fotos são renderizados no template fiel ao layout atual do cliente
   - Definir formato de template (Jinja2 + HTML→PDF ou DOCX template)

6. **Estratégia de integração com Lightshot:**
   - Fluxo A: upload manual (arrastar foto → API)
   - Fluxo B: pasta monitorada local que sincroniza automaticamente
   - Fluxo C: extensão/clipboard import

7. **Estrutura de pastas** do repositório (`04_backend/`, `03_frontend/`, `templates/`, `migrations/`, `tests/`)

8. **ADRs obrigatórios:**
   - ADR-01: escolha do motor de geração de PDF
   - ADR-02: armazenamento de imagens (local vs cloud)
   - ADR-03: PWA vs App nativo para uso em campo
   - ADR-04: estratégia de templates de relatório (HTML/CSS vs DOCX template)

---

### ETAPA 3 — Prototipagem e Documentação para o Cliente
**Agente:** Prototipagem e Documentação para Cliente | **Saída:** `00_docs/prototipos.md` + `00_docs/cliente/proposta.md`

Crie wireframes e documentação orientada ao cliente para validação **antes** da implementação:

1. **Proposta da solução** (`00_docs/cliente/proposta.md`) — em linguagem simples:
   - O que o sistema faz e como resolve o problema atual
   - Comparativo: antes (manual) vs depois (sistema)
   - Benefícios quantificáveis (tempo por relatório, histórico digitalizado, dashboard)

2. **Wireframes das telas principais** (`00_docs/prototipos.md`) em Mermaid ou descrição estruturada:

   | # | Tela | Descrição |
   |---|---|---|
   | 1 | Dashboard Principal | Visão geral: obras ativas, inspeções recentes, alertas de risco crítico |
   | 2 | Lista de Edificações/Obras | Cards com nome, cliente, última inspeção, status de risco |
   | 3 | Ficha da Edificação | Dados, sistemas prediais, histórico de inspeções, dashboard de saúde |
   | 4 | Nova Inspeção / Fiscalização | Formulário de criação com tipo, data, contrato, responsáveis |
   | 5 | Diário de Obra (Fiscalização) | Registro diário: data, atividades, mão de obra, medições, fotos |
   | 6 | Formulário de Ocorrência | Sistema, subsistema, localização, classificação, fotos vinculadas |
   | 7 | Galeria de Fotos da Inspeção | Grid de fotos com legenda, anotações Lightshot e vínculo à ocorrência |
   | 8 | Gerador de Relatório | Seleção de template, preview, ajustes finais, botão Gerar PDF/DOCX |
   | 9 | Dashboard de Saúde Predial | Scorecard por sistema, mapa de calor de riscos, gráfico de evolução |
   | 10 | Gestão de Clientes/Contratos | CRM simples: cliente, contato, contratos, edificações vinculadas |

3. **Lista de itens para aprovação do cliente** antes de iniciar o desenvolvimento

---

### ETAPA 4 — Especificação do Backend
**Agente:** Engenheiro Backend | **Saída:** `00_docs/especificacao-backend.md`

Sem escrever código de produção ainda, especifique em detalhe:

1. **Estrutura de módulos/serviços** do backend (pastas, responsabilidades de cada módulo)
2. **Schemas de banco de dados** — DDL comentado para cada tabela, com tipos de dados, constraints, índices e FKs
3. **Regras de negócio por serviço** — para cada endpoint da API, descreva as validações, cálculos e efeitos colaterais
4. **Fluxo de geração de relatório** — passo a passo técnico: query dos dados → montagem do contexto → renderização do template → output PDF/DOCX → armazenamento → URL de download
5. **Autenticação e autorização** — estratégia (JWT, roles: admin, engenheiro, cliente somente-leitura)
6. **Estratégia de testes** — unitários por serviço, integração por endpoint, fixtures de dados de inspeção real

---

### ETAPA 5 — Especificação do Frontend
**Agente:** Engenheiro Frontend | **Saída:** `00_docs/especificacao-frontend.md`

Sem escrever código de produção ainda, especifique:

1. **Árvore de componentes** — hierarquia de componentes para cada tela do wireframe
2. **Rotas e navegação** — estrutura de rotas do Next.js (App Router), fluxo de navegação
3. **Gerenciamento de estado** — o que fica em estado global (sessão, edificação ativa) vs local (formulário)
4. **Formulários críticos** — campos, validações e UX do formulário de Ocorrência e do Diário de Obra
5. **Fluxo de upload de foto Lightshot** — UX detalhada: drag-and-drop, clipboard paste, seleção de arquivo; preview + legenda + vínculo
6. **Dashboard de saúde predial** — quais bibliotecas de gráfico, quais métricas exibir e como calcular o score por sistema
7. **Comportamento offline/PWA** — quais dados cachear para uso em campo sem internet (formulário de ocorrência, fotos pendentes)
8. **Estratégia de testes** — componentes críticos a testar, ferramentas (Playwright, Testing Library)

---

### ETAPA 6 — Plano de Implementação Faseado
**Agente:** Gestor de Projeto / Arquiteto de Soluções | **Saída:** `00_docs/projeto/plano-implementacao.md`

Produza um plano de implementação em **3 fases**:

#### Fase 1 — MVP (Relatório Funcional)
> Meta: engenheiro consegue registrar uma inspeção e gerar um PDF fiel ao template atual

- Cadastro de edificação e cliente
- Criação de inspeção/fiscalização
- Registro de ocorrências com fotos
- Upload de imagens Lightshot
- Geração de PDF com template base
- Autenticação básica

#### Fase 2 — Produtividade
> Meta: sistema substitui completamente o Excel/Word no dia a dia

- Todos os tipos de relatório (fiscalização, inspeção predial, vistoria cautelar, vistoria residencial, fotográfico)
- Templates fiéis a cada modelo atual do cliente
- Exportação DOCX editável
- Histórico de inspeções por edificação
- Gestão de múltiplos clientes e contratos

#### Fase 3 — Inteligência e Entrega ao Cliente Final
> Meta: entrega de dashboards interativos para os clientes do engenheiro

- Dashboard de saúde predial por edificação
- Portal do cliente (acesso somente-leitura ao histórico e relatórios)
- Mapa de calor de riscos por sistema predial
- Alertas e notificações de prazo de intervenção
- Assinatura digital / QR Code de autenticidade
- PWA com funcionamento offline

Para cada fase, liste: entregáveis, dependências, ordem de implementação e critérios de aceite.

---

## Saída Esperada — Resumo de Artefatos

| Etapa | Arquivo | Conteúdo |
|---|---|---|
| 1 | `00_docs/estudo-do-contexto.md` | Domínio, entidades, RN, RF, RNF, fluxos |
| 2 | `00_docs/arquitetura.md` | Stack, ER, API, estratégias técnicas, ADRs |
| 3 | `00_docs/prototipos.md` | Wireframes das 10 telas principais |
| 3 | `00_docs/cliente/proposta.md` | Proposta executiva para o cliente |
| 4 | `00_docs/especificacao-backend.md` | Schemas, regras por endpoint, auth, testes |
| 5 | `00_docs/especificacao-frontend.md` | Componentes, rotas, estado, PWA, testes |
| 6 | `00_docs/projeto/plano-implementacao.md` | 3 fases com entregáveis e critérios de aceite |

---

## Restrições Globais

- Baseie **todas** as decisões nos documentos de `00_docs/convertidos/` — não invente regras ou entidades.
- O sistema **deve reproduzir fielmente** o layout visual dos relatórios atuais do cliente.
- A integração com **Lightshot é mandatória** em todas as decisões de upload de imagem.
- Marque `[A ESCLARECER]` em tudo que precisar de confirmação do cliente antes de implementar.
- **Não escreva código de produção** neste fluxo — apenas documentação e especificação.
- Ao concluir cada etapa, registre o artefato produzido em `00_docs/projeto/status.md` antes de avançar.
