# Análise Comparativa dos Contratos de Prestação de Serviços de Desenvolvimento

**Perspectiva de análise:** CONTRATADO (prestador de serviços de desenvolvimento)
**Documentos comparados:**
- Versão original: [contrato-prestacao-servicos-desenvolvimento.md](contrato-prestacao-servicos-desenvolvimento.md)
- Versão revisada (proposta pela CONTRATANTE): [Contrato_Revisado_Garra_Software.md](../01_output-context/Contrato_Revisado_Garra_Software.md)
- Versão negociada/final (partes já qualificadas): [Contrato_Prestacao_Servicos_Software.md](convertidos/Contrato_Prestacao_Servicos_Software.md)

**Data da análise:** 16/07/2026

---

## Resumo Executivo

Existem duas versões do mesmo contrato: uma minuta original mais equilibrada e uma versão **revisada pelo lado da CONTRATANTE**, redigida para proteger prioritariamente os interesses da Garra Engenharia. A versão revisada **reduz o valor recebido pelo CONTRATADO, aumenta suas obrigações, retira suas garantias de retenção/leverage e amplia sua responsabilidade civil de forma desproporcional**. Do ponto de vista do CONTRATADO, a versão revisada **não deve ser assinada sem negociação prévia** de pelo menos seis a oito pontos críticos identificados abaixo.

---

## Comparativo Direto (Original x Revisada)

| Tema | Original (docs) | Revisada (output-context) | Impacto para o CONTRATADO |
|---|---|---|---|
| Valor total | R$ 5.500,00 | R$ 5.000,00 | 🔴 Redução de ~9% no valor-base |
| Parcela mensal | R$ 550,00 | R$ 500,00 | 🔴 Renda mensal menor |
| Prazo de conclusão | Sem data fixa (incremental) | Data fixa a inserir + cronograma no Anexo I | 🟡 Maior pressão de prazo e risco de multa |
| Aceite de entregas | Tácito em 7 dias | Expresso e escrito, prazo 10 dias úteis, **sem aceite tácito** | 🔴 Pode atrasar pagamento indefinidamente se cliente não se manifestar |
| Propriedade intelectual | Cedida só após **quitação integral** (retenção como garantia) | Cedida **progressivamente**, por entrega paga, de forma ampla (inclusive para comercializar/sublicenciar a terceiros) | 🔴 Perda da principal moeda de negociação |
| Retenção de código/credenciais | Não tratado (implícito controle do CONTRATADO até entrega final) | **Proibida expressamente**, mesmo em caso de disputa financeira; acesso admin da CONTRATANTE desde o início | 🔴 Elimina o poder de barganha em caso de inadimplência do cliente |
| Multas por atraso | Só multa compensatória de 10% em inadimplemento essencial | Multa moratória diária de 0,5%/dia (até 10%) **+** multa compensatória de 10% | 🔴 Penalidades cumulativas e mais severas |
| Limite de responsabilidade | Limitada ao valor do contrato | **Sem limite** em diversas hipóteses (dolo, culpa grave, sigilo, PI, LGPD, perda de dados, retenção de ativos) | 🔴 Exposição patrimonial ilimitada |
| Notificação de incidente LGPD | 48 horas | 12 horas | 🟡 Prazo muito mais apertado, difícil cumprir sozinho |
| Rescisão sem culpa pela CONTRATANTE | Aviso de 30 dias, paga proporcional | Aviso de **15 dias**, paga só o "aproveitável e aceito", descontando "custos de correção" (critério subjetivo) | 🔴 Menos previsibilidade de recebimento em caso de rescisão |
| Rescisão por inadimplemento do cliente | Notificação e rescisão após 30 dias + 10 dias úteis | Igual, mas com obrigação de manter dados/continuidade mesmo durante a mora | 🟡 Obrigação de "preservar dados" mesmo sem receber |
| Auditoria pela CONTRATANTE | Não prevista | Prevista, inclusive por terceiro, com aviso "razoável" ou imediata em incidente | 🟡 Nova obrigação de exposição |
| Confidencialidade | 5 anos, para todas as informações | 5 anos para informações gerais, **prazo indeterminado** para segredos empresariais e dados pessoais | 🟡 Obrigação perpétua em parte das informações |
| Garantia | Durante a vigência (10 meses) | 90 dias após aceite final **ou última correção**, "prevalecendo a data posterior", mesmo após o fim da vigência | 🟡 Pode se estender indefinidamente se houver correções tardias |
| Bônus de pontualidade | Condicionado a aceite (tácito ou expresso) | Condicionado a aceite final expresso + entrega de código, documentação, credenciais e ausência de pendências críticas | 🟡 Requisitos mais difíceis de cumprir para receber o bônus |

---

## Pontos Críticos (versão revisada)

