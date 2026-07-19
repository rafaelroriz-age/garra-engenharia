# CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO E MANUTENÇÃO DE SOFTWARE

---


## QUALIFICAÇÃO DAS PARTES

**CONTRATADO:**
Nome completo: _____________________________________________
CPF: ___.___.___-___
RG: ______________ — Órgão Emissor: ________ — UF: ___
Endereço: _______________________________________________, n.º ______, Bairro: _________________, Cidade: ___________________, Estado: ___, CEP: ___-___
E-mail: ___________________________
Telefone: (___)_____________

**CONTRATANTE:**
Nome completo: _____________________________________________
Profissão:  _____________________________________________
CPF/CNPJ: ___.___.___-___ / __.___.___/____-__
Endereço: _______________________________________________, n.º ______, Bairro: _________________, Cidade:  ___________________, Estado: ___, CEP: ___-___
E-mail: ___________________________
Telefone: (___)_____________


---

As partes acima qualificadas têm entre si justo e contratado o presente **Contrato de Prestação de Serviços de Desenvolvimento e Manutenção de Software**, que se regerá pelas cláusulas e condições seguintes, nos termos dos arts. 593 a 609 do Código Civil (Lei n.º 10.406/2002) e demais legislação aplicável.

---

## CLÁUSULA PRIMEIRA — DO OBJETO

**1.1.** O presente contrato tem por objeto a **prestação de serviços de desenvolvimento e manutenção de sistema web de automação de relatórios técnicos de engenharia predial**, denominado internamente "Sistema de Automação de Relatórios Prediais — Garra Engenharia", doravante referido apenas como **"o Sistema"**.

**1.2.** O escopo das entregas compreende, de forma não exaustiva, as seguintes funcionalidades:

| Módulo | Descrição |
|--------|-----------|
| Cadastro de edificações | Registro de sistemas prediais, caracterização física e documentos técnicos |
| Contratos de serviço | Gestão de partes, Responsável Técnico, ARTs e documentos |
| Relatório de Fiscalização de Obra (RFO) | Visitas, mão de obra, medições e registro fotográfico |
| Laudo Técnico de Inspeção Predial (LTIP) | Ocorrências por sistema, classificação CMM + GUT |
| Vistoria Cautelar de Recebimento | Conformidade com projeto e contrato |
| Vistoria de Imóvel Residencial | Diagnóstico por cômodo e sistema |
| Relatório Fotográfico de Inspeção Predial (RFIP) | Fotos organizadas por sistema |
| Integração de captura de imagens | Suporte a clipboard paste e upload manual (Lightshot) |
| Geração de PDF | Fiel ao template do cliente via WeasyPrint/HTML |
| Geração de DOCX | Via template Word do cliente |
| Dashboard de saúde predial | Painel por edificação e sistema predial |
| Histórico de inspeções | Versionamento por edificação |
| Interface PWA | Funcional em smartphone para uso em campo |
| Autenticação e segurança | JWT + bcrypt |

**1.3.** O preço contratado remunera as **funcionalidades entregues e a mão de obra do CONTRATADO**, não constituindo cessão de direitos de terceiros, licenças de software externo ou custos de infraestrutura de hospedagem, que serão tratados separadamente, se necessário.

**1.4.** Ajustes no escopo que representem acréscimo substancial de funcionalidades não previstas neste contrato deverão ser formalizados por meio de **Termos Aditivos** assinados pelas partes, com definição de valor e cronograma específicos.

---

## CLÁUSULA SEGUNDA — DA FORMA DE EXECUÇÃO

**2.1.** O CONTRATADO executará os serviços com **autonomia técnica**, na qualidade de profissional independente, sem vínculo empregatício com o CONTRATANTE, nos termos do art. 593 do Código Civil.

**2.2.** Não existe data limite predefinida para a conclusão global do desenvolvimento do Sistema. A entrega ocorrerá de forma **incremental**, por módulos e funcionalidades, conforme priorização acordada entre as partes.

**2.3.** As entregas parciais serão validadas pelo CONTRATANTE em prazo de até **7 (sete) dias corridos** após a comunicação do CONTRATADO. Decorrido esse prazo sem manifestação, a entrega parcial será considerada **tacitamente aceita**.

