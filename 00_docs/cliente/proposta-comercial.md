<!--
Documento destinado a conversão em PDF profissional.
Recomendação de conversão: Pandoc + wkhtmltopdf ou VS Code "Markdown PDF".
Paleta: navy #1e3a5f | accent #f97316 | surface #f8fafc
-->

<div align="center">

<!-- [LOGO: Garra Engenharia] -->

# ⬛ GARRA ENGENHARIA

### Proposta Comercial
## Sistema de Automação de Relatórios Prediais

---

**Preparada para:** Eng. Civil Esp. Roniel Ribeiro Costa
**CREA-GO nº** 1020613386/D-GO — Aparecida de Goiânia/GO

**Data:** 08 de julho de 2026
**Versão:** 1.0
**Validade da proposta:** 30 dias

</div>

<div style="page-break-after: always;"></div>

---

## 1. Sumário Executivo

### O cenário atual

Hoje, cada laudo técnico, relatório de fiscalização ou vistoria é produzido **manualmente**: as informações são anotadas em planilhas Excel no campo, transferidas para o Word, as fotos são inseridas uma a uma e o layout é ajustado antes de cada entrega. Um único Laudo de Inspeção Predial pode ter **150 a 200 páginas** e **mais de 150 fotografias** organizadas por sistema predial.

Esse processo é **lento, cansativo e sujeito a erros de digitação e de organização** — e torna difícil atender vários contratos ao mesmo tempo.

### A solução proposta

Um **sistema web moderno**, que o engenheiro acessa pelo celular durante a vistoria e pelo computador no escritório. As informações são registradas **uma única vez**, as fotos são organizadas **automaticamente** por sistema predial e, ao final, o relatório completo é gerado em **PDF e Word com um clique** — fiel ao modelo que o cliente já usa hoje.

### Benefícios mensuráveis

| Benefício | Situação atual | Com o sistema |
|---|---|---|
| Tempo para produzir um Laudo (LTIP) | 8 a 16 horas de edição manual | **Menos de 2 horas** |
| Erros de preenchimento | Frequentes (cópia manual planilha → Word) | **Eliminados** (dado inserido uma vez) |
| Organização de fotos | Manual, sujeita a perda | **Automática**, por sistema predial |
| Acesso ao histórico | Arquivos soltos no notebook | **Centralizado**, de qualquer dispositivo |
| Gestão de vários contratos | Difícil acima de 3 simultâneos | **Múltiplos contratos em paralelo** |

> **Em resumo:** menos tempo de escritório, mais tempo em campo, zero retrabalho e a mesma qualidade técnica dos documentos atuais.

<div style="page-break-after: always;"></div>

---

## 2. Descrição Detalhada do Sistema

### O que é

Uma plataforma digital sob medida para a rotina da Garra Engenharia. Funciona como um **site que também pode ser instalado no celular** (tecnologia PWA — sem precisar baixar app na loja) e acompanha o engenheiro do campo ao escritório.

### Como funciona — o fluxo principal

```
  1. CADASTRO            2. VISTORIA EM CAMPO         3. GERAÇÃO
  ┌───────────┐          ┌───────────────────┐        ┌──────────────┐
  │ Edificação│   ──►     │ Registra ocorrên- │  ──►   │ Relatório    │
  │ + Contrato│          │ cias + fotos pelo │        │ PDF / Word   │
  │           │          │ celular           │        │ em 1 clique  │
  └───────────┘          └───────────────────┘        └──────────────┘
```

1. **Cadastro** — O engenheiro registra a edificação (endereço, tipologia, sistemas prediais) e o contrato (partes envolvidas, ARTs, NBRs aplicáveis).
2. **Vistoria em campo** — Pelo celular, registra cada ocorrência com sistema predial, classificação técnica, criticidade e fotos (integrado ao Lightshot).
3. **Geração** — Com todos os dados lançados, o relatório completo é produzido automaticamente em PDF e Word, pronto para entrega.

### Onde funciona

- 📱 **Celular / tablet** — para registro em campo (interface otimizada para uso na obra)
- 💻 **Computador** — para gestão, revisão e emissão dos relatórios
- 🌐 **Instalável** — pode ser adicionado à tela inicial do celular como um aplicativo, sem loja de apps

<div style="page-break-after: always;"></div>

---

## 3. Regras e Conformidades Atendidas

O sistema foi concebido para respeitar integralmente as normas e boas práticas da inspeção predial brasileira:

| Conformidade | Como é atendida |
|---|---|
| **NBR 16747** | Estrutura de laudo, terminologia e organização de fotos por sistema predial |
| **IBAPE-NA** | Critérios de classificação de anomalias e falhas |
| **Grau de Risco (CMM)** | Classificação Crítico / Médio / Mínimo em cada ocorrência |
| **Matriz GUT** | Priorização por Gravidade, Urgência e Tendência |
| **VUP (NBR 15575)** | Registro de Vida Útil de Projeto dos sistemas |
| **ART / CREA** | Números de ART de Fiscalização e de Execução no cabeçalho dos relatórios |
| **Rastreabilidade fotográfica** | Cada ocorrência com foto vinculada, legenda técnica e organização por sistema |
| **Assinatura técnica** | Cabeçalho com dados do engenheiro responsável e registro no CREA |

> Todo relatório emitido preserva **validade pericial** e **fidelidade absoluta** ao layout dos documentos atuais.

<div style="page-break-after: always;"></div>

---

## 4. Módulos e Funcionalidades