### 🔴 Alto — Perda da garantia de recebimento (leverage)
Cláusulas 5.4 e 14.5 proíbem qualquer retenção de código, credenciais ou ativos, **mesmo em caso de controvérsia financeira**. Combinado com a cessão progressiva de PI (6.1) e a exigência de acesso administrativo permanente da CONTRATANTE ao repositório desde o início (5.1), o CONTRATADO perde toda alavancagem para forçar o pagamento em caso de inadimplência do cliente.

*Fundamento legal:* art. 476 do Código Civil (exceção do contrato não cumprido) ainda seria aplicável mesmo sem cláusula expressa — mas a redação atual tenta **afastar contratualmente** esse direito, o que é discutível e deveria ser objeto de negociação.

### 🔴 Alto — Responsabilidade civil ilimitada
Cláusula 13.3 remove o teto de responsabilidade em hipóteses amplas e de conceito aberto ("culpa grave", "violação de segurança"), o que na prática pode ser usado para argumentar responsabilidade ilimitada em quase qualquer incidente.

*Fundamento legal:* art. 944 do Código Civil permite redução de indenização por equidade, mas a cláusula, ao afastar previamente qualquer teto, dificulta essa defesa.

### 🔴 Alto — Aceite sem presunção de tácito
Cláusula 3.2 elimina o aceite tácito, condicionando pagamento a aceite expresso. Sem prazo de "silêncio = aceite", a CONTRATANTE pode postergar indefinidamente o pagamento apenas não se manifestando.

*Sugestão:* reintroduzir cláusula de aceite tácito decorrido o prazo de teste, como na versão original.

### 🟡 Médio — Multas cumulativas
Cláusula 13.1 (moratória diária) + 13.2 (compensatória) podem, somadas, ultrapassar 20% do valor do contrato por um único atraso, sem cobertura de força maior expressamente ressalvada de forma objetiva.

### 🟡 Médio — Prazo de notificação de incidente de 12h
Tecnicamente exigente para um prestador individual/pequena equipe. Recomenda-se negociar para 24h ou 48h como na versão original.

### 🟢 Baixo — Redução de valor (R$ 5.500 → R$ 5.000)
Comercialmente relevante, mas não é questão jurídica — é ponto de negociação de preço.

---

## Cláusulas Recomendadas / Alterações Sugeridas

| Cláusula Atual (revisada) | Problema | Redação Sugerida | Base Legal |
|---|---|---|---|
| 5.4 / 14.5 — vedação de retenção mesmo em disputa financeira | Remove o único mecanismo de pressão para receber | "O CONTRATADO poderá suspender a concessão de novos acessos ou entregas, mediante notificação prévia de 5 dias úteis, em caso de inadimplemento de valor incontroverso superior a 15 dias, sem prejuízo da preservação dos dados já entregues" | art. 476, Código Civil (exceptio non adimpleti contractus) |
| 13.3 — responsabilidade ilimitada | Exposição patrimonial desproporcional ao valor do contrato (R$ 5.000) | Manter teto de responsabilidade em, por exemplo, 2x ou 3x o valor do contrato, exceto dolo comprovado | art. 944, Código Civil |
| 3.2 — ausência de aceite tácito | Pagamento pode ficar indefinidamente pendente | "Decorrido o prazo de 10 dias úteis sem manifestação expressa e fundamentada da CONTRATANTE, a entrega será considerada tacitamente aceita para fins de faturamento" | art. 421-A, Código Civil (função social e boa-fé objetiva) |
| 8.4 — prazo de 12h para notificar incidente | Incompatível com estrutura de prestador autônomo/pequena equipe | Ajustar para 24h a 48h | Lei 13.709/2018 (LGPD), art. 48 — a lei não fixa prazo rígido, é negociável |
| 6.1 — cessão progressiva ampla de PI | Cede inclusive direito de comercializar/sublicenciar a terceiros, algo que extrapola uma prestação de serviço pontual | Restringir a cessão ao uso interno da CONTRATANTE e seus clientes diretos, vedando sublicenciamento a terceiros não relacionados sem remuneração adicional | Lei 9.609/1998 (Lei do Software), art. 4º |
| 13.1 + 13.2 — multas cumulativas | Pode ultrapassar patamar razoável frente ao valor do contrato | Prever que a multa moratória diária seja **compensada** (e não somada) com eventual multa compensatória pelo mesmo fato gerador | art. 413, Código Civil (redução equitativa de cláusula penal) |

---

## Parecer Final

**Negociar antes de assinar.** A versão revisada é tecnicamente bem construída e juridicamente válida, mas está **desequilibrada em favor da CONTRATANTE** em pontos estruturais para o CONTRATADO: perda de garantia de pagamento (proibição de retenção), responsabilidade ilimitada, ausência de aceite tácito e redução de valor. Para um contrato de baixo valor total (R$ 5.000,00) com escopo tecnicamente extenso (14+ módulos, PWA, LGPD, backup, SLA), a assimetria de risco é desproporcional.