**2.4.** O CONTRATADO manterá o CONTRATANTE informado sobre o progresso por meio de comunicação periódica (e-mail ou aplicativo de mensagens acordado entre as partes).

**2.5.** O CONTRATANTE se compromete a fornecer, em tempo hábil, os materiais necessários para a execução dos serviços, incluindo: templates de documentos (Word/HTML), dados mestre de sistemas prediais, credenciais de ambientes, e feedback sobre as entregas parciais.

---

## CLÁUSULA TERCEIRA — DO VALOR E DAS CONDIÇÕES DE PAGAMENTO

**3.1.** Pelos serviços de desenvolvimento e manutenção prestados durante a vigência deste contrato, o CONTRATANTE pagará ao CONTRATADO o valor total de **R$ 5.500,00 (cinco mil e quinhentos reais)**, dividido em **10 (dez) parcelas mensais de R$ 550,00 (quinhentos e cinquenta reais)** cada.

**3.2.** As parcelas serão pagas mensalmente, com vencimento todo dia ___ de cada mês, iniciando-se no mês subsequente à assinatura deste instrumento.

**3.3.** O pagamento será realizado por meio de [Pix / transferência bancária / boleto] para:

> Chave Pix / Banco: ______________________________
> Agência: _________ Conta: _____________________
> Titular: _____________________________________________

**3.4. — BÔNUS DE PONTUALIDADE NA ENTREGA:**

Fica estabelecido o seguinte bônus por conclusão antecipada das funcionalidades essenciais do Sistema (conforme Cláusula Primeira), a ser pago conjuntamente com a parcela do mês da entrega final:

| Prazo de conclusão a partir da assinatura | Valor do Bônus |
|-------------------------------------------|----------------|
| Até **2 (dois) meses** | **R$ 500,00 (quinhentos reais)** |
| Acima de 2 meses e até **5 (cinco) meses** | **R$ 200,00 (duzentos reais)** |
| Acima de 5 meses | Sem bônus |

**3.4.1.** Para fins desta cláusula, considera-se "conclusão" a entrega e aceite formal das funcionalidades essenciais do Sistema listadas na Cláusula Primeira, mediante comunicação escrita do CONTRATADO e validação expressa ou tácita (conforme §2.3) pelo CONTRATANTE.

**3.5.** O atraso no pagamento de qualquer parcela por período superior a **15 (quinze) dias corridos** implicará incidência de:
- Multa de **2% (dois por cento)** sobre o valor da parcela em atraso;
- Juros de mora de **1% (um por cento)** ao mês, pro rata die;
- Correção monetária pelo **IPCA** desde o vencimento até o efetivo pagamento.

**3.6.** Nenhum atraso de pagamento por parte do CONTRATANTE autoriza a suspensão unilateral dos serviços pelo CONTRATADO antes de notificação prévia de **10 (dez) dias úteis**.

---

## CLÁUSULA QUARTA — DA VIGÊNCIA E DA MANUTENÇÃO

**4.1.** O presente contrato vigorará pelo prazo de **10 (dez) meses** contados da data de sua assinatura, abrangendo tanto o desenvolvimento quanto a manutenção corretiva do Sistema entregue.

**4.2.** Entende-se por **manutenção corretiva** a correção de erros e bugs nas funcionalidades entregues e aceitas, sem custo adicional, pelo período de vigência contratual.

**4.3.** Solicitações de novas funcionalidades, alterações de escopo ou personalizações adicionais durante o período de manutenção serão tratadas como **novos serviços**, sujeitos a orçamento e aditivo contratual.

**4.4.** Ao término da vigência, as partes poderão celebrar novo contrato de manutenção evolutiva ou suporte técnico, em condições a negociar.

---

## CLÁUSULA QUINTA — DAS OBRIGAÇÕES DO CONTRATADO

O CONTRATADO obriga-se a:

**a)** Executar os serviços com **boa técnica, diligência e profissionalismo**, observando as melhores práticas de desenvolvimento de software;

**b)** Manter **sigilo absoluto** sobre todas as informações técnicas, comerciais e pessoais do CONTRATANTE, de seus clientes e de terceiros às quais tiver acesso em razão deste contrato;

**c)** Corrigir, **sem ônus adicional**, os defeitos ou erros resultantes de falha na execução dos serviços, durante a vigência do contrato;

