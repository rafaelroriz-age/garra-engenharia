---
description: "Ativa o agente Prototipagem e Documentação para Cliente para criar proposta comercial em PDF, protótipo visual de alta fidelidade e apresentação em PPTX."
---

## Contexto

O projeto é o **Sistema de Automação de Relatórios Prediais** da **Garra Engenharia**, desenvolvido para o **Eng. Civil Esp. Roniel Ribeiro Costa** (CREA-GO nº 1020613386/D-GO), Aparecida de Goiânia/GO.

Artefatos disponíveis para consulta:
- `00_docs/estudo-do-contexto.md` — domínio completo, tipos de serviço, entidades, regras de negócio
- `00_docs/arquitetura.md` — stack tecnológica, modelo de dados, fluxos de API
- `00_docs/projeto/resumo-executivo.md` — visão do problema e solução em linguagem de cliente
- `00_docs/projeto/escopo.md` — o que está dentro e fora do escopo, funcionalidades core
- `00_docs/projeto/riscos.md` — riscos e mitigações
- `00_docs/projeto/decisoes.md` — decisões de arquitetura já tomadas
- `00_docs/convertidos/` — documentos reais do cliente convertidos (laudos, RFO, COND)

**Identidade visual de referência:** profissional de engenharia civil, sóbria, técnica mas moderna. Paleta sugerida: tons de azul escuro navy, laranja/âmbar como cor de destaque, branco e cinza claro como fundo. Tipografia sans-serif limpa (ex.: Inter, Manrope).

---

## Tarefa

Assuma o papel de **Agente de Prototipagem e Documentação para Cliente** e entregue **três artefatos distintos**, todos profissionais e visualmente impecáveis:

---

### Entregável 1 — Proposta Comercial em PDF (`00_docs/cliente/proposta-comercial.md`)

Gere um documento Markdown estruturado para ser convertido em PDF profissional. O documento deve conter:

1. **Capa** — logotipo placeholder da Garra Engenharia, título "Proposta Comercial — Sistema de Automação de Relatórios Prediais", data (2026-07-08), versão 1.0.
2. **Sumário Executivo** — problema atual (processo manual), solução proposta, benefícios mensuráveis (use a tabela do resumo-executivo).
3. **Descrição Detalhada do Sistema** — o que é, como funciona, fluxo principal (cadastro → vistoria → geração de relatório), compatibilidade com dispositivos (PWA).
4. **Regras e Conformidades Atendidas** — NBR 16747, IBAPE-NA, VUP, CMM, GUT, ART, CREA; rastreabilidade fotográfica; assinatura técnica.
5. **Módulos e Funcionalidades** — lista visual de módulos com ícone placeholder e descrição curta (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP, Dashboard, Histórico).
6. **Proposta de Solução de Negócio** — três cenários/planos:
   - **Plano Essencial** (RFO + geração PDF) — para quem quer começar rápido
   - **Plano Profissional** (todos os laudos + DOCX + dashboard) — para operação completa
   - **Plano Enterprise** (Profissional + deploy em nuvem + treinamento + suporte 12 meses) — para escala
7. **Capturas de Tela do Protótipo** — seção reservada com placeholders `[SCREENSHOT: nome-da-tela]` para as telas geradas no Entregável 2 (instruções para inserir após geração do mock).
8. **Proposta de Preço** — tabela com os três planos, valores sugeridos (preencha com valores de referência de mercado para sistemas SaaS para engenharia, em BRL), condições de pagamento (entrada + parcelas) e o que está incluso em cada plano.
9. **Próximos Passos** — call to action claro: aprovação, assinatura de contrato, kick-off.
10. **Rodapé** — dados do fornecedor (placeholder), CNPJ, contato.

**Formato visual do PDF:** use formatação Markdown rica — tabelas, separadores `---`, emojis técnicos discretos se necessário, seções bem demarcadas com títulos de nível correto.

---

### Entregável 2 — Protótipo Mock de Alta Fidelidade (`02_prototipos/`)

Crie um protótipo HTML/CSS/JS navegável, com o **design mais moderno e bonito possível**, usando as melhores práticas atuais de UI/UX. Requisitos visuais e técnicos:

**Stack de UI obrigatória:**
- HTML5 semântico
- Tailwind CSS via CDN (última versão disponível via Play CDN ou link oficial)
- Fonte Google Fonts: **Inter** (body) + **Manrope** (headings)
- Ícones: **Heroicons** (inline SVG) ou **Lucide** via CDN
- Animações sutis: transições CSS (hover, focus, active), micro-interações
- Layout responsivo: funciona em desktop 1440px e mobile 390px

**Paleta de cores:**
- Primary: `#1e3a5f` (navy profundo)
- Accent: `#f97316` (laranja técnico)
- Surface: `#f8fafc` (cinza fundo)
- Text: `#0f172a` / `#64748b`
- Success: `#22c55e`, Warning: `#eab308`, Danger: `#ef4444`

**Telas a criar (arquivos separados):**