Recomenda-se negociar, no mínimo, os itens 🔴 (retenção/leverage, responsabilidade ilimitada, aceite tácito) antes da assinatura. Os itens 🟡 podem ser aceitos com ajustes pontuais.

> **Aviso:** esta análise não substitui parecer de advogado(a) contratado(a) para revisão final e assessoria na negociação, especialmente quanto à cláusula de responsabilidade ilimitada, que merece atenção jurídica específica antes de assinar.

---

## Atualização — Análise da Versão Negociada/Final

**Documento:** [Contrato_Prestacao_Servicos_Software.md](convertidos/Contrato_Prestacao_Servicos_Software.md)
**Partes já qualificadas:** CONTRATANTE = Garra Perícias e Avaliações Ltda. (CNPJ 49.049.662/0001-45); CONTRATADO = 65.773.915 Rafael Roriz de Menezes Pereira (CNPJ 65.773.915/0001-85), representado por Rafael Menezes Bento Roriz.

### Resumo Executivo da Atualização

Esta terceira versão do contrato **corrige a grande maioria dos pontos críticos** apontados na análise da "Versão Revisada" (seção anterior). Os principais mecanismos de proteção retirados na revisão anterior foram **reintroduzidos de forma equilibrada**, mantendo, ao mesmo tempo, garantias legítimas para a CONTRATANTE (não bloqueio de dados, preservação de ativos, LGPD). Do ponto de vista do CONTRATADO, esta versão é **sensivelmente mais segura e assinável**, restando poucos pontos a ajustar antes da assinatura.

### O que melhorou em relação à "Versão Revisada" anterior

| Tema | Versão Revisada (anterior) | Versão Negociada/Final (atual) | Efeito para o CONTRATADO |
|---|---|---|---|
| Aceite tácito | Eliminado — só aceite expresso | Reintroduzido (3.2.1): decorridos 10 dias úteis sem manifestação, entrega considerada aceita **para fins de faturamento** | 🟢 Resolve o risco de pagamento indefinidamente pendente |
| Apontamentos genéricos da CONTRATANTE | Não tratado | Cláusula 3.2.3: apontamentos vagos podem ser objeto de pedido de complementação, suspendendo o prazo até esclarecimento | 🟢 Evita manobra de recusa sem fundamento |
| Retenção/suspensão em caso de inadimplência | Proibição total, mesmo em disputa financeira | Cláusula 5.4: CONTRATADO pode suspender **novas funcionalidades e evolutivo** após 15 dias de inadimplência incontroversa + notificação de 5 dias úteis (mantendo, porém, acesso a dados e entregas já pagas) | 🟢 Devolve leverage proporcional, sem comprometer dados do cliente |
| Retenção de entregas não pagas na rescisão | Vedada integralmente (14.5 anterior) | Cláusula 14.5 atual: veda retenção de dados/ativos, mas permite **suspender a disponibilização definitiva de entregas ainda não pagas** até regularização | 🟢 Preserva parte do mecanismo de cobrança |
| Cessão de PI | Ampla e imediata por entrega paga | Cláusula 6.1: cessão condicionada a entregas **integralmente pagas**; cláusula 6.6 prevê negociação de participação do CONTRATADO caso a CONTRATANTE comercialize o Sistema como produto autônomo a terceiros | 🟡 Melhora, mas 6.6 é apenas expectativa de negociação futura, não direito garantido |
| Multa moratória | 0,5%/dia sobre o **valor total do contrato**, até 10% | Cláusula 13.1: 0,5%/dia sobre o valor da **parcela ou marco em atraso**, até 10% desse valor | 🟢 Redução drástica da exposição financeira |
| Cumulação de multas | Moratória + compensatória cumulativas | Cláusula 13.2.1: **vedada cumulação pelo mesmo fato gerador**; valores de multa moratória compensados na compensatória | 🟢 Resolve o risco de dupla penalização |
| Excludente de força maior | Não prevista expressamente | Cláusula 13.3: exclui multa em caso de força maior, caso fortuito, culpa da CONTRATANTE ou alteração formal de escopo | 🟢 Proteção adicional relevante |
| Responsabilidade ilimitada | Hipóteses amplas e abertas ("culpa grave", "violação de segurança") | Cláusula 13.4: hipóteses **fechadas e objetivas** (dolo/fraude, violação intencional de sigilo, apropriação indevida, infração de PI por componente não autorizado, destruição/retenção deliberada de dados, código malicioso) | 🟢 Reduz drasticamente o risco de interpretação extensiva |
| Incidentes não dolosos de segurança | Não tratados separadamente | Cláusula 13.5: responsabilidade apurada proporcionalmente (causa, culpa, medidas preventivas, extensão do dano) | 🟢 Afasta responsabilidade objetiva/automática |
| Prazo de notificação de incidente LGPD | 12 horas | 24 horas, com comunicação preliminar admitida e relatório complementar em até 3 dias úteis (cláusulas 8.4 a 8.4.3) | 🟢 Prazo mais realista para prestador autônomo |
| Vulnerabilidade não explorada | Tratada como incidente | Cláusula 8.4.3: vulnerabilidade ainda não explorada não é automaticamente incidente com dados pessoais | 🟢 Evita notificações desnecessárias |
| Retenção de pagamento por controvérsia alheia | Não vedada | Cláusula 4.2.2: CONTRATANTE não pode reter parcela de entrega aceita por motivo de **outra** controvérsia | 🟢 Protege fluxo de caixa do CONTRATADO |
| Pagamento proporcional de marco parcial | Não previsto | Cláusula 4.2.1: admite pagamento proporcional de marco parcialmente cumprido, mediante registro escrito | 🟢 Flexibiliza faturamento |

