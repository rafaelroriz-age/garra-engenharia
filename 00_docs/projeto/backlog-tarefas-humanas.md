---
title: Backlog de Tarefas Humanas — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
related:
  - 00_docs/estudo-do-contexto.md
  - 00_docs/projeto/decisoes.md
  - 00_docs/projeto/status.md
  - 00_docs/projeto/backlog-tarefas.md
  - 00_docs/projeto/plano-gestao-configuracao.md
last_updated: 2026-07-20
---

# Backlog de Tarefas Humanas

> Este documento lista **apenas** tarefas que só uma pessoa pode executar — porque exigem autoridade de decisão/negócio, relação direta com o cliente, presença física, manuseio de credenciais/segredos ou um ato legal/regulatório. Não confundir com [backlog-tarefas.md](backlog-tarefas.md) (tarefas de engenharia executáveis por agente).
>
> **Critério de inclusão ("SÓ humano"):** a tarefa falha um destes testes → (1) exige assinatura, aprovação de orçamento ou negociação com o cliente; (2) exige presença física em campo; (3) exige credencial/segredo que não pode transitar por chat/agente (chave SSH, token de produção, senha); (4) é um gate de governança deliberadamente humano (segregação de funções); (5) é um ato jurídico/regulatório (assinatura digital, contrato).
>
> Quando a tarefa **pode** ser total ou parcialmente resolvida por um agente/MCP (mesmo que o passo final continue humano), a seção "Alternativa via agente/MCP" descreve a opção e o passo a passo equivalente. Manter este arquivo atualizado sempre que uma tarefa for concluída, uma nova ferramenta ficar disponível, ou um novo bloqueio humano surgir.
>
> **Legenda de status:** 🔴 Pendente | 🟡 Em andamento | ✅ Concluída

---

## Resumo