**d)** Comunicar ao CONTRATANTE, com antecedência razoável, qualquer impedimento ou circunstância que possa comprometer o andamento dos serviços;

**e)** Entregar ao CONTRATANTE, ao final do contrato ou em caso de rescisão, o **código-fonte completo** do Sistema, juntamente com documentação mínima de uso e implantação;

**f)** Não subcontratar total ou parcialmente os serviços sem autorização prévia e expressa do CONTRATANTE.

---

## CLÁUSULA SEXTA — DAS OBRIGAÇÕES DO CONTRATANTE

O CONTRATANTE obriga-se a:

**a)** Efetuar os pagamentos nas datas e condições previstas na Cláusula Terceira;

**b)** Fornecer, em tempo hábil, todas as informações, materiais, acessos e feedbacks necessários à execução dos serviços;

**c)** Designar um responsável para validação das entregas e comunicação com o CONTRATADO;

**d)** Não utilizar o Sistema, ou quaisquer partes dele, para finalidades diversas das previstas neste contrato, especialmente para revenda ou sublicenciamento a terceiros sem anuência do CONTRATADO;

**e)** Manter a confidencialidade das credenciais de acesso ao sistema e de quaisquer informações técnicas recebidas do CONTRATADO.

---

## CLÁUSULA SÉTIMA — DA PROPRIEDADE INTELECTUAL

**7.1.** O Sistema desenvolvido em decorrência deste contrato, incluindo código-fonte, arquitetura, interfaces e documentação técnica produzida exclusivamente para este projeto, será de **propriedade intelectual do CONTRATANTE**, nos termos do art. 4.º da Lei n.º 9.609/1998 (Lei do Software), após a **quitação integral** do valor contratual.

**7.2.** Até a quitação integral, o CONTRATANTE possuirá **licença de uso não exclusiva** do Sistema, podendo operá-lo internamente, mas sem direito de ceder, sublicenciar ou comercializar o software a terceiros.

**7.3.** O CONTRATADO poderá utilizar **componentes de código aberto** (open source) de licença compatível (MIT, Apache 2.0, LGPL) na composição do Sistema, mantendo o registro de todas as dependências utilizadas e suas respectivas licenças.

**7.4.** O CONTRATADO reserva-se o direito de mencionar o projeto no seu portfólio profissional, **sem divulgar informações confidenciais** ou dados de clientes do CONTRATANTE, salvo autorização expressa.

---

## CLÁUSULA OITAVA — DA CONFIDENCIALIDADE

**8.1.** Cada parte se compromete a manter em sigilo todas as informações confidenciais da outra parte às quais tiver acesso em razão deste contrato, incluindo, mas não se limitando a: dados técnicos, estratégicos, comerciais, financeiros, de clientes e de processos internos.

**8.2.** A obrigação de sigilo permanece vigente por **5 (cinco) anos** após o término ou rescisão deste contrato.

**8.3.** Não se considera quebra de confidencialidade a divulgação de informações: (i) que se tornarem públicas sem culpa das partes; (ii) por determinação judicial ou administrativa; (iii) já conhecidas antes da celebração deste contrato.

---

## CLÁUSULA NONA — DA PROTEÇÃO DE DADOS PESSOAIS (LGPD)

**9.1.** As partes reconhecem que a execução deste contrato pode envolver o tratamento de dados pessoais de terceiros (clientes finais do CONTRATANTE, proprietários de imóveis, funcionários, etc.) e comprometem-se a cumprir integralmente a **Lei n.º 13.709/2018 — Lei Geral de Proteção de Dados Pessoais (LGPD)** e demais normativos editados pela **Autoridade Nacional de Proteção de Dados (ANPD)**.

**9.2. — Papéis no tratamento de dados:**

Para fins da LGPD, ficam estabelecidos os seguintes papéis:

- **CONTRATANTE**: atua como **Controlador** dos dados pessoais de seus clientes e terceiros inseridos no Sistema, sendo responsável pelas decisões sobre o tratamento (finalidade, forma e duração);
- **CONTRATADO**: atua como **Operador**, tratando os dados em nome e conforme as instruções do Controlador, exclusivamente para os fins previstos neste contrato.

**9.3.** O CONTRATADO compromete-se a:

