---
title: Estudo do Contexto — Sistema de Automação de Relatórios Prediais
type: knowledge
status: validated
owner: Garra Engenharia
related:
  - 00_docs/arquitetura.md
  - 00_docs/convertidos/RFO_INSPECAO.md
  - 00_docs/convertidos/Relatorio_de_Fiscalizacao_1.md
  - 00_docs/convertidos/Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md
tags: [contexto, domínio, requisitos, regras-de-negócio, rbac, portal-cliente, ia-legendas]
last_updated: 2026-07-27
---

<!-- ai-summary
System: sistema para automação da produção de relatórios técnicos de engenharia predial (fiscalização de obras, inspeção predial, vistoria cautelar, vistoria residencial, relatório fotográfico).
Flow: cadastro de edificação/contrato -> registro de visita/inspeção -> lançamento de ocorrências + fotos -> geração automática de relatório PDF/DOCX fiel ao modelo do cliente.
Owner: Eng. Civil Esp. Roniel Ribeiro Costa (CREA-GO 1020613386/D-GO) — Garra Engenharia, Aparecida de Goiânia/GO.
Systems: XLSM (template atual), Lightshot (captura de imagens), Power BI (análise de gravidade).
Status: validated.
-->

# Estudo do Contexto — Sistema de Automação de Relatórios Prediais

## 1. Visão Geral do Domínio

O **Eng. Civil Esp. Roniel Ribeiro Costa** (CREA-GO nº 1020613386/D-GO), atuando pela **Garra Engenharia** (Aparecida de Goiânia/GO), presta serviços técnicos de inspeção, fiscalização e vistoria de edificações para clientes privados (condomínios residenciais, pessoas físicas e jurídicas).

O valor entregue é duplo: (a) **conformidade técnica e legal** — os documentos emitidos têm validade pericial, são assinados com ART e seguem NBRs vigentes; (b) **rastreabilidade fotográfica e histórica** — cada ocorrência é documentada com imagens, localização e classificação técnica, criando um histórico auditável da edificação.

O principal gargalo operacional atual é a **produção manual dos documentos**: o engenheiro preenche planilhas XLSM complexas no campo e monta relatórios PDF/DOCX a partir de templates, processo lento e propenso a inconsistências. O sistema a construir elimina esse gargalo mantendo fidelidade absoluta ao layout e terminologia dos documentos existentes.

---

## 2. Tipos de Serviço e Documentos

### 2.1 Relatório de Fiscalização de Obra (RFO)

Acompanhamento contínuo de obras em execução. Tem periodicidade variável (há vários relatórios por contrato, um por visita). Registra:

- Dados da obra: contratante, empresa executora, RTE, objeto do contrato, ART de Fiscalização e ART de Execução, NBRs aplicáveis, prazo, área.
- Por visita: data, mão de obra presente (função + quantidade), serviços executados no dia, medições parciais, observações e fotos.
- Estrutura baseada em planilha XLSM com abas: `Informações Gerais` (cabeçalho da obra) + uma aba por visita com data, equipe, serviços e medições.

**Documento de referência:** `Relatorio_de_Fiscalizacao_1.md` (xlsm), `Relatorio_de_Fiscalizacao.md` (PDF modelo, 98 págs.)

### 2.2 Laudo Técnico de Inspeção Predial (LTIP)

Inspeção sistematizada da edificação conforme NBR 16747 e IBAPE-NA. É o documento mais complexo — pode ter 150 a 200+ páginas. Estrutura:

- Introdução, Histórico, Considerações Preliminares (pressupostos, ressalvas, fatores limitantes).
- Objetivo geral e específico.
- Objeto: tipologia, caracterização, localização, descrição qualitativa (região, valorização, sistema construtivo, pavimentos, áreas), documentação técnica analisada.
- Metodologia: nível da inspeção, critério (NBR 16747 + IBAPE-NA), classificação de anomalias/falhas, grau de risco CMM e GUT, avaliação de manutenção e uso, VUP.
- Desenvolvimento: laudo por sistema predial inspecionado.
- Relatório fotográfico: organizado por sistema, com legenda técnica por foto.

**Documento de referência:** `Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md` (199 págs.)

### 2.3 Laudo Técnico de Vistoria Cautelar de Recebimento

