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
  - 00_docs/projeto/pauta-validacao-lacunas.md
  - 00_docs/cliente/solicitacao-templates-docx.md
last_updated: 2026-09-17
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
| [HT-01](#ht-01--validar-as-10-lacunas-a-esclarecer-com-o-cliente) | Validar as lacunas `[A ESCLARECER]` com o cliente | Negociação/decisão de negócio com o cliente | BL-15, BL-18, B-01 | ✅ **Concluída (2026-09-17)** — Bloco 1 respondido em 2026-09-10 (#2, #3, #9 → DEC-26/27/28) e Blocos 2 e 3 encerrados em 2026-09-17 (#1, #4, #5, #7, #8, #10 → DEC-29). **B-01 encerrado**, BL-15 e BL-18 destravadas. Resta só o Bloco 4 (provedor de IA), tratado como B-04 | Parcial (pauta redigida pelo agente; docs atualizados após a decisão) |
| [HT-02](#ht-02--confirmar-versão-vigente-dos-originais) | Confirmar que os originais em `01_output-context/` são a versão vigente | Comunicação externa com o cliente | Nada — item de gestão | 🟡 Reduzida em 2026-09-17 (DEC-30/ADR-16) — a marca vetorial deixou de ser pendência: foi derivada do próprio JPEG oficial por script. **B-02 encerrado** | Sim (agente derivou templates e marca dos arquivos já disponíveis) |
| [HT-03](#ht-03--decidir-a-preferência-de-hospedagem) | Decidir a preferência de hospedagem (local vs. nuvem) | Decisão orçamentária | BL-20, BL-24, BL-28, B-03 | ✅ Decidido (Render, 2026-07-21) | Sim (Blueprint `render.yaml` já pronto) |
| [HT-04](#ht-04--aplicar-o-blueprint-do-render-ou-provisionar-servidorvps-alternativo-e-registrar-domínio) | Aplicar o Blueprint do Render (conta + pagamento) e registrar domínio | Criação de conta, pagamento, conexão OAuth com GitHub | BL-24, BL-28 | 🟡 Em andamento — env vars não-secretas aplicadas via MCP em 2026-08-07; restam **apenas 2 segredos** (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`) + Pre-Deploy Command + Health Check Path | Sim, parcialmente (MCP não expõe senha do banco nem edição de Settings do serviço) |
| [HT-05](#ht-05--configurar-proteção-das-branches-mainmain_frontmain_back-no-github) | Configurar proteção das 3 branches (`main`/`main_front`/`main_back`) no GitHub | Configuração administrativa sensível do repositório | BL-25/26 (item pendente), DEC-17/DEC-22 | 🔴 Pendente — `gh` CLI **não autenticado** na máquina (verificado em 2026-08-07); MCP do GitHub não expõe branch protection | Sim, via `gh` CLI após `gh auth login` (comando pronto abaixo) |
| [HT-06](#ht-06--cadastrar-secrets-do-github-actions) | Cadastrar Secrets do GitHub Actions (SSH, `.env` de produção) | Segredos/credenciais nunca devem passar por chat/agente | BL-28 | 🔴 Pendente | Não recomendado — apenas humano |
| [HT-07](#ht-07--aprovar-manualmente-o-deploy-de-produção) | Aprovar manualmente o deploy de produção (GitHub Environment) | Gate de governança intencional (segregação de funções, DEC-14) | Deploys em produção (recorrente) | 🔴 Recorrente | Não — é por design |
| [HT-08](#ht-08--obter-certificado-digital-icp-brasil-se-necessário) | Obter certificado digital ICP-Brasil | Processo legal com autoridade certificadora, identidade do engenheiro | Módulo de assinatura digital (futuro) | ⚪ Sem efeito para a v1.0 (2026-09-10) — lacuna #9 respondida: basta CREA/ART impressos (DEC-28) | Não para obtenção; integração técnica sim, depois de obtido |
| [HT-09](#ht-09--validar-visualmente-a-fidelidade-dos-relatórios-gerados) | Validar visualmente a fidelidade dos relatórios PDF/DOCX gerados vs. template original | Julgamento de qualidade/aprovação antes de ir a produção | BL-12, BL-13, BL-17 (sign-off) | 🟡 **Pronta para conferência (amostra regerada em 2026-09-17, já com a marca vetorizada)** em `01_output-context/_amostras_ht09/` | Parcial (agente gera a amostra; o parecer é humano) |
| [HT-10](#ht-10--coleta-de-dados-e-fotos-em-campo-durante-a-vistoriainspeção) | Coleta de dados e fotos em campo durante a vistoria/inspeção | Atividade física de engenharia, fora do escopo de software | Alimenta BL-10/BL-11 (dados de entrada) | 🔴 Recorrente | Não |
| [HT-11](#ht-11--negociar-e-assinar-o-contrato-de-prestação-de-serviços) | Negociar e assinar o contrato de prestação de serviços/aditivos | Assinatura com validade jurídica | Formalização comercial | 🔴 Pendente | Parcial (minuta/revisão do contrato) |
| [HT-12](#ht-12--autenticar-o-servidor-mcp-do-notion) | Autenticar o servidor MCP do Notion (OAuth) e selecionar o workspace/página de destino | Login/OAuth e escolha de workspace são atos do próprio usuário; credencial não deve passar por chat/agente | Criação do board `backlog-kanban.md` real dentro do Notion (DEC-20) | ✅ Concluída (2026-08-07) — board criado, ver [HT-12](#ht-12--autenticar-o-servidor-mcp-do-notion) | Sim (board criado integralmente pelo agente após a autenticação) |

---

## Bloqueios do projeto (B-01 a B-04)

> Esses IDs não são classes, enums, constantes de código ou variáveis da aplicação. Eles representam **bloqueios de gestão/projeto** usados para sinalizar pendências que exigem decisão ou ação humana. A definição formal fica em [status.md](status.md#bloqueios-ativos) e em [backlog-tarefas.md](backlog-tarefas.md).

| ID | Nome | Descrição | Tarefa humana associada |
|---|---|---|---|
| ~~B-01~~ | ~~Lacunas de requisitos pendentes~~ — **ENCERRADO em 2026-09-17** | Todas as lacunas `[A ESCLARECER]` de requisito foram fechadas: #2/#3/#9 pelo cliente em 2026-09-10 (DEC-26/27/28), #6/#11/#12 por DEC-18 e as seis restantes (#1, #4, #5, #7, #8, #10) por [DEC-29](decisoes.md#dec-29--fechamento-das-lacunas-remanescentes-blocos-2-e-3-encerramento-do-bloqueio-b-01). Nenhuma tarefa do backlog segue bloqueada por lacuna | HT-01 (✅) |
| ~~B-02~~ | ~~Fidelidade de template~~ — **ENCERRADO em 2026-09-17** | Os originais `.xlsx`/`.xlsm`/PDF dos 5 modelos já eram a base dos templates desde DEC-25/ADR-13, e a última pendência — a marca vetorial/transparente (RN-07) — foi resolvida internamente por [DEC-30](decisoes.md#dec-30--marca-vetorizada-internamente-a-partir-do-jpeg-oficial-encerramento-do-bloqueio-b-02): a logo foi vetorizada do próprio JPEG oficial por script determinístico | HT-02 (reduzida) |
| ~~B-03~~ | ~~Preferência de hospedagem~~ — **DECIDIDO em 2026-07-21 (Render)** | Decisão de plataforma **já tomada**: Render escolhido. Segue pendente apenas a execução operacional do deploy/ajustes em HT-04 | HT-03 (✅) e HT-04 (em andamento) |
| B-04 | Provedor de IA/LLM não definido | Decide a política de privacidade/retensão e o provedor para legendas assistidas por IA | Decisão de negócio / não há HT dedicada ainda. **2026-11-11:** DEC-49 (proposta) adota a DeepSeek Platform API em modo só texto; falta aprovar e definir a política de retenção do provedor |

**Observação:** o sufixo `B` significa “Bloqueio”. Já o sufixo `HT` significa “Tarefa Humana”. Em outras palavras, as tarefas humanas resolvem ou destravam os bloqueios de projeto.

---

## HT-01 — Validar as 10 lacunas `[A ESCLARECER]` com o cliente — ✅ CONCLUÍDA (2026-09-17)

**Por que só um humano:** exigia agendar e conduzir uma conversa de negócio com o cliente (Eng. Roniel) para resolver ambiguidades que mudam a arquitetura (offline, multiusuário, assinatura digital etc.). Nenhum agente pode decidir por conta do cliente.

**Bloqueava:** B-01 (`status.md`), BL-15, BL-18 (`backlog-tarefas.md`) — **todos destravados**.

**Desfecho:**
- **2026-09-10 — Bloco 1 respondido pelo cliente:** #3 (sem necessidade de operação offline → DEC-26), #2 (há auxiliares de campo → perfil `auxiliar`, DEC-27, gerou BL-42, já implementada) e #9 (sem ICP-Brasil, apenas CREA/ART impressos → DEC-28).
- **2026-09-17 — Blocos 2 e 3 encerrados pelo gestor ([DEC-29](decisoes.md#dec-29--fechamento-das-lacunas-remanescentes-blocos-2-e-3-encerramento-do-bloqueio-b-01)):** #10 prioridade sugerida **e editável** com registro do ajuste ("Prioridade 0" = não aplicável) → **desbloqueia BL-15**; #1 sem periodicidade obrigatória de re-inspeção; #8 unidade de medição livre por item; #5 DOCX obrigatório; #4 fotos por clipboard/upload manual, sem monitoramento de pasta; #7 sem integração com o CREA. Em cada caso foi adotada a posição de **menor impacto sobre o que já está entregue** — nenhuma exige refazer código existente, e todas podem ser revistas pelo cliente a baixo custo.
- Antes disso, #13 já havia sido parcialmente esclarecida pelo prompt do cliente em [00_docs/cliente/prompt-lado-cliente.md](../cliente/prompt-lado-cliente.md) e #6/#11/#12 tratadas via DEC-18.

Registro completo em [ata-validacao-lacunas.md](ata-validacao-lacunas.md).

**Resta apenas** (fora de B-01, não é lacuna de requisito): a escolha do **provedor de IA/LLM** e da política de retenção de dados — Bloco 4 da pauta, rastreado como **B-04**; e o **destino externo do backup** (RNF-08), escolha operacional que não bloqueia nenhuma tarefa.

**Alternativa via agente/MCP (parcial) — executada:**
- A **pauta completa da reunião** está em [pauta-validacao-lacunas.md](pauta-validacao-lacunas.md), com as lacunas organizadas em 4 blocos por impacto arquitetural, cada uma com a pergunta, o motivo técnico e as opções de resposta.
- O agente aplicou as edições decorrentes nos documentos (`estudo-do-contexto.md`, `decisoes.md`, `status.md`, `backlog-tarefas.md`, `ata-validacao-lacunas.md`, `riscos.md`, `escopo.md`, `arquitetura.md`).
- A decisão/negociação em si permaneceu 100% humana.

---

## HT-02 — Confirmar versão vigente dos originais

> **Reescrita em 2026-09-17 (DEC-30/ADR-16).** A versão anterior também pedia ao cliente a **logo vetorial/transparente** — último item de B-02. Esse pedido foi eliminado: a marca foi vetorizada internamente a partir do próprio JPEG oficial por script determinístico (`python -m app.scripts.build_brand_assets`), com fundo transparente, e já está no cabeçalho do PDF e do DOCX. **B-02 encerrado.** Antes disso, a reescrita de 2026-08-12 (DEC-25/ADR-13) já havia eliminado o pedido dos `.docx` (o cliente não produz esses documentos em Word).

**Por que só um humano:** é comunicação externa com o cliente — confirmar qual versão dos arquivos está vigente.

**Bloqueia:** nada. BL-12, BL-13 e BL-17 foram desbloqueadas por DEC-25/ADR-13 e a marca deixou de ser pendência por DEC-30/ADR-16. Se o cliente vier a enviar um `.svg`/`.ai` oficial, ele é insumo **opcional** de refinamento — basta substituir os arquivos em `04_backend/templates/assets/`.

**Originais já disponíveis em `01_output-context/`** (não precisam ser solicitados):

| # | Documento | Arquivo original | Formato |
|---|---|---|---|
| 1 | RFO — Relatório de Fiscalização de Obra | `RFO INSPEÇÃO .xlsx` (77,9 MB), `Relatório de Fiscalização 1.xlsm` (17,5 MB) | Planilha |
| 2 | LTIP — Laudo Técnico de Inspeção Predial | `Laudo Técnico de Inspeção Predial 2026 - Cond. Cortina D'Ampezzo.pdf` (32,5 MB) | PDF final |
| 3 | Vistoria Cautelar de Recebimento | `Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf` (38,5 MB) | PDF final |
| 4 | Vistoria de Imóvel Residencial | `Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf` (21,5 MB) | PDF final |
| 5 | RFIP — Relatório Fotográfico de Inspeção Predial | `Relatório Fotográfico de Inspeção Predial - CORTINA D'AMPAREZZO - Versão Final.xlsx` (479,3 MB) | Planilha |

**Passo a passo (o que ainda precisa ser feito):**
1. Confirmar com o cliente que os 5 arquivos acima são a **versão vigente** dos modelos — se houver revisão mais recente, pedir a atualização do arquivo (mesmo formato, não `.docx`).
2. Confirmar também que as 4 variantes JPEG da marca recebidas em 2026-08-11 (`03_frontend/public/brand/logos/`) são as vigentes — são a origem do vetor gerado em DEC-30. Se o cliente tiver o `.svg`/`.ai` original, receber é bom, mas **não é mais necessário**.
3. Perguntar, sem bloquear a v1.0, se o fluxo de trabalho seguirá em Excel — se sim, avaliar a exportação `.xlsx` como formato adicional de saída na v1.1 (ponto aberto registrado em DEC-25).
4. Manter os originais **fora do Git** (`.gitignore` já bloqueia `.xlsx`/`.xlsm`/`.pdf`/`.docx`/`.pbix` em `01_output-context/`) — apenas o `layout.json` e os templates gerados são versionados.

**Alternativa via agente/MCP:**
- A derivação dos templates (`openpyxl` para as planilhas, `pypdf`/`pdfplumber` para os PDFs → `layout.json` → `.html.j2` + `.docx`) é 100% executável por agente a partir dos arquivos já presentes — foi o escopo de BL-12/BL-13/BL-17, todas concluídas.
- A vetorização da marca também foi feita por agente (DEC-30): `python -m app.scripts.build_brand_assets`.
- ⚠️ A minuta antiga em [solicitacao-templates-docx.md](../cliente/solicitacao-templates-docx.md) está **obsoleta**: pedir `.docx` que o cliente não possui gera retrabalho e ruído. Reescrever antes de enviar, cobrindo apenas os itens 1 a 3 acima.

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

**Estado atual (2026-08-07, após execução via MCP do Render):** `garra-backend`/`garra-frontend` estão **live** e em dia com o código de `main_back`/`main_front` (auto-deploy funcionando, DEC-22). Nesta data o agente aplicou via MCP todas as variáveis de ambiente **não secretas** que faltavam no `garra-backend` (`ENVIRONMENT=production`, `BACKEND_CORS_ORIGINS=https://garra-frontend.onrender.com`, `POSTGRES_HOST=dpg-d9obbtfqj5pc738dqf2g-a`, `POSTGRES_PORT=5432`, `POSTGRES_USER=garra_db_user`, `POSTGRES_DB=garra_db`, `JWT_ALGORITHM=HS256`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60`) e confirmou `NEXT_PUBLIC_API_URL=https://garra-backend.onrender.com/api/v1` no `garra-frontend`. O deploy resultante subiu com status `live`, mas `GET https://garra-backend.onrender.com/health` continua respondendo `{"status":"degraded","database":"unavailable"}` — causa restante é exclusivamente a ausência de `POSTGRES_PASSWORD` (o `Settings` do backend usa string vazia como default, ver [04_backend/app/core/config.py](../../04_backend/app/core/config.py)).

**Por que o agente não consegue fechar sozinho:** (1) o MCP do Render **não expõe a senha do Postgres** em nenhuma ferramenta (`get_postgres` retorna só metadados; `query_render_postgres` roda em transação read-only, então também não permite criar um usuário novo); (2) `JWT_SECRET_KEY` é segredo e não deve transitar pelo chat/modelo; (3) o MCP não tem ferramenta de `update_service`, então **Pre-Deploy Command** e **Health Check Path** só podem ser definidos no Dashboard. Vale lembrar que os 2 serviços foram criados via MCP como **runtime nativo** (`env: python`/`env: node`), não como `runtime: docker` a partir de `Dockerfile.render` — ou seja, o Blueprint nunca foi de fato aplicado, e por isso `preDeployCommand`/`healthCheckPath` do `render.yaml` não valem para eles.

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

**Checklist final pendente (atualizado em 2026-08-07 — só restam itens que exigem o Dashboard):**

1. **[CRÍTICO — único bloqueio do `/health`]** `garra-backend` → Environment → adicionar **`POSTGRES_PASSWORD`**. Prefira o botão **"Add from Database"** apontando para `garra-db` (cria o vínculo sem expor a senha); se ele adicionar as demais `POSTGRES_*` em duplicidade, remova as que o agente já gravou (`POSTGRES_HOST`/`PORT`/`USER`/`DB`) e mantenha as vinculadas ao banco.
2. **[CRÍTICO — segurança]** Adicionar **`JWT_SECRET_KEY`** com um valor aleatório forte. Desde **DEC-24/BL-23 (2026-08-07)**, com `ENVIRONMENT=production` o backend **falha no boot** se essa variável estiver vazia, for `"changeme"` ou tiver menos de 32 caracteres — e também se `BACKEND_CORS_ORIGINS` contiver `*`. É fail-closed proposital (OWASP A05): melhor não subir do que subir com tokens forjáveis. Gere localmente e cole direto no Dashboard (nunca no chat):
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
2.1. **[NOVO — DEC-24]** Depois do primeiro deploy saudável, criar o auditor de bootstrap pelo Shell do Render (`cd 04_backend && python -m app.scripts.seed_admin`, com `ADMIN_EMAIL`/`ADMIN_SENHA` definidos): `POST /auth/register` deixou de ser público e só um auditor autenticado pode cadastrar novos usuários (inclusive os do Portal do Cliente).
3. Settings do `garra-backend` → **Pre-Deploy Command**: `cd 04_backend && alembic upgrade head`. Sem isso, a migration `5f9f3cb4d87f` (RBAC/Portal do Cliente, BL-30) e as futuras não são aplicadas — rode uma vez manualmente pelo Shell do Render até configurar o campo.
4. Settings do `garra-backend` → **Health Check Path**: `/health`.
5. Garantir que os recursos estejam no project/grupo `garraengenharia` dentro do workspace da conta.
6. Após 1-4, rodar novo deploy manual e validar `GET /health` retornando `"database":"ok"`.
7. (Opcional, mais robusto) Recriar os 2 serviços via **Blueprint real** (`New → Blueprint`, passos 1-3 acima) para que passem a usar `Dockerfile.render`/`preDeployCommand`/`healthCheckPath` nativamente do `render.yaml`, em vez de manter a configuração manual criada via MCP.

> ✅ Já resolvido via MCP em 2026-08-07 (não precisa refazer): `ENVIRONMENT`, `BACKEND_CORS_ORIGINS`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_DB`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` no backend e `NEXT_PUBLIC_API_URL` no frontend.

---

## HT-12 — Autenticar o servidor MCP do Notion

**Status: ✅ Concluída (2026-08-07).** O servidor MCP `notion` foi autenticado (workspace de `Rafael Pereira`) e o agente criou o board real:

- **Banco de dados:** "Backlog — Garra Engenharia" — https://app.notion.com/p/c5c276e8a13041499be0017833efb379
- **View "Quadro"** agrupada por `Status` (colunas `Backlog` / `To do` / `In progress` / `Done`), conforme DEC-20/ADR-11.
- **Propriedades:** `Tarefa` (título), `Código`, `Status`, `Requisitos`, `Agente` (multi-select), `Etapa`, `Bloqueio`.
- **52 cartões:** as 40 tarefas de engenharia (BL-01 a BL-40) **mais** as 12 tarefas humanas (HT-01 a HT-12), estas últimas identificadas pela `Etapa = "Tarefa humana (HT)"`.

**Manutenção:** o board e [backlog-tarefas.md](backlog-tarefas.md)/[backlog-kanban.md](backlog-kanban.md) precisam ser atualizados em paralelo — não há sincronização automática (limitação já registrada em DEC-20). Com o MCP autenticado, basta pedir ao agente para refletir no Notion qualquer mudança de status feita nos arquivos.

**Por que era uma tarefa humana:** o login OAuth no Notion (escolha da conta/workspace e concessão de escopo) é um ato de autenticação pessoal que não pode passar por chat/agente — mesmo princípio aplicado ao Render (HT-04). Uma vez autenticado, todo o resto foi executado pelo agente.

---

## HT-05 — Configurar proteção das branches `main`/`main_front`/`main_back` no GitHub

**Por que só um humano:** é uma configuração administrativa do repositório (Settings → Branches) que a ferramenta MCP do GitHub disponível no momento não expõe (sem endpoint de "branch protection" no toolset atual).

**Referência:** Seção 1.4 de [plano-gestao-configuracao.md](plano-gestao-configuracao.md#14-proteção-das-branches-main_frontmain_backstaging_frontstaging_back-dec-17), DEC-17 em [decisoes.md](decisoes.md#dec-17--branching-por-serviço-no-monorepo-main_frontmain_backstaging_frontstaging_back) e DEC-22 (remoção de staging + sync automático) em [decisoes.md](decisoes.md#dec-22--consolidação-de-branches-de-deploy-remoção-de-staging-e-sincronização-automática-main--main_backmain_front), pendência registrada em BL-25/BL-26 de `backlog-tarefas.md`.

**Passo a passo (via UI do GitHub):**
1. Acessar `https://github.com/rafaelroriz-age/garra-engenharia/settings/branches`.
2. Adicionar uma regra de proteção para CADA uma das 3 branches: `main`, `main_front`, `main_back` (repetir os passos 3-4 abaixo por branch). `staging`/`staging_front`/`staging_back` foram removidas (DEC-22), não precisam mais de proteção.
3. Marcar: exigir Pull Request antes de merge; exigir o status check `ci.yml`; exigir branch atualizada antes do merge; bloquear force-push e deleção da branch; habilitar apenas squash merge. Em `main_front`/`main_back`, permitir também o bypass do bot `github-actions[bot]` (ou marcar como exceção de "Allow specified actors to bypass required pull requests") para o workflow `sync-deploy-branches.yml` conseguir dar push do merge automático.
4. Salvar e confirmar em `status.md`/memória de repositório que o item foi concluído.

**Alternativa via agente/MCP:**
- Não há tool MCP disponível hoje para isso (o toolset atual do GitHub MCP não expõe branch protection), e em 2026-08-07 o agente verificou que a **GitHub CLI não está autenticada** nesta máquina (`gh auth status` retorna "You are not logged into any GitHub hosts"). Portanto o humano precisa primeiro rodar `gh auth login` (fluxo de browser/token — nunca colar o token no chat) e depois executar:
  ```powershell
  foreach ($branch in @("main", "main_front", "main_back")) {
    gh api -X PUT "repos/rafaelroriz-age/garra-engenharia/branches/$branch/protection" `
      -f required_status_checks[strict]=true `
      -f required_status_checks[contexts][]=ci.yml `
      -f enforce_admins=true `
      -f required_pull_request_reviews[required_approving_review_count]=0 `
      -f restrictions=null
  }
  ```
- Depois de `gh auth login` estar feito, o agente **consegue rodar o comando acima** por conta própria — basta avisar no chat que a autenticação foi concluída.

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

> ⚪ **Sem efeito para a v1.0 (2026-09-10).** A lacuna #9 foi respondida pelo cliente: a responsabilidade técnica é atestada pelo CREA e pela ART impressos no documento, e nenhum contratante exige assinatura ICP-Brasil (DEC-28). Esta tarefa só volta a valer se um contratante futuro passar a exigir assinatura digital.

**Por que só um humano:** é um processo legal com uma Autoridade Certificadora (compra de e-CPF/e-CNPJ, validação presencial ou por vídeo, identidade do engenheiro responsável) — nenhuma ferramenta de código resolve isso.

**Depende de:** resposta à lacuna #9 em HT-01 — **respondida em 2026-09-10: apenas CREA impresso**, sem ICP-Brasil.

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

> **Amostra pronta para conferência (regerada em 2026-09-17).** O agente já executou o passo 1: `01_output-context/_amostras_ht09/amostra_rfo.pdf` (5 páginas) e `amostra_rfo.docx`, renderizados pelo pipeline real (`rfo_pipeline`) com os templates derivados do original em BL-12/BL-13 — capa, 2 relatórios diários com equipe, medições, ocorrências e registro fotográfico. Esta versão já sai com a **marca vetorizada de fundo transparente** no cabeçalho (DEC-30), no lugar do JPEG com fundo creme. A pasta é ignorada pelo Git (saída descartável, regerável). **Falta apenas o passo 2 em diante: a comparação visual e o parecer do engenheiro.**
>
> Para regerar: `docker compose up -d backend` em `05_infra/`, copiar `04_backend/templates/rfo` e o script de amostra para dentro do container (não há bind-mount) e executá-lo — o WeasyPrint não roda no Windows local (faltam as libs GTK).

**Passo a passo:**
1. ~~Gerar um relatório de teste (RFO/LTIP) com dados de exemplo.~~ ✅ feito para o RFO — ver amostra acima. O LTIP ainda depende do `ltip_pipeline.py` (renderização), que não faz parte de BL-17.
2. Abrir lado a lado com o original do cliente arquivado em `01_output-context/` — `.xlsx`/`.xlsm` para RFO/RFIP, PDF final para LTIP e as vistorias (ADR-13).
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