### Pontos que ainda merecem atenção

🟡 **Médio — Rescisão sem culpa com aviso de 15 dias (cláusula 14.1)**
Mantido o prazo curto de 15 dias para rescisão imotivada pela CONTRATANTE (versus 30 dias na minuta original). Ainda que a cláusula 4.2.2 proteja o recebimento de entregas já aceitas, o prazo curto reduz o tempo de reação comercial do CONTRATADO.
*Sugestão:* negociar para 30 dias, alinhando com a prática usual de prestação de serviços continuados.

🟡 **Médio — Cessão de PI ainda ampla, com "comercialização por terceiros" apenas sujeita a negociação futura (cláusula 6.6)**
A cláusula 6.6 não garante remuneração adicional ao CONTRATADO caso a CONTRATANTE venda o Sistema como produto para terceiros — apenas prevê que "as partes poderão negociar". Não há obrigação, prazo ou parâmetro para essa negociação.
*Sugestão:* transformar em direito de participação mínima ou de preferência para prestação de serviços de manutenção/customização, com percentual ou condições definidas desde já.

🟡 **Médio — Anexo I ainda com diversos campos em branco**
Prazos de severidade de suporte, RPO/RTO, disponibilidade mínima, frequência de backup, data-limite de conclusão e critérios objetivos de aceite por módulo continuam como `INSERIR`. Sem esse preenchimento, a cláusula 3.4 (correções não configuram alteração de escopo) e a cláusula 13 (penalidades por atraso) ficam com base fática indefinida, o que gera risco de controvérsia sobre o que é ou não "conforme".
*Sugestão:* não assinar sem o Anexo I integralmente preenchido e rubricado, como já alerta o próprio documento.

🟢 **Baixo — Valor do contrato mantido em R$ 5.000,00 / parcelas de R$ 500,00**
Ponto comercial, não jurídico, mas ainda inferior ao valor da minuta original (R$ 5.500,00). Cabe negociação de preço, se desejado, independentemente da qualidade jurídica do texto.

🟢 **Baixo — Confidencialidade por prazo indeterminado para segredos empresariais e dados pessoais (cláusula 7.4)**
Mantida a mesma redação da versão revisada. Compatível com a prática de mercado e com a natureza sensível de laudos periciais, não havendo necessidade de alteração.

### Parecer Final Atualizado

**Assinável, condicionada ao preenchimento integral do Anexo I e à negociação pontual de dois itens.** A versão negociada representa evolução significativa em relação à "Versão Revisada": restabeleceu o aceite tácito, tornou as multas proporcionais e não cumulativas, delimitou objetivamente as hipóteses de responsabilidade ilimitada e devolveu ao CONTRATADO um mecanismo de suspensão de novas entregas em caso de inadimplência, sem comprometer os dados da CONTRATANTE.

Antes de assinar, recomenda-se:
1. **Exigir o preenchimento completo do Anexo I** (datas, critérios de aceite objetivos, SLAs, RPO/RTO, backup) — condição para a segurança jurídica de todas as cláusulas de prazo e penalidade.
2. Negociar a ampliação do prazo de rescisão imotivada de 15 para 30 dias (cláusula 14.1).
3. Buscar parâmetros objetivos (percentual, prazo, condições) para a participação do CONTRATADO prevista na cláusula 6.6, em vez de mera expectativa de negociação futura.

Os demais pontos identificados nesta versão são compatíveis com uma relação contratual equilibrada entre as partes.

> **Aviso:** esta análise não substitui parecer de advogado(a) contratado(a) para revisão final antes da assinatura, especialmente quanto ao preenchimento do Anexo I e à formalização da cláusula 6.6.