Avaliação do estado de uma obra imediatamente antes ou após sua conclusão, para fins de recebimento formal. Estrutura similar ao LTIP, mas focada na verificação de conformidade com o projeto e contrato de reforma. Registra o estado encontrado, divergências e pendências.

**Documento de referência:** `Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md` (148 págs.)

### 2.4 Vistoria de Imóvel Residencial

Diagnóstico técnico de unidade habitacional (apartamento, casa). Registra patologias por cômodo/sistema, medições e emite parecer técnico sobre estado geral e recomendações.

**Documento de referência:** `Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md`

### 2.5 Relatório Fotográfico de Inspeção Predial (RFIP)

Documento subsidiário ao LTIP ou entregue de forma independente. Composto exclusivamente de fotografias organizadas por sistema predial, com legendas técnicas. Não contém texto analítico extenso.

**Documento de referência:** `Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md`

---

## 3. Atores

| Ator | Papel | Observações |
|---|---|---|
| **Engenheiro Fiscal** | Profissional responsável pela fiscalização. É o autor dos relatórios. | Roniel Ribeiro Costa; possui CREA e emite ART de Fiscalização. |
| **Responsável Técnico pela Execução (RTE)** | Engenheiro da empresa executora que assina a ART de Execução. | Diferente do fiscal; pode ser de outra empresa. |
| **Responsável Legal da Empresa Executora** | Representante jurídico da construtora/reformadora. | Pode haver duas empresas executoras no mesmo contrato. |
| **Contratante / Cliente** | Pessoa física ou jurídica que contratou o serviço. Pode ser o dono do imóvel, síndico ou administradora. Acompanha a auditoria/fiscalização feita pelo Engenheiro Fiscal através de um Portal do Cliente próprio (dashboard + documentos) — ver RF-13. | Tem CPF ou CNPJ; assina o contrato. Perfil de acesso distinto do Engenheiro Fiscal (RBAC, ver RN-14). |
| **Síndico / Administradora** | Representante do condomínio em inspeções prediais. | Deve estar presente ou autorizar o acesso às áreas. |
| **Morador / Proprietário de Unidade** | Permite acesso à unidade durante vistoria residencial. | [A ESCLARECER] se há assinatura de termo de autorização. |
| **Responsável Legal do Contratante** | Quando o contratante é PJ, o representante legal assina. | Ex.: Carlos Leite de Camargo Filho (Res. Bucareste). |

---

## 4. Entidades e Glossário

### 4.1 Entidades principais

| Entidade | Descrição |
|---|---|
| **Edificação** | Imóvel inspecionado: condomínio, apartamento, casa ou obra. Possui endereço, tipologia, caracterização física (pavimentos, áreas, sistema construtivo) e acervo técnico (projetos, ARTs). |
| **Contrato** | Vínculo entre o engenheiro fiscal e o cliente para prestação de um serviço. Possui número, tipo de serviço, objeto, início, prazo e dados de todas as partes envolvidas. |
| **Inspeção / Fiscalização** | Evento de campo vinculado a um Contrato. Para RFO: série de visitas. Para LTIP/Vistoria: pode ser uma ou mais visitas. Gera um Relatório final. |
| **Visita** | Ida a campo em data específica. Em RFO, cada visita gera um registro diário com equipe, serviços e medições. Em LTIP, cada visita gera observações e fotos por sistema. |
| **Sistema Predial** | Conjunto de componentes da edificação agrupados por função: Aberturas e Fechamentos, Acessibilidade, Circulações, Cobertura e Telhamento, Elementos Estruturais Aparentes, Impermeabilização, Instalações de Gás, Instalações de Telecomunicação, Revestimentos, Esquadrias, Prevenção e Combate a Incêndios, SPDA, Sistemas Elétricos, Hidrossanitários, Vedações Verticais. |
| **Subsistema** | Componente específico dentro de um Sistema Predial (ex.: Calhas e Rufos, Pilares, Mantas, Extintores). Listagem completa no gabarito `RFO_INSPECAO.md`. |
| **Ocorrência** | Item inspecionado com desvio registrado. Vinculada a um Sistema, Subsistema e Localização. Classificada por Situação, Classificação, Tipo de Anomalia/Falha, Grau de Risco e Prioridade. |
| **Foto** | Imagem digital capturada com Lightshot, câmera ou editor interno (RF-14), vinculada a uma Ocorrência ou a uma Visita de Fiscalização. Possui legenda técnica, que pode ser sugerida por IA a partir de anotação de campo/transcrição de áudio (RF-15) e é sempre revisada e aprovada por um profissional habilitado antes de compor o relatório. |
| **Relatório** | Documento final gerado pelo sistema: PDF e/ou DOCX. Representa a saída formal do serviço prestado. |
| **ART** | Anotação de Responsabilidade Técnica emitida no CREA. Existe ART de Fiscalização (do engenheiro fiscal) e ART de Execução (do RTE). Ambas têm número registrado no contrato. |
| **Medição** | Quantitativo de serviços executados em uma visita de fiscalização. Pode ser em m², unidades ou outro critério. |