| | Módulo | O que faz |
|:---:|---|---|
| 🏗️ | **RFO — Fiscalização de Obra** | Registra visitas diárias, mão de obra, medições e fotos do andamento da obra |
| 📋 | **LTIP — Inspeção Predial** | Laudo completo por sistema, com classificação CMM + GUT e relatório fotográfico |
| 🔍 | **Vistoria Cautelar** | Verificação de conformidade de obra para recebimento formal |
| 🏠 | **Vistoria Residencial** | Diagnóstico técnico de imóvel por cômodo e sistema |
| 📸 | **RFIP — Relatório Fotográfico** | Fotos organizadas automaticamente por sistema e subsistema |
| 📊 | **Dashboard de Saúde** | Painel visual do estado de cada sistema predial (Mínimo / Médio / Crítico) |
| 🕓 | **Histórico** | Linha do tempo de inspeções e versões de relatórios por edificação |

<div style="page-break-after: always;"></div>

---

## 5. Proposta de Solução de Negócio

Para atender diferentes momentos e necessidades, a solução é oferecida em **três planos**:

### 🟢 Plano Essencial — *Comece rápido*
Ideal para quem quer digitalizar a fiscalização de obra imediatamente.
- Módulo RFO (Relatório de Fiscalização de Obra)
- Cadastro de edificações e contratos
- Registro de visitas com fotos
- Geração automática de **PDF**
- Uso individual (1 engenheiro)

### 🔵 Plano Profissional — *Operação completa* ⭐ recomendado
Para quem quer toda a operação de inspeção predial automatizada.
- **Todos os tipos de laudo** (RFO, LTIP, Cautelar, Residencial, RFIP)
- Geração em **PDF e Word (DOCX editável)**
- **Dashboard de saúde** por edificação e sistema
- Histórico e versionamento de relatórios
- Classificação CMM + matriz GUT

### 🟠 Plano Enterprise — *Escala e tranquilidade*
Para operar em nuvem com suporte contínuo e equipe.
- Tudo do Plano Profissional
- **Hospedagem em nuvem** (acesso de qualquer lugar)
- **Treinamento** da equipe
- **Suporte prioritário por 12 meses**
- Múltiplos usuários (auxiliares e estagiários)

<div style="page-break-after: always;"></div>

---

## 6. Capturas de Tela do Protótipo

> As telas abaixo foram desenhadas no protótipo navegável entregue junto a esta proposta.
> **Instrução:** após abrir o protótipo (`02_prototipos/index.html`), capture cada tela e substitua os marcadores abaixo pelas imagens correspondentes.

**Dashboard Principal**
`[SCREENSHOT: 01-dashboard]`

**Lista de Edificações**
`[SCREENSHOT: 02-edificacoes]`

**Nova Vistoria (registro em campo)**
`[SCREENSHOT: 03-nova-vistoria]`

**Registro de Ocorrência**
`[SCREENSHOT: 04-ocorrencia]`

**Relatórios Gerados**
`[SCREENSHOT: 05-relatorios]`

**Preview do Laudo (fidelidade ao modelo)**
`[SCREENSHOT: 06-laudo-preview]`

<div style="page-break-after: always;"></div>

---

## 7. Proposta de Preço

Valores em Reais (BRL), referentes ao desenvolvimento sob medida do sistema mais a licença de uso mensal.

| | 🟢 Essencial | 🔵 Profissional ⭐ | 🟠 Enterprise |
|---|:---:|:---:|:---:|
| **Implementação (uma vez)** | R$ 12.900 | R$ 28.900 | R$ 46.900 |
| **Licença mensal** | R$ 149/mês | R$ 349/mês | R$ 690/mês |
| Módulo RFO | ✅ | ✅ | ✅ |
| Laudos LTIP / Cautelar / Residencial | — | ✅ | ✅ |
| Relatório Fotográfico (RFIP) | — | ✅ | ✅ |
| Geração de PDF | ✅ | ✅ | ✅ |
| Geração de Word (DOCX) | — | ✅ | ✅ |
| Dashboard de saúde | — | ✅ | ✅ |
| Histórico e versionamento | Básico | ✅ | ✅ |
| Hospedagem em nuvem | — | Opcional | ✅ |
| Treinamento | — | 1 sessão | Completo |
| Suporte | E-mail | Prioritário | Prioritário 12 meses |
| Usuários | 1 | 1 | Múltiplos |

### Condições de pagamento

- **Entrada:** 40% da implementação na assinatura do contrato
- **Saldo:** 60% divididos em até **3 parcelas** ao longo do desenvolvimento, atreladas às entregas de cada fase
- **Licença mensal:** começa a ser cobrada a partir da entrega do sistema em produção
- Formas aceitas: PIX, boleto ou transferência

> Os valores acima são **estimativas de referência de mercado** para sistemas sob medida de engenharia no Brasil e podem ser ajustados conforme o escopo final validado no kickoff.

<div style="page-break-after: always;"></div>

---

## 8. Próximos Passos

1. ✅ **Aprovação da proposta** — confirmação do plano escolhido pelo Eng. Roniel
2. 📝 **Assinatura do contrato** — formalização de escopo, prazos e condições
3. 🚀 **Reunião de kickoff** — validação dos templates, resolução das lacunas em aberto e início da Fase 3

**Cronograma estimado de entrega:** aproximadamente **10 a 13 semanas** após o kickoff, distribuídas em 5 fases (backend, frontend, integração, testes e treinamento).

---

<div align="center">

### Vamos automatizar a produção dos seus laudos?

**Entre em contato para agendar o kickoff.**

</div>

---

<div align="center" style="color:#64748b; font-size: 0.9em;">

**GARRA ENGENHARIA**
Aparecida de Goiânia / GO
CNPJ: [placeholder — 00.000.000/0001-00]
Contato: [placeholder — e-mail / telefone / WhatsApp]
Responsável Técnico: Eng. Civil Esp. Roniel Ribeiro Costa — CREA-GO 1020613386/D-GO

*Proposta Comercial v1.0 — 08/07/2026 — documento confidencial*

</div>