| Arquivo | Tela | Descrição |
|---|---|---|
| `02_prototipos/index.html` | Hub de navegação | Landing page interna com cards para cada tela |
| `02_prototipos/01-dashboard.html` | Dashboard Principal | KPIs (total de edificações, contratos ativos, laudos em andamento, relatórios gerados este mês), gráfico de pizza de status por sistema predial, lista das últimas vistorias com badge de criticidade |
| `02_prototipos/02-edificacoes.html` | Lista de Edificações | Tabela/card grid de edificações com foto placeholder, endereço, última inspeção, badge de saúde (Ótimo/Regular/Crítico), botão de ação |
| `02_prototipos/03-nova-vistoria.html` | Formulário de Nova Vistoria | Stepper de 4 etapas: (1) Dados Gerais, (2) Seleção de Sistemas Prediais, (3) Lançamento de Ocorrências + Upload de Fotos, (4) Resumo e Geração |
| `02_prototipos/04-ocorrencia.html` | Card de Ocorrência | Modal/card para registrar ocorrência: sistema predial, descrição, classificação CMM, matriz GUT (sliders interativos), upload de foto com preview |
| `02_prototipos/05-relatorios.html` | Relatórios Gerados | Lista de relatórios com tipo (RFO/LTIP/RFIP), edificação, data, status (Rascunho/Final), botões Baixar PDF e Baixar DOCX |
| `02_prototipos/06-laudo-preview.html` | Preview do Laudo | Visualização paginada simulada de um LTIP, com capa, sumário, seção de ocorrências e relatório fotográfico — mostrando fidelidade ao template real |

**Padrões de UX obrigatórios:**
- Sidebar fixa de navegação (desktop) / bottom navigation (mobile) com os módulos do sistema
- Topbar com avatar, nome do usuário e breadcrumb
- Skeleton loaders (CSS) nos cards e tabelas
- Empty states ilustrados (SVG inline simples) quando lista estiver vazia
- Badges coloridos para criticidade de ocorrências (Mínimo=verde, Médio=amarelo, Crítico=vermelho)
- Botões com ícone + texto, estados hover/active/disabled visíveis

---

### Entregável 3 — Apresentação Comercial em PPTX (`00_docs/cliente/apresentacao-comercial.md`)

Gere um roteiro completo e detalhado para uma apresentação de **12 a 15 slides** em PowerPoint, salvo como Markdown estruturado em `00_docs/cliente/apresentacao-comercial.md`. O documento deve descrever **cada slide com precisão** para que possa ser montado em qualquer ferramenta (PowerPoint, Google Slides, Canva).

**Para cada slide especifique:**
- Número e título do slide
- Layout sugerido (ex.: "título + imagem à direita", "3 colunas", "full-bleed foto")
- Conteúdo textual exato (título, subtítulo, bullets, notas do apresentador)
- Elemento visual (gráfico, ícone, screenshot, ilustração — descreva com precisão)
- Animação de entrada sugerida (Fade In, Fly from left, etc.)

**Roteiro de slides sugerido:**

1. **Capa** — logo Garra Engenharia, título da proposta, apresentador, data
2. **Agenda** — 5 tópicos da apresentação em cards horizontais
3. **O Problema** — 3 dores principais com ícone para cada, dado numérico de impacto
4. **Situação Atual** — diagrama do fluxo atual (manual/planilha) vs. fluxo futuro (sistema)
5. **A Solução** — headline forte + screenshot do dashboard (Tela 01)
6. **Como Funciona** — stepper visual de 4 etapas do fluxo principal
7. **Módulos do Sistema** — grid de 6 cards com ícone + nome do módulo
8. **Fidelidade ao Template** — split screen: template atual à esquerda / preview do laudo gerado à direita (Tela 06)
9. **Mobile-First** — mockup de smartphone mostrando o formulário de vistoria (Tela 03)
10. **Benefícios Mensuráveis** — antes/depois em tabela visual impactante
11. **Planos e Investimento** — 3 planos em cards comparativos (destacar o Profissional como recomendado)
12. **Cronograma** — timeline horizontal com 5 fases e duração estimada
13. **Por Que Escolher** — 4 diferenciais em ícone + texto
14. **Próximos Passos** — 3 ações com ícone de checkbox animado
15. **Encerramento** — logo, contato, call to action final

**Padrão visual dos slides:**
- Fundo: `#1e3a5f` (slides de destaque) ou `#f8fafc` (slides de conteúdo)
- Título em Manrope Bold, corpo em Inter Regular
- Accent em `#f97316` para highlights, números e CTAs
- Máximo de 6 bullets por slide — preferir visual a texto

---

## Saída Esperada

| Artefato | Caminho | Formato |
|---|---|---|
| Proposta Comercial | `00_docs/cliente/proposta-comercial.md` | Markdown para PDF |
| Navegador Hub | `02_prototipos/index.html` | HTML/CSS/JS |
| Dashboard | `02_prototipos/01-dashboard.html` | HTML/CSS/JS |
| Lista Edificações | `02_prototipos/02-edificacoes.html` | HTML/CSS/JS |
| Nova Vistoria | `02_prototipos/03-nova-vistoria.html` | HTML/CSS/JS |
| Card Ocorrência | `02_prototipos/04-ocorrencia.html` | HTML/CSS/JS |
| Relatórios | `02_prototipos/05-relatorios.html` | HTML/CSS/JS |
| Preview Laudo | `02_prototipos/06-laudo-preview.html` | HTML/CSS/JS |
| Roteiro PPTX | `00_docs/cliente/apresentacao-comercial.md` | Markdown estruturado |

---

## Restrições

- NÃO use frameworks JavaScript (React, Vue, Angular) — apenas HTML/CSS/JS vanilla + Tailwind via CDN.
- NÃO use imagens externas que possam quebrar offline — use gradientes CSS, SVG inline e placeholders com `bg-gray-200`.
- NÃO escreva código de backend ou lógica de negócio real — o protótipo é mock estático.
- NÃO use jargão técnico de programação na proposta PDF ou na apresentação — o público é o cliente engenheiro civil.
- NÃO omita nenhuma das 7 telas do protótipo — todas são necessárias para a proposta.
- MANTENHA consistência visual entre os 3 entregáveis (mesma paleta, fontes e terminologia).
- Os valores de preço na proposta devem ser **estimativas de mercado razoáveis** para sistemas SaaS de engenharia no Brasil — não invente valores impossíveis.
- O protótipo deve ser **navegável** — todos os links entre páginas devem funcionar com caminhos relativos.