| ID | Tarefa | Motivo (só humano) | Bloqueia | Status | Tem alternativa agente/MCP? |
|---|---|---|---|---|---|
| [HT-01](#ht-01--validar-as-10-lacunas-a-esclarecer-com-o-cliente) | Validar as 10 lacunas `[A ESCLARECER]` com o cliente | Negociação/decisão de negócio com o cliente | BL-15, BL-18, B-01 | 🔴 Pendente | Parcial (preparar pauta e atualizar docs após resposta) |
| [HT-02](#ht-02--solicitar-e-receber-os-arquivos-docx-de-template-e-logo) | Solicitar e receber os `.docx` de template e logo em alta resolução | Comunicação externa + espera de entrega pelo cliente | BL-12 (fiel), BL-13, BL-17, BL-19, B-02 | 🔴 Pendente | Parcial (redigir a solicitação) |
| [HT-03](#ht-03--decidir-a-preferência-de-hospedagem) | Decidir a preferência de hospedagem (local vs. nuvem) | Decisão orçamentária | BL-20, BL-24, BL-28, B-03 | 🔴 Pendente | Parcial (pesquisa comparativa de opções) |
| [HT-04](#ht-04--provisionar-o-servidorvps-de-produção-e-registrar-domínio) | Provisionar servidor/VPS de produção e registrar domínio | Criação de conta, pagamento, registro de domínio | BL-24, BL-28 | 🔴 Pendente | Parcial (IaC/Bicep se Azure; configuração pós-provisionamento) |
| [HT-05](#ht-05--configurar-proteção-da-branch-main-no-github) | Configurar proteção da branch `main` no GitHub | Configuração administrativa sensível do repositório | BL-25/26 (item pendente) | 🔴 Pendente (ação manual restante) | Sim, via `gh` CLI (mesmo assim disparado pelo humano) |
| [HT-06](#ht-06--cadastrar-secrets-do-github-actions) | Cadastrar Secrets do GitHub Actions (SSH, `.env` de produção) | Segredos/credenciais nunca devem passar por chat/agente | BL-28 | 🔴 Pendente | Não recomendado — apenas humano |
| [HT-07](#ht-07--aprovar-manualmente-o-deploy-de-produção) | Aprovar manualmente o deploy de produção (GitHub Environment) | Gate de governança intencional (segregação de funções, DEC-14) | Deploys em produção (recorrente) | 🔴 Recorrente | Não — é por design |
| [HT-08](#ht-08--obter-certificado-digital-icp-brasil-se-necessário) | Obter certificado digital ICP-Brasil (se lacuna #9 confirmar necessidade) | Processo legal com autoridade certificadora, identidade do engenheiro | Módulo de assinatura digital (futuro) | 🔴 Condicional a HT-01 | Não para obtenção; integração técnica sim, depois de obtido |
| [HT-09](#ht-09--validar-visualmente-a-fidelidade-dos-relatórios-gerados) | Validar visualmente a fidelidade dos relatórios PDF/DOCX gerados vs. template original | Julgamento de qualidade/aprovação antes de ir a produção | BL-12, BL-13, BL-17 (sign-off) | 🔴 Pendente | Parcial (comparação visual assistida) |
| [HT-10](#ht-10--coleta-de-dados-e-fotos-em-campo-durante-a-vistoriainspeção) | Coleta de dados e fotos em campo durante a vistoria/inspeção | Atividade física de engenharia, fora do escopo de software | Alimenta BL-10/BL-11 (dados de entrada) | 🔴 Recorrente | Não |
| [HT-11](#ht-11--negociar-e-assinar-o-contrato-de-prestação-de-serviços) | Negociar e assinar o contrato de prestação de serviços/aditivos | Assinatura com validade jurídica | Formalização comercial | 🔴 Pendente | Parcial (minuta/revisão do contrato) |

---

## HT-01 — Validar as 10 lacunas `[A ESCLARECER]` com o cliente

**Por que só um humano:** exige agendar e conduzir uma conversa de negócio com o cliente (Eng. Roniel) para resolver ambiguidades que mudam a arquitetura (offline, multiusuário, assinatura digital etc.). Nenhum agente pode decidir por conta do cliente.

**Bloqueia:** B-01 (`status.md`), BL-15, BL-18 (`backlog-tarefas.md`).

**Passo a passo:**
1. Revisar a lista completa das 10 lacunas em [estudo-do-contexto.md §9](../estudo-do-contexto.md#9-lacunas-a-esclarecer).
2. Agendar reunião com o Eng. Roniel (ou responsável técnico do cliente) — canal a critério do gestor (e-mail, WhatsApp, chamada).
3. Conduzir a reunião cobrindo os 10 itens, com atenção prioritária a: offline (#3), multiusuário (#2), assinatura digital (#9) — citados como prioritários em [status.md](status.md#próximos-passos-em-ordem).
4. Documentar as respostas (ata ou anotações) e guardar em `00_docs/` (ex.: novo arquivo `ata-validacao-lacunas.md`).
5. Atualizar `estudo-do-contexto.md` removendo as tags `[A ESCLARECER]` e ajustando RN-04, RN-13, RNF-02, RNF-08 conforme as respostas.
6. Remover o bloqueio B-01 de [status.md](status.md#bloqueios-ativos) e desbloquear BL-15/BL-18 em `backlog-tarefas.md`.

**Alternativa via agente/MCP (parcial):**
- Um agente (ex.: modo "estudo-contexto" ou "Gestor de Projeto") pode **preparar a pauta/roteiro da reunião** e um rascunho de e-mail/mensagem convite, a partir de `estudo-do-contexto.md §9`.
- Depois que o humano obtiver as respostas do cliente (por texto/e-mail), o agente pode **aplicar as edições nos documentos** (`estudo-do-contexto.md`, `status.md`, `backlog-tarefas.md`) automaticamente — basta colar as respostas no chat e pedir a atualização.
- A decisão/negociação em si permanece 100% humana.

---

## HT-02 — Solicitar e receber os `.docx` de template e logo

**Por que só um humano:** é comunicação externa com o cliente e espera pela entrega de arquivos que só o cliente possui (RFO, LTIP, Vistoria Cautelar, RFIP, logo em alta resolução).

**Bloqueia:** B-02 (`status.md`), BL-12 (fidelidade completa), BL-13, BL-17, BL-19 (`backlog-tarefas.md`).

**Passo a passo:**
1. Listar os arquivos necessários: template `.docx` de RFO, LTIP, Vistoria Cautelar de Recebimento, Vistoria Residencial, RFIP, e logo em alta resolução (vetor/PNG transparente).
2. Enviar solicitação formal ao cliente (e-mail ou canal já usado no contrato).
3. Receber os arquivos e salvá-los localmente — **atenção:** por convenção do repositório, arquivos binários originais do cliente (`.docx`, `.pdf`, `.pbix`, `.xlsm`) não são versionados no Git (ver `.gitignore` e nota em memória de repositório); mantê-los em `01_output-context/` local (OneDrive) e não commitar.
4. Avisar o time técnico (ou pedir para um agente) para iniciar a conversão/uso como template real (desbloqueia BL-12/BL-13/BL-17/BL-19).
5. Remover o bloqueio B-02 de [status.md](status.md#bloqueios-ativos).

**Alternativa via agente/MCP (parcial):**
- Um agente pode **redigir o texto da solicitação** (e-mail/mensagem) listando exatamente os arquivos e formatos esperados.
- Depois de recebidos, o agente "conversor-documentos-md" pode gerar a versão `.md` de referência (como já feito para os documentos em `00_docs/convertidos/`), mas o **envio, recebimento e organização dos arquivos originais é sempre humano**.

---

## HT-03 — Decidir a preferência de hospedagem

**Por que só um humano:** é uma decisão orçamentária/estratégica (custo recorrente vs. hospedagem local), de responsabilidade do gestor do projeto.

**Bloqueia:** B-03 (`status.md`), BL-20, BL-24, BL-28 (`backlog-tarefas.md`).

**Passo a passo:**
1. Revisar as opções técnicas descritas em `12-devops.prompt.md` e na Seção 2 de [plano-gestao-configuracao.md](plano-gestao-configuracao.md#2-ambientes).
2. Comparar custo, manutenção e disponibilidade entre hospedagem local (na empresa) e nuvem (VPS/Cloud).
3. Registrar a decisão formal em `decisoes.md` (nova entrada `DEC-16` ou similar) e atualizar `backlog-tarefas.md`/`status.md` removendo B-03.

**Alternativa via agente/MCP (parcial):**
- Um agente de DevOps (modo "devops" ou subagente) pode **pesquisar e montar uma tabela comparativa** de provedores (custo, região, requisitos técnicos do Docker Compose) para embasar a decisão.
- Se a decisão recair sobre Azure, o agente "modernize-deployment" (skill de deployment) pode gerar automaticamente o IaC (Bicep/Terraform) e o plano de containerização depois que a escolha for confirmada.
- A escolha final (aprovar o gasto/local) continua humana.

---

## HT-04 — Provisionar o servidor/VPS de produção e registrar domínio

**Por que só um humano:** exige criar conta em um provedor, inserir dados de pagamento e registrar um domínio — ações financeiras/contratuais que um agente não deve (nem consegue) executar.

**Depende de:** HT-03 resolvido.

**Bloqueia:** BL-24, BL-28.

**Passo a passo:**
1. Após HT-03, escolher o provedor específico (ex.: VPS nacional, Azure, ou servidor físico próprio).
2. Criar a conta, configurar pagamento e provisionar a instância (SO Linux compatível com Docker).
3. Registrar/apontar o domínio (DNS) para o IP do servidor.
4. Gerar um usuário de deploy sem privilégio `root`/`sudo` interativo, conforme Seção 7 de [plano-gestao-configuracao.md](plano-gestao-configuracao.md#7-segurança-operacional-do-pipeline-e-do-host).
5. Repassar host/usuário (não a senha/chave em texto puro pelo chat) para configuração dos Secrets (ver HT-06).

**Alternativa via agente/MCP (parcial):**
- Se o provedor escolhido for **Azure**, o agente "modernize-deployment" ou a skill `microsoft-foundry`/Bicep pode gerar todo o IaC de provisionamento (rede, VM/Container Apps, regras de firewall) para o humano apenas revisar e aplicar (`az deployment` ou pipeline) — reduz o trabalho manual a aprovar/rodar o script.
- Após o servidor existir, um agente de DevOps pode ajudar a configurar Docker, nginx e firewall via terminal (SSH), desde que as credenciais de acesso sejam fornecidas fora do fluxo de chat (nunca coladas na conversa).
- Criação de conta, pagamento e registro de domínio continuam exclusivamente humanos.

---

## HT-05 — Configurar proteção da branch `main` no GitHub

**Por que só um humano:** é uma configuração administrativa do repositório (Settings → Branches) que a ferramenta MCP do GitHub disponível no momento não expõe (sem endpoint de "branch protection" no toolset atual).

**Referência:** Seção 1.4 de [plano-gestao-configuracao.md](plano-gestao-configuracao.md#14-proteção-da-branch-main), pendência registrada em BL-25/BL-26 de `backlog-tarefas.md`.

**Passo a passo (via UI do GitHub):**
1. Acessar `https://github.com/rafaelroriz-age/garra-engenharia/settings/branches`.
2. Adicionar regra de proteção para `main`.
3. Marcar: exigir Pull Request antes de merge; exigir o status check `ci.yml`; exigir branch atualizada antes do merge; bloquear force-push e deleção da branch; habilitar apenas squash merge.
4. Salvar e confirmar em `status.md`/memória de repositório que o item foi concluído.

**Alternativa via agente/MCP:**
- Não há tool MCP disponível hoje para isso, mas o **próprio humano** pode rodar via terminal usando a GitHub CLI (`gh`) já autenticada na máquina, por exemplo:
  ```powershell
  gh api -X PUT repos/rafaelroriz-age/garra-engenharia/branches/main/protection `
    -f required_status_checks[strict]=true `
    -f required_status_checks[contexts][]=ci.yml `
    -f enforce_admins=true `
    -f required_pull_request_reviews[required_approving_review_count]=0 `
    -f restrictions=null
  ```
- Um agente pode **gerar o comando exato** (como acima) para o humano copiar/colar e executar no próprio terminal autenticado — mas a execução deve ser feita pelo humano, pois envolve permissões administrativas do repositório.

---

## HT-06 — Cadastrar Secrets do GitHub Actions

**Por que só um humano:** envolve segredos reais (chave SSH privada, hosts de produção, conteúdo do `.env` de produção) que **nunca devem transitar por chat, agente ou modelo de IA**, conforme a política de segurança deste projeto.

**Referência:** Seção 3.4 de [plano-gestao-configuracao.md](plano-gestao-configuracao.md#34-secrets-necessários-github-actions--settings--secrets-and-variables).

**Passo a passo:**
1. Acessar `https://github.com/rafaelroriz-age/garra-engenharia/settings/secrets/actions`.
2. Cadastrar (via UI ou `gh secret set <NOME>` rodado pelo próprio humano no terminal): `SSH_HOST_STAGING`, `SSH_HOST_PROD`, `SSH_PRIVATE_KEY`, `REGISTRY_USERNAME` (se necessário; `GITHUB_TOKEN` já é automático), `PROD_ENV_FILE`.
3. Confirmar que nenhum desses valores foi colado em conversas com agentes/chat neste ou em outros repositórios.

**Alternativa via agente/MCP:** nenhuma recomendada. Um agente pode, no máximo, **listar quais secrets faltam** (checklist) mas nunca deve receber, gerar ou manusear os valores reais.

---

## HT-07 — Aprovar manualmente o deploy de produção

**Por que só um humano:** é um gate de governança **intencional** (segregação de funções) definido em DEC-14 — o workflow `cd-production.yml` exige um required reviewer no GitHub Environment `production` antes de aplicar qualquer tag `v*.*.*` em produção.

**Passo a passo (recorrente, a cada release):**
1. Após a tag `vX.Y.Z` disparar o workflow, acessar a aba **Actions** do GitHub.
2. Revisar o diff/checklist do PR mesclado e o resultado do `ci.yml`.
3. Aprovar (ou rejeitar) a execução do `cd-production.yml` na tela de "Review deployments".

**Alternativa via agente/MCP:** não se aplica — o próprio propósito do gate é impedir que uma automação aprove sozinha o próprio deploy.

---

## HT-08 — Obter certificado digital ICP-Brasil (se necessário)

**Por que só um humano:** é um processo legal com uma Autoridade Certificadora (compra de e-CPF/e-CNPJ, validação presencial ou por vídeo, identidade do engenheiro responsável) — nenhuma ferramenta de código resolve isso.

**Depende de:** resposta à lacuna #9 em HT-01 (o cliente/engenheiro usa assinatura digital ICP-Brasil ou apenas CREA impresso?).

**Passo a passo (se confirmado necessário):**
1. Contratar certificado digital e-CPF (A1 ou A3) junto a uma AC credenciada pela ICP-Brasil.
2. Realizar a validação de identidade exigida pela AC.
3. Instalar/exportar o certificado em formato utilizável pelo backend (ex.: `.pfx` protegido por senha).
4. Repassar ao time técnico apenas as informações necessárias para integração (nunca a senha do certificado por chat).

**Alternativa via agente/MCP:** a obtenção do certificado é 100% humana. Depois de obtido, um agente de backend pode implementar a integração técnica de assinatura (ex.: biblioteca de assinatura PDF/PKCS#7), mas isso é tarefa de código, não deste backlog.

---

## HT-09 — Validar visualmente a fidelidade dos relatórios gerados

**Por que só um humano:** é um julgamento de qualidade/aprovação de entregável ao cliente — comparar o PDF/DOCX gerado pelo sistema com o template original e decidir se está "fiel o suficiente" para ir a produção é uma responsabilidade do engenheiro, não uma métrica automatizável por completo.

**Bloqueia:** aprovação final de BL-12, BL-13, BL-17 antes de uso em produção.

**Passo a passo:**
1. Gerar um relatório de teste (RFO/LTIP) com dados de exemplo.
2. Abrir lado a lado com o `.docx`/PDF original do cliente.
3. Conferir: cabeçalho/rodapé por página, tabelas, quebras de página, fotos e legendas, tipografia.
4. Registrar aprovação (ou lista de ajustes) — pode ser um comentário no PR ou uma nota em `00_docs/projeto/status.md`.

**Alternativa via agente/MCP (parcial):**
- Um agente com ferramentas de navegador (ex.: captura de tela/`Playwright`) pode gerar **screenshots comparativos automáticos** entre o PDF gerado e uma referência, adiantando a revisão visual.
- O agente "prototipagem-documentacao-cliente" pode ajudar a apontar diferenças de layout durante o desenvolvimento dos templates HTML/CSS.
- A **aprovação final** ("está pronto para o cliente") continua sendo uma decisão humana.

---

## HT-10 — Coleta de dados e fotos em campo durante a vistoria/inspeção

**Por que só um humano:** é a atividade fim de engenharia (visitar a edificação, inspecionar sistemas prediais, tirar fotos, registrar medições) — está fora do escopo de qualquer ferramenta de software, é o próprio trabalho profissional que o sistema apenas documenta.

**Alimenta:** BL-10 (registro de visitas), BL-11 (upload de fotos).

**Passo a passo:**
1. Planejar a visita (edificação, contrato, sistemas a inspecionar).
2. Executar a inspeção física, registrando ocorrências e tirando fotos (via app PWA, quando BL-11 estiver pronta, ou meio atual).
3. Lançar os dados coletados no sistema (ou repassar para lançamento).

**Alternativa via agente/MCP:** nenhuma — é trabalho de campo. O sistema (BL-10/BL-11) apenas facilita o registro digital do que foi coletado presencialmente.

---

## HT-11 — Negociar e assinar o contrato de prestação de serviços

**Por que só um humano:** assinatura contratual tem validade jurídica e representa compromisso financeiro/legal entre as partes.

**Referência:** [contrato-prestacao-servicos-desenvolvimento.md](../contrato-prestacao-servicos-desenvolvimento.md), [proposta-comercial.md](../cliente/proposta-comercial.md).

**Passo a passo:**
1. Revisar a minuta atual do contrato/proposta comercial.
2. Negociar termos (escopo, prazo, valores, SLA) diretamente com o cliente.
3. Formalizar a assinatura (física ou eletrônica com validade jurídica, ex.: DocuSign/Clicksign — ferramenta de assinatura, não de IA generativa).
4. Arquivar o contrato assinado e atualizar `decisoes.md`/`status.md` se algo do escopo mudar.

**Alternativa via agente/MCP (parcial):**
- O agente "Especialista em Contratos Jurídicos" pode **revisar/redigir cláusulas**, identificar riscos e sugerir ajustes na minuta.
- A **negociação e a assinatura em si** permanecem exclusivamente humanas.

---

## Manutenção deste documento

- Atualizar o status de cada item assim que resolvido (mover para ✅ e anotar a data, como feito em `backlog-tarefas.md`).
- Ao destravar B-01/B-02/B-03, revisar se novas tarefas humanas surgem (ex.: HT-04 só começa depois de HT-03).
- Se uma nova ferramenta/MCP passar a cobrir parte de uma tarefa aqui listada (ex.: um tool de branch protection for adicionado ao GitHub MCP), mover a tarefa correspondente para `backlog-tarefas.md` ou marcar a alternativa como "automatizável" e ajustar o passo a passo.
