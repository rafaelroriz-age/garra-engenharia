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
  - 00_docs/projeto/backlog-kanban.md
last_updated: 2026-08-03
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
| [HT-03](#ht-03--decidir-a-preferência-de-hospedagem) | Decidir a preferência de hospedagem (local vs. nuvem) | Decisão orçamentária | BL-20, BL-24, BL-28, B-03 | ✅ Decidido (Render, 2026-07-21) | Sim (Blueprint `render.yaml` já pronto) |
| [HT-04](#ht-04--aplicar-o-blueprint-do-render-ou-provisionar-servidorvps-alternativo-e-registrar-domínio) | Aplicar o Blueprint do Render (conta + pagamento) e registrar domínio | Criação de conta, pagamento, conexão OAuth com GitHub | BL-24, BL-28 | 🟡 Em andamento (MCP executado em 2026-08-03) | Sim (provisionamento via MCP já feito; faltam ajustes finais) |
| [HT-05](#ht-05--configurar-proteção-das-branches-main_frontmain_backstaging_frontstaging_back-no-github) | Configurar proteção das 4 branches (`main_front`/`main_back`/`staging_front`/`staging_back`) no GitHub | Configuração administrativa sensível do repositório | BL-25/26 (item pendente), DEC-17 | 🔴 Pendente (ação manual restante) | Sim, via `gh` CLI (mesmo assim disparado pelo humano) |
| [HT-06](#ht-06--cadastrar-secrets-do-github-actions) | Cadastrar Secrets do GitHub Actions (SSH, `.env` de produção) | Segredos/credenciais nunca devem passar por chat/agente | BL-28 | 🔴 Pendente | Não recomendado — apenas humano |
| [HT-07](#ht-07--aprovar-manualmente-o-deploy-de-produção) | Aprovar manualmente o deploy de produção (GitHub Environment) | Gate de governança intencional (segregação de funções, DEC-14) | Deploys em produção (recorrente) | 🔴 Recorrente | Não — é por design |
| [HT-08](#ht-08--obter-certificado-digital-icp-brasil-se-necessário) | Obter certificado digital ICP-Brasil (se lacuna #9 confirmar necessidade) | Processo legal com autoridade certificadora, identidade do engenheiro | Módulo de assinatura digital (futuro) | 🔴 Condicional a HT-01 | Não para obtenção; integração técnica sim, depois de obtido |
| [HT-09](#ht-09--validar-visualmente-a-fidelidade-dos-relatórios-gerados) | Validar visualmente a fidelidade dos relatórios PDF/DOCX gerados vs. template original | Julgamento de qualidade/aprovação antes de ir a produção | BL-12, BL-13, BL-17 (sign-off) | 🔴 Pendente | Parcial (comparação visual assistida) |
| [HT-10](#ht-10--coleta-de-dados-e-fotos-em-campo-durante-a-vistoriainspeção) | Coleta de dados e fotos em campo durante a vistoria/inspeção | Atividade física de engenharia, fora do escopo de software | Alimenta BL-10/BL-11 (dados de entrada) | 🔴 Recorrente | Não |
| [HT-11](#ht-11--negociar-e-assinar-o-contrato-de-prestação-de-serviços) | Negociar e assinar o contrato de prestação de serviços/aditivos | Assinatura com validade jurídica | Formalização comercial | 🔴 Pendente | Parcial (minuta/revisão do contrato) |
| [HT-12](#ht-12--autenticar-o-servidor-mcp-do-notion) | Autenticar o servidor MCP do Notion (OAuth) e selecionar o workspace/página de destino | Login/OAuth e escolha de workspace são atos do próprio usuário; credencial não deve passar por chat/agente | Criação do board `backlog-kanban.md` real dentro do Notion (DEC-20) | 🔴 Pendente | Sim (após autenticado, o agente cria/atualiza o board automaticamente) |

---

## HT-01 — Validar as 10 lacunas `[A ESCLARECER]` com o cliente

**Por que só um humano:** exige agendar e conduzir uma conversa de negócio com o cliente (Eng. Roniel) para resolver ambiguidades que mudam a arquitetura (offline, multiusuário, assinatura digital etc.). Nenhum agente pode decidir por conta do cliente.

**Bloqueia:** B-01 (`status.md`), BL-15, BL-18 (`backlog-tarefas.md`).

**Estado atual (2026-07-29):** a lacuna #13 foi esclarecida parcialmente pelo prompt do cliente em [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md); as lacunas #6, #11 e #12 já foram tratadas/definidas via DEC-18 em [00_docs/projeto/decisoes.md](decisoes.md). As lacunas remanescentes (#1, #2, #3, #4, #5, #7, #8, #9, #10) ainda precisam de confirmação formal, inclusive a decisão de provedor de IA e política de retenção/privacidade para o fluxo de legendas assistidas por IA.

**Passo a passo:**
1. Revisar a lista completa das 10 lacunas em [estudo-do-contexto.md §9](../estudo-do-contexto.md#9-lacunas-a-esclarecer).
2. Agendar reunião com o Eng. Roniel (ou responsável técnico do cliente) — canal a critério do gestor (e-mail, WhatsApp, chamada).
3. Conduzir a reunião cobrindo os 10 itens, com atenção prioritária a: offline (#3), multiusuário (#2), assinatura digital (#9) — citados como prioritários em [status.md](status.md#próximos-passos-em-ordem).
4. Documentar as respostas (ata ou anotações) e guardar em `00_docs/` (ex.: novo arquivo `ata-validacao-lacunas.md`).
5. Atualizar `estudo-do-contexto.md` marcando as lacunas já esclarecidas (#6, #11, #12) e a lacuna #13 como parcialmente resolvida, mantendo as demais como pendentes e ajustando RN-04, RN-13, RNF-02, RNF-08 conforme as respostas.
6. Atualizar o status de B-01 para "parcialmente resolvido" em [status.md](status.md#bloqueios-ativos) e ajustar BL-15/BL-18 em `backlog-tarefas.md` para refletir o que ficou esclarecido e o que ainda precisa confirmação.

**Alternativa via agente/MCP (parcial):**
- Um agente (ex.: modo "estudo-contexto" ou "Gestor de Projeto") pode **preparar a pauta/roteiro da reunião** e um rascunho de e-mail/mensagem convite, a partir de `estudo-do-contexto.md §9`.
- Depois que o humano obtiver as respostas do cliente (por texto/e-mail), o agente pode **aplicar as edições nos documentos** (`estudo-do-contexto.md`, `status.md`, `backlog-tarefas.md`) automaticamente — basta colar as respostas no chat e pedir a atualização.
- A decisão/negociação em si permanece 100% humana.

---

## HT-02 — Solicitar e receber os `.docx` de template e logo

**Por que só um humano:** é comunicação externa com o cliente e espera pela entrega de arquivos que só o cliente possui (RFO, LTIP, Vistoria Cautelar, RFIP, logo em alta resolução).

**Bloqueia:** B-02 (`status.md`), BL-12 (fidelidade completa), BL-13, BL-17, BL-19 (`backlog-tarefas.md`).

**Templates `.docx` exigidos (lista explícita, ver também [status.md § Bloqueios Ativos](status.md#bloqueios-ativos)):**
1. RFO — Relatório de Fiscalização de Obra (referência convertida: `Relatorio_de_Fiscalizacao_1.md`/`Relatorio_de_Fiscalizacao.md`).
2. LTIP — Laudo Técnico de Inspeção Predial (referência convertida: `Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md`).
3. Laudo Técnico de Vistoria Cautelar de Recebimento (referência convertida: `Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md`).
4. Vistoria de Imóvel Residencial (referência convertida: `Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md`).
5. RFIP — Relatório Fotográfico de Inspeção Predial (referência convertida: `Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md`).
6. Logo da Garra Engenharia em alta resolução (vetor `.svg`/`.ai` ou `.png` transparente), exigido por RN-07 no cabeçalho de todos os itens acima.

**Passo a passo:**
1. Confirmar a lista acima com o cliente antes de enviar (os `.md` já convertidos em `00_docs/convertidos/` são só referência aproximada, não substituem o `.docx`/`.xlsm` original fiel).
2. Enviar solicitação formal ao cliente (e-mail ou canal já usado no contrato).
3. Receber os arquivos e salvá-los localmente — **atenção:** por convenção do repositório, arquivos binários originais do cliente (`.docx`, `.pdf`, `.pbix`, `.xlsm`) não são versionados no Git (ver `.gitignore` e nota em memória de repositório); mantê-los em `01_output-context/` local (OneDrive) e não commitar.
4. Avisar o time técnico (ou pedir para um agente) para iniciar a conversão/uso como template real (desbloqueia BL-12/BL-13/BL-17/BL-19).
5. Remover o bloqueio B-02 de [status.md](status.md#bloqueios-ativos).

**Alternativa via agente/MCP (parcial):**
- Um agente pode **redigir o texto da solicitação** (e-mail/mensagem) listando exatamente os arquivos e formatos esperados.
- Depois de recebidos, o agente "conversor-documentos-md" pode gerar a versão `.md` de referência (como já feito para os documentos em `00_docs/convertidos/`), mas o **envio, recebimento e organização dos arquivos originais é sempre humano**.

---

## HT-03 — Decidir a preferência de hospedagem

**Status (2026-07-21): ✅ Decidido — Render (nuvem).** O usuário optou por hospedar em [Render](https://render.com/) e pediu para subir os 3 serviços (frontend, backend, banco). O agente de DevOps já preparou todo o IaC (`../render.yaml`, `04_backend/Dockerfile.render`, `03_frontend/Dockerfile.render`, `05_infra/.env.render.example`, seção "Deploy em produção (Render)" em `05_infra/README.md`) — falta só a ação humana da HT-04 abaixo (que ficou bem mais simples do que provisionar um VPS).

**Por que só um humano:** é uma decisão orçamentária/estratégica (custo recorrente vs. hospedagem local), de responsabilidade do gestor do projeto.

**Bloqueava:** B-03 (`status.md`), BL-20, BL-24, BL-28 (`backlog-tarefas.md`) — desbloqueados a partir de agora (dependiam só da escolha da plataforma).

**Alternativa via agente/MCP (parcial) — já executada:**
- O agente de DevOps gerou o Blueprint (`render.yaml`) com os 3 recursos definidos como código, prontos para aplicar no Dashboard do Render.
- Existe um servidor MCP do Render já configurado em `.vscode/mcp.json`, mas **não conectado** nesta sessão (precisa que o usuário inicie o servidor pela paleta de comandos do VS Code e cole a própria API key quando solicitado — nunca pelo chat). Uma vez conectado, o agente pode aplicar o Blueprint e devolver os links reais automaticamente, sem precisar do passo manual no Dashboard.

---

## HT-04 — Aplicar o Blueprint do Render (ou provisionar servidor/VPS alternativo) e registrar domínio

**Por que só um humano:** exige uma conta no provedor de nuvem (Render), autorização de pagamento dos planos pagos (`starter`/`basic-256mb` — sem tier perpétuo gratuito) e a conexão OAuth com o GitHub — ações financeiras/contratuais que um agente não deve (nem consegue) executar sem credenciais do usuário.

**Depende de:** HT-03 resolvido (✅ Render escolhido).

**Bloqueia:** BL-24, BL-28.

**Estado atual (2026-08-03):** provisionamento de produção executado via MCP do Render: banco `garra-db` e serviços `garra-backend`/`garra-frontend` criados com deploy inicial disparado. Para manter segurança, os segredos do backend foram deixados vazios para preenchimento manual no painel. Ainda resta confirmar a organização no project/grupo `garraengenharia` no Dashboard e preencher variáveis sensíveis antes da validação final.

**Passo a passo (caminho simplificado — Render, ver `05_infra/README.md` § "Deploy em produção (Render)"):**
1. Criar/acessar conta em [dashboard.render.com](https://dashboard.render.com/) e conectar o repositório GitHub `rafaelroriz-age/garra-engenharia`.
2. New → Blueprint → selecionar o repositório — o Render lê `render.yaml` automaticamente e mostra o preview dos 3 recursos.
3. Clicar em **Apply** (confirmar os planos pagos). O Render provisiona `garra-db`, builda e sobe `garra-backend` e `garra-frontend`, já rodando `alembic upgrade head` antes do deploy do backend.
4. Copiar as URLs reais (`Settings → URL` de cada serviço) e, se diferirem do previsto em `render.yaml`, ajustar `NEXT_PUBLIC_API_URL`/`BACKEND_CORS_ORIGINS` manualmente (ver checklist em `05_infra/.env.render.example`).
5. (Opcional, domínio próprio) Settings → Custom Domains → apontar o DNS do domínio do cliente para o serviço `garra-frontend`.

**Alternativa via agente/MCP:**
- Se o usuário iniciar o servidor MCP do Render (já em `.vscode/mcp.json`) e inserir a própria API key quando o VS Code solicitar, o agente pode aplicar o Blueprint e ler os links de volta diretamente, sem precisar repetir os passos 1-4 manualmente no Dashboard.
- Criação de conta, aprovação de custo e registro de domínio continuam exclusivamente humanos.
- Caminho alternativo (VPS/Azure) permanece documentado no histórico deste arquivo caso a decisão de hospedagem mude no futuro.

**Checklist final pendente (pós-MCP):**
1. Abrir o serviço `garra-backend` no Render e preencher os segredos em branco: `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET_KEY`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_HOST`.
2. Confirmar `NEXT_PUBLIC_API_URL` no `garra-frontend` e `BACKEND_CORS_ORIGINS` no `garra-backend` com as URLs reais dos serviços.
3. Garantir que os recursos estejam no project/grupo `garraengenharia` dentro do workspace da conta.
4. Rodar novo deploy manual e validar `GET /health` do backend.

---

## HT-12 — Autenticar o servidor MCP do Notion

**Por que só um humano:** o login OAuth no Notion (escolha da conta/workspace de destino e concessão de escopo de acesso) é um ato de autenticação pessoal que não pode passar por chat/agente — mesmo princípio já aplicado ao Render (HT-04) e descrito nas restrições deste modo (nenhuma chave/token de provedor é solicitada, digitada ou lida via chat).

**Bloqueia:** criação/atualização real do board `00_docs/projeto/backlog-kanban.md` dentro do Notion (DEC-20, ADR-11 em `arquitetura.md`).

**Passo a passo:**
1. Abrir a paleta de comandos do VS Code (`Ctrl+Shift+P`) → `MCP: List Servers` → selecionar `notion` → `Start Server`.
2. Concluir o login OAuth no navegador que abrir automaticamente, escolhendo o workspace/página do Notion onde o board de backlog deve ser criado.
3. Confirmar no chat que a autenticação foi concluída — a partir daí o agente cria o banco de dados "Backlog — Garra Engenharia" com as colunas Backlog/To do/In progress/Done e os cartões descritos em `00_docs/projeto/backlog-kanban.md`.

**Alternativa via agente/MCP:**
- Depois de autenticado, todo o trabalho de criação/atualização do board é feito pelo agente — não é necessário criar manualmente bases de dados ou cartões no Notion.
- Sem a autenticação, o agente só consegue preparar o conteúdo localmente (já feito em `00_docs/projeto/backlog-kanban.md`), sem conseguir publicá-lo no Notion.

---

## HT-05 — Configurar proteção das branches `main_front`/`main_back`/`staging_front`/`staging_back` no GitHub

**Por que só um humano:** é uma configuração administrativa do repositório (Settings → Branches) que a ferramenta MCP do GitHub disponível no momento não expõe (sem endpoint de "branch protection" no toolset atual).

**Referência:** Seção 1.4 de [plano-gestao-configuracao.md](plano-gestao-configuracao.md#14-proteção-das-branches-main_frontmain_backstaging_frontstaging_back-dec-17), DEC-17 em [decisoes.md](decisoes.md#dec-17--branching-por-serviço-no-monorepo-main_frontmain_backstaging_frontstaging_back), pendência registrada em BL-25/BL-26 de `backlog-tarefas.md`.

**Passo a passo (via UI do GitHub):**
1. Acessar `https://github.com/rafaelroriz-age/garra-engenharia/settings/branches`.
2. Adicionar uma regra de proteção para CADA uma das 4 branches: `main_front`, `main_back`, `staging_front`, `staging_back` (repetir os passos 3-4 abaixo por branch).
3. Marcar: exigir Pull Request antes de merge; exigir o status check `ci.yml`; exigir branch atualizada antes do merge; bloquear force-push e deleção da branch; habilitar apenas squash merge.
4. Salvar e confirmar em `status.md`/memória de repositório que o item foi concluído.

**Alternativa via agente/MCP:**
- Não há tool MCP disponível hoje para isso, mas o **próprio humano** pode rodar via terminal usando a GitHub CLI (`gh`) já autenticada na máquina, por exemplo (repetir para cada uma das 4 branches, trocando `main_back` pelo nome correspondente):
  ```powershell
  foreach ($branch in @("main_front", "main_back", "staging_front", "staging_back")) {
    gh api -X PUT "repos/rafaelroriz-age/garra-engenharia/branches/$branch/protection" `
      -f required_status_checks[strict]=true `
      -f required_status_checks[contexts][]=ci.yml `
      -f enforce_admins=true `
      -f required_pull_request_reviews[required_approving_review_count]=0 `
      -f restrictions=null
  }
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