**a)** Tratar os dados pessoais **somente** para as finalidades necessárias à execução dos serviços previstos neste contrato;

**b)** **Não compartilhar** dados pessoais com terceiros sem autorização prévia e expressa do CONTRATANTE, salvo obrigação legal;

**c)** Adotar **medidas técnicas e administrativas** adequadas para proteger os dados pessoais contra acessos não autorizados, destruição, alteração ou divulgação indevida (art. 46, LGPD), incluindo: criptografia de senhas (bcrypt), autenticação com JWT, controle de acesso por perfil e comunicações via HTTPS;

**d)** **Notificar o CONTRATANTE**, no prazo máximo de **48 (quarenta e oito) horas**, caso tome conhecimento de qualquer incidente de segurança que possa afetar dados pessoais (art. 48, LGPD);

**e)** Eliminar ou devolver os dados pessoais ao CONTRATANTE ao término da vigência contratual, salvo obrigação legal de retenção;

**f)** Auxiliar o CONTRATANTE, na medida do possível, no atendimento de requisições de titulares de dados (arts. 17 a 22, LGPD).

**9.4.** O CONTRATANTE, na qualidade de Controlador, é responsável por:

**a)** Garantir que existe **base legal** adequada (art. 7.º, LGPD) para o tratamento dos dados pessoais inseridos no Sistema;

**b)** Informar os titulares de dados sobre o tratamento realizado, quando aplicável;

**c)** Definir as políticas internas de retenção, exclusão e compartilhamento de dados pessoais.

**9.5.** O descumprimento das obrigações desta cláusula por qualquer das partes gera responsabilidade civil pelos danos causados aos titulares de dados, nos termos dos arts. 42 a 45 da LGPD.

---

## CLÁUSULA DÉCIMA — DAS PENALIDADES

**10.1.** O inadimplemento de obrigações essenciais deste contrato, após notificação prévia com prazo razoável para regularização, sujeitará a parte infratora ao pagamento de multa compensatória de **10% (dez por cento)** sobre o valor total do contrato (R$ 5.500,00), sem prejuízo de perdas e danos apurados.

**10.2.** A multa prevista no item anterior não se aplica cumulativamente aos encargos por atraso de pagamento previstos na Cláusula Terceira, que são autônomos.

**10.3.** Nenhuma penalidade poderá ser aplicada sem que a parte inadimplente seja previamente notificada por escrito e não regularize a situação no prazo concedido.

---

## CLÁUSULA DÉCIMA PRIMEIRA — DA RESCISÃO

**11.1.** O presente contrato poderá ser rescindido:

**a) Por mútuo acordo** entre as partes, formalizado por escrito, com acerto das obrigações cumpridas até a data da rescisão;

**b) Por iniciativa do CONTRATANTE**, mediante notificação escrita com antecedência mínima de **30 (trinta) dias**, hipótese em que serão devidas ao CONTRATADO todas as parcelas vencidas e a **remuneração proporcional** pelos serviços executados e não ainda remunerados, calculada com base nas entregas parciais aceitas;

**c) Por iniciativa do CONTRATADO**, mediante notificação escrita com antecedência mínima de **30 (trinta) dias**, hipótese em que deverá concluir as entregas em andamento e transferir toda a documentação e código ao CONTRATANTE;

**d) Por justa causa**, imediatamente, nos casos de: (i) atraso de pagamento superior a 30 dias após notificação; (ii) violação grave e não remediada de cláusulas essenciais; (iii) violação comprovada de obrigações de confidencialidade ou proteção de dados.

**11.2.** Na rescisão por justa causa imputável ao CONTRATANTE, além do acerto das parcelas vencidas e dos serviços executados, será devida ao CONTRATADO a **multa rescisória** prevista na Cláusula Décima.

**11.3.** Na rescisão por justa causa imputável ao CONTRATADO, este deverá restituir ao CONTRATANTE o valor proporcional às parcelas recebidas pelos serviços **não entregues**, sem prejuízo da multa rescisória.

---

## CLÁUSULA DÉCIMA SEGUNDA — DA RESPONSABILIDADE CIVIL

**12.1.** O CONTRATADO responde pelos **danos diretos** causados ao CONTRATANTE em decorrência de falha técnica comprovada na execução dos serviços, limitada ao valor total do contrato.