### 4.2 Glossário técnico

| Termo | Definição |
|---|---|
| **Anomalia** | Irregularidade de origem no projeto, execução, material ou uso da edificação que compromete seu desempenho. |
| **Falha** | Irregularidade de origem na manutenção ou operação da edificação. |
| **Grau de Risco CMM** | Classificação de criticidade: **Crítico** (risco imediato à segurança ou estrutura), **Médio** (risco de agravamento a médio prazo), **Mínimo** (risco apenas estético ou de conforto). |
| **Método GUT** | Matriz de priorização por Gravidade, Urgência e Tendência. |
| **VUP** | Vida Útil de Projeto — expectativa de durabilidade dos sistemas segundo NBR 15575. |
| **NBR 16747** | Norma da ABNT para Inspeção Predial: diretrizes, conceitos, terminologia e procedimento. |
| **IBAPE-NA** | Norma de Inspeção Predial Nacional do IBAPE, complementar à NBR 16747. |
| **Retrofit** | Reforma que atualiza sistemas da edificação sem alteração de uso. |
| **Platibanda** | Elemento estrutural que arremata a cobertura, comumente impermeabilizado. |
| **RTE** | Responsável Técnico pela Execução — engenheiro da empresa que executa a obra. |
| **Lightshot** | Ferramenta de captura de tela (https://app.prntscr.com) usada em campo para capturar e anotar imagens. |

---

## 5. Regras de Negócio (RN)

| Código | Regra |
|---|---|
| **RN-01** | Um Relatório de Fiscalização de Obra possui exatamente um Contrato e N Visitas (uma por dia de obra acompanhado). |
| **RN-02** | Cada Visita do RFO deve registrar a data, os serviços executados, a equipe presente (função + quantidade de profissionais) e as observações do dia. |
| **RN-03** | Toda Ocorrência em LTIP e Vistoria deve ter pelo menos uma Foto vinculada. |
| **RN-04** | O Grau de Risco CMM de uma Ocorrência determina sua Prioridade padrão: Crítico = Prioridade 5, Médio = Prioridade 3, Mínimo = Prioridade 1. [A ESCLARECER] se o engenheiro pode sobrescrever manualmente. |
| **RN-05** | Toda Ocorrência deve ser classificada em: Situação (Conforme/Não Conforme), Classificação (Anomalia, Falha, Anomalia+Falha, Não se Aplica), Tipo de Anomalia (se aplicável), Tipo de Falha (se aplicável), Grau de Risco e Prioridade (0 a 5). |
| **RN-06** | Um Contrato pode envolver mais de uma empresa executora (subcontratadas), cada uma com CNPJ, Responsável Legal e RTE próprios. |
| **RN-07** | O documento final (Relatório/Laudo) deve ser fiel ao layout, terminologia e estrutura dos modelos atuais do cliente, incluindo cabeçalho com logo, dados do engenheiro e do CREA. |
| **RN-08** | Um Relatório somente pode ser marcado como "emitido" após ter todos os campos obrigatórios preenchidos e pelo menos uma foto por Ocorrência Não Conforme. |
| **RN-09** | Contratos possuem ART de Fiscalização (do engenheiro fiscal) e, quando aplicável, ART de Execução (do RTE). Os números devem constar no cabeçalho do relatório. |
| **RN-10** | Cada sistema predial inspecionado deve ser avaliado individualmente. A ausência de um sistema na edificação deve ser registrada como "Não se Aplica". |
| **RN-11** | O Relatório Fotográfico de Inspeção Predial organiza fotos estritamente por Sistema Predial e, dentro de cada sistema, por Subsistema. |
| **RN-12** | Documentos técnicos da edificação analisados durante a inspeção (projetos, ARTs anteriores) devem ser listados como "analisados" ou "ausentes" no laudo. |
| **RN-13** | [A ESCLARECER] Periodicidade obrigatória de re-inspeção por grau de risco: Crítico (90 dias?), Médio (6 meses?), Mínimo (anual?). |
| **RN-14** | Um usuário do tipo Cliente (RBAC — ver RF-13) só pode visualizar dados (dashboard, acompanhamento de visitas/ocorrências e relatórios) das Edificações/Contratos em que esteja vinculado como contratante. Nenhum dado de outro cliente ou de contratos de terceiros é acessível pelo Portal do Cliente. |
| **RN-15** | A imagem resultante do editor de anotação (RF-14) — com setas, formas, texto ou traço livre aplicados — substitui a imagem enviada como a Foto definitiva vinculada à Ocorrência/Visita; o sistema não é obrigado a reter a versão sem marcação. |
| **RN-16** | A legenda técnica sugerida por IA (RF-15) é sempre uma minuta sujeita à revisão e aprovação do profissional responsável antes de compor um relatório emitido; o sistema não deve permitir que uma legenda gerada por IA seja incluída no relatório sem essa aprovação explícita. |
| **RN-17** | Toda legenda gerada por IA deve preservar a rastreabilidade da origem: texto bruto/transcrição original, sugestão da IA, versão do prompt-sistema utilizada, usuário que aprovou/editou e data/hora da aprovação. |

---

## 6. Requisitos Funcionais (RF)

| Código | Requisito |
|---|---|
| **RF-01** | Cadastro de edificação com: nome/identificação, endereço completo, tipologia (residencial, comercial, misto), sistema construtivo, descrição de pavimentos, área total, proprietário/síndico, documentos técnicos (upload de projetos e ARTs). |
| **RF-02** | Criação e edição de Contratos de serviço vinculados a uma Edificação, com: número do contrato, tipo de serviço, objeto, data de início, prazo, contratante (PF/PJ), empresas executoras, engenheiro fiscal, RTE, ART de Fiscalização, ART de Execução, NBRs aplicáveis, observações gerais. |
| **RF-03** | Registro de Visitas (para RFO): data, serviços executados, equipe presente por função e quantidade, medições parciais (m², unidades), observações e fotos do dia. |
| **RF-04** | Registro de Ocorrências (para LTIP e Vistorias): vinculação a Sistema Predial, Subsistema, Localização, Situação (Conforme/Não Conforme), Classificação, Tipo de Anomalia, Tipo de Falha, Grau de Risco CMM, Prioridade (0-5), descrição textual e fotos vinculadas. |
| **RF-05** | Upload e vinculação de imagens a Ocorrências e Visitas, via clipboard paste no browser (compatível com imagens já marcadas externamente no Lightshot) ou upload manual. A função do Lightshot no fluxo do auditor é desenhar setas, marcações e anotações sobre a foto — não apenas capturar a tela; ver RF-14 para a mesma capacidade de marcação dentro do próprio sistema. |
| **RF-06** | Geração automática de Relatório em PDF e/ou DOCX a partir de template fiel ao modelo atual, com: cabeçalho com logo e dados do engenheiro, seções estruturadas, tabelas de ocorrências, fotos com legendas e sumário automático. |
| **RF-07** | Dashboard de saúde da edificação por sistema predial: contagem e proporção de itens Conforme/Não Conforme, distribuição por Grau de Risco (Mínimo/Médio/Crítico), média de gravidade por subsistema (similar ao Power BI do COND.md). |
| **RF-08** | Histórico de inspeções por edificação: linha do tempo de Contratos e Inspeções com acesso aos relatórios gerados e evolução dos indicadores. |
| **RF-09** | Controle de múltiplos clientes e obras/inspeções simultâneas: listagem filtrada por tipo de serviço, status (em andamento, concluído), edificação e período. |
| **RF-10** | Gabarito de sistemas prediais pré-carregado (conforme `RFO_INSPECAO.md`): lista de Sistemas, Subsistemas, Tipos de Anomalia/Falha e Localizações como dados mestre editáveis. |
| **RF-11** | Controle de versão dos relatórios emitidos: cada emissão gera uma nova versão (V01, V02...) e mantém o histórico. |
| **RF-12** | Gestão de múltiplas empresas executoras por contrato, cada uma com CNPJ, Responsável Legal, RTE e ART de Execução. |
| **RF-13** | Portal do Cliente (contratante/síndico): área somente leitura, restrita às Edificações/Contratos em que o usuário conste como contratante (RN-14), com dashboard de acompanhamento da auditoria/fiscalização em andamento (status das visitas/ocorrências) e acesso aos documentos (relatórios/laudos) já emitidos para download. |
| **RF-14** | Editor de anotação de imagens integrado ao fluxo de upload de fotos: setas, formas (retângulo/elipse), texto e traço livre sobre a foto, equivalente à marcação feita externamente no Lightshot — permite ao auditor marcar tecnicamente a anomalia diretamente no sistema, simplificando a confecção do relatório sem depender de uma ferramenta externa. |
| **RF-15** | Geração assistida por IA de legendas técnicas de fotos: a partir de anotação de campo, transcrição de áudio ou descrição bruta fornecida pelo auditor, o sistema envia os dados a um provedor de IA (LLM) usando um prompt-sistema técnico versionado — aplicável a qualquer tipo de relatório fotográfico (RFO, LTIP, Vistoria Cautelar, Vistoria Residencial, RFIP) — e retorna uma legenda sugerida, estruturada e classificada por nível de certeza. A sugestão é sempre apresentada em campo editável — nunca substitui automaticamente a legenda existente — e só passa a compor o relatório após revisão e aprovação do profissional habilitado (RN-16, RN-17). |

---

## 7. Requisitos Não Funcionais (RNF)

| Código | Requisito |
|---|---|
| **RNF-01** | **Usabilidade mobile em campo**: a interface de registro de visitas e ocorrências deve funcionar em smartphone (tela ≥ 5,5") sem necessidade de instalação de app nativo. Preferência por PWA. |
| **RNF-02** | **Operação offline**: [A ESCLARECER] se é necessário suporte a registro offline com sincronização posterior (em campo, nem sempre há conexão). |
| **RNF-03** | **Fidelidade ao template**: o relatório gerado deve ser visualmente indistinguível dos documentos atuais entregues ao cliente. Qualquer diferença no layout é inaceitável. |
| **RNF-04** | **Exportação PDF e DOCX**: o sistema deve gerar ambos os formatos; o DOCX permite edição manual pelo engenheiro antes da entrega final. |
| **RNF-05** | **Autenticação**: o sistema deve ter login com senha. Como é uso individual (um engenheiro) ou de pequena equipe, autenticação simples é suficiente. Dados de clientes devem ser protegidos. |
| **RNF-06** | **Performance de geração**: relatórios de até 200 páginas com 150+ fotos devem ser gerados em menos de 60 segundos. |
| **RNF-07** | **Armazenamento de imagens**: fotos devem ser armazenadas em serviço de objeto (S3/MinIO) para não onerar o banco relacional. |
| **RNF-08** | **Backup e versionamento**: dados devem ser persistidos com backup automático. [A ESCLARECER] frequência e destino do backup. |

---

## 8. Fluxos Principais

### Fluxo 1 — Relatório de Fiscalização de Obra (RFO)

```
Cadastra Edificação -> Cadastra Contrato (RFO) -> [Para cada dia de obra]
  Cria Visita (data + equipe + serviços + medições + fotos)
  -> [Ao final da obra ou período] Gera Relatório PDF/DOCX
  -> Emite Relatório ao contratante
```

### Fluxo 2 — Laudo de Inspeção Predial (LTIP)

```
Cadastra Edificação -> Cadastra Contrato (LTIP) -> [Em campo, por visita]
  Percorre sistemas prediais
  -> Por sistema: registra Ocorrências (situação, classificação, risco, prioridade, localização)
  -> Por ocorrência: vincula Fotos (Lightshot) com legenda técnica
  -> [Após todas as visitas] Gera Laudo com: sumário, metodologia, relatório fotográfico por sistema, tabelas GUT
  -> Revisa e emite versão V01
```

### Fluxo 3 — Vistoria Cautelar de Recebimento

```
Cadastra Edificação (obra em fase final) -> Cadastra Contrato (Vistoria Cautelar)
  -> Visita de campo: verifica conformidade do produto entregue com projeto/contrato
  -> Registra pendências e não conformidades por sistema/área
  -> Vincula fotos de evidência
  -> Gera Laudo de Vistoria Cautelar PDF/DOCX
```

### Fluxo 4 — Relatório Fotográfico

```
[Vinculado a um LTIP ou independente]
  -> Seleciona fotos registradas por sistema predial
  -> Sistema ordena automaticamente por Sistema > Subsistema
  -> Gera PDF com fotos + legendas no layout padrão
```

---

## 9. Lacunas [A ESCLARECER]

| # | Dúvida | Impacto |
|---|---|---|
| 1 | Existe periodicidade de re-inspeção mandatória por grau de risco (Crítico < 90 dias, Médio < 180 dias, Mínimo < 1 ano)? | Define se o sistema precisa de alertas/calendário. |
| 2 | O engenheiro trabalha sozinho ou tem auxiliares que também fazem registro em campo? | Define se autenticação multi-usuário é necessária. |
| 3 | O sistema precisa funcionar totalmente offline em campo (sem internet)? | Define necessidade de PWA com Service Worker + IndexedDB. |
| 4 | As fotos do Lightshot são salvas automaticamente em pasta monitorada ou somente na área de transferência? | Define estratégia de integração com Lightshot. |
| 5 | O DOCX gerado serve como rascunho editável antes da entrega, ou o PDF final deve ser definitivo sem edição manual? | Define se WeasyPrint (PDF direto) é suficiente ou se docxtpl (DOCX intermediário) é obrigatório. |
| 6 | ~~O cliente (síndico/proprietário) precisa ter acesso ao sistema para consultar relatórios, ou o engenheiro sempre entrega o PDF por e-mail?~~ **RESOLVIDA (2026-07-24):** sim, o cliente terá acesso a um Portal do Cliente próprio (dashboard de acompanhamento da auditoria + documentos), com login separado do Engenheiro Fiscal. | Gerou RF-13, RN-14 e a decisão de arquitetura DEC-18 (RBAC) em `00_docs/projeto/decisoes.md`. |
| 7 | Existe integração necessária com o CREA para consulta ou validação de ARTs? | Define complexidade da integração com sistemas externos. |
| 8 | As medições do RFO têm formato fixo (m²) ou variam por contrato (unidades, horas, etc.)? | Define flexibilidade do modelo de medições. |
| 9 | O engenheiro usa assinatura digital (ICP-Brasil) nos PDFs emitidos, ou a assinatura é apenas o CREA impresso? | Define se é necessário módulo de assinatura digital. |
| 10 | O campo "Prioridade 0" significa "sem prioridade definida" ou "não aplicável"? | Define tratamento no banco e na geração do relatório. |
| 11 | [A ESCLARECER] O acesso do cliente ao Portal (RF-13) é auto-cadastro, convite por e-mail enviado pelo engenheiro, ou criação manual de credencial pelo próprio engenheiro fiscal? | Define o fluxo de onboarding do usuário Cliente (BL-30). Posição interina: criação manual pelo engenheiro fiscal (sem auto-cadastro público), mais simples e segura para o v1.0. |
| 12 | [A ESCLARECER] O Portal do Cliente deve permitir múltiplos contratantes por Edificação (ex.: síndico atual + administradora) ou apenas um usuário Cliente por Edificação/Contrato? | Define se o vínculo Usuario↔Responsavel é 1:1 ou 1:N (BL-30). Posição interina: 1:N (um Contrato tem um contratante, mas o mesmo Responsavel/contratante pode logar em múltiplos Contratos/Edificações se vinculado a mais de um). |
| 13 | [A ESCLARECER] Qual provedor de IA/LLM (ex.: OpenAI, Azure OpenAI, Anthropic Claude, outro) será utilizado para a geração assistida de legendas técnicas (RF-15), considerando custo por chamada, política de retenção/treinamento sobre os dados enviados (fotos e descrições de imóveis de clientes) e disponibilidade/latência de API? | Define a implementação do Adapter `LegendaIAClient` (ADR-12 em `arquitetura.md`) e o tratamento de dados sensíveis enviados a terceiros (OWASP A02). |