**12.2.** O CONTRATADO **não responde** por danos indiretos, lucros cessantes ou danos decorrentes de: (i) uso indevido do Sistema pelo CONTRATANTE ou por terceiros; (ii) falhas de infraestrutura de hospedagem não gerenciada pelo CONTRATADO; (iii) fornecimento de informações incorretas ou insuficientes pelo CONTRATANTE.

**12.3.** O CONTRATANTE é exclusivamente responsável pela veracidade, licitude e adequação dos dados inseridos no Sistema.

---

## CLÁUSULA DÉCIMA TERCEIRA — DA INEXISTÊNCIA DE VÍNCULO EMPREGATÍCIO

**13.1.** O CONTRATADO executa os serviços na qualidade de **profissional autônomo**, sem exclusividade, subordinação jurídica, pessoalidade obrigatória nem habitualidade configuradores de relação de emprego, nos termos do art. 593 do Código Civil e art. 2.º da CLT a contrario sensu.

**13.2.** O CONTRATADO é responsável pelo recolhimento de seus próprios tributos (IRPF, INSS autônomo e outros) incidentes sobre a remuneração auferida.

---

## CLÁUSULA DÉCIMA QUARTA — DAS DISPOSIÇÕES GERAIS

**14.1.** O presente contrato constitui o **acordo integral** entre as partes sobre o objeto aqui descrito e substitui quaisquer entendimentos anteriores, verbais ou escritos.

**14.2.** Qualquer modificação neste contrato somente terá validade se formalizada por **Termo Aditivo** escrito e assinado por ambas as partes.

**14.3.** A tolerância de uma parte em relação ao descumprimento de qualquer cláusula pela outra parte não implicará novação, renúncia ou alteração contratual.

**14.4.** Se qualquer cláusula deste contrato for considerada inválida ou inaplicável, as demais permanecerão em pleno vigor (**cláusula de severabilidade**).

**14.5.** As comunicações previstas neste contrato serão realizadas por escrito, preferencialmente por e-mail com confirmação de recebimento, nos endereços indicados no preâmbulo.

---

## CLÁUSULA DÉCIMA QUINTA — DO FORO E RESOLUÇÃO DE CONFLITOS

**15.1.** As partes elegem o **Foro da Comarca de Aparecida de Goiânia/GO** para dirimir quaisquer controvérsias oriundas deste contrato que não possam ser resolvidas por negociação direta, com renúncia expressa a qualquer outro, por mais privilegiado que seja.

**15.2.** Antes do recurso ao Poder Judiciário, as partes comprometem-se a buscar a solução da controvérsia por **mediação**, nos termos da Lei n.º 13.140/2015, no prazo de **30 (trinta) dias** contados da comunicação formal da controvérsia.

---

## ASSINATURAS

Por estarem justas e contratadas, as partes assinam o presente instrumento em **2 (duas) vias de igual teor e forma**, juntamente com as testemunhas abaixo.

**Goiânia/GO, ___ de _______________ de 2026.**

---

**CONTRATADO:**

```
_______________________________________________
[Nome completo]
CPF: ___.___.___-___
```

---

**CONTRATANTE:**

```
_______________________________________________
CPF/CNPJ: ___.___.___-___ / __.___.___/____-__
```

---

**TESTEMUNHAS:**

```
1. _______________________________________________
   Nome: ________________________________________
   CPF:  ___.___.___-___
   RG:   __________________________


2. _______________________________________________
   Nome: ________________________________________
   CPF:  ___.___.___-___
   RG:   __________________________
```

## ANEXO A — RESUMO FINANCEIRO

| Item | Valor |
|------|-------|
| Valor total do contrato | R$ 5.500,00 |
| Número de parcelas | 10 |
| Valor de cada parcela | R$ 550,00 |
| Bônus por conclusão em até 2 meses | + R$ 500,00 |
| Bônus por conclusão em até 5 meses | + R$ 200,00 |
| **Valor máximo com bônus** | **R$ 6.000,00** |
| **Valor mínimo (sem bônus)** | **R$ 5.500,00** |

> **Nota:** O bônus é pago uma única vez, referente ao prazo alcançado. As faixas são excludentes entre si.
