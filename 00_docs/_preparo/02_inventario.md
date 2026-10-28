---
title: Inventário da documentação existente
type: knowledge
status: draft
owner: Garra Engenharia
related:
  - 00_docs/projeto/plano-gestao-configuracao.md
  - .github/pull_request_template.md
tags: [inventario, documentacao, preparo]
last_updated: 2026-10-28
---

<!-- ai-summary
System: inventário (sem avaliação de qualidade) de toda a documentação rastreada no repositório garra-engenharia.
Flow: 109 arquivos .md/.docx/README listados por pasta; docstrings de módulo e cabeçalhos de scripts resumidos à parte.
Owner: Garra Engenharia.
Status: draft — etapa D02; a avaliação de qualidade é a próxima etapa.
-->

# Inventário da documentação existente

> Etapa D02. Apenas inventário: não há avaliação de qualidade aqui. Escopo: arquivos rastreados pelo Git (`git ls-files`). "Último commit" vem de `git log -1 --format=%cs -- <arquivo>`; tamanho é o do arquivo no disco; "Resumo" vem do título, do `ai-summary`/`description` do próprio arquivo ou da leitura do início do texto.

## Visão geral

- Documentação existe: 109 arquivos `.md`, `.docx` e `README` rastreados (tabelas abaixo).
- Docstrings de módulo Python: 119 arquivos com docstring de módulo (seção própria).
- Cabeçalhos de scripts e configs: 10 arquivos (seção própria).
- Convenção de documentos em `00_docs/`: frontmatter YAML (`title`, `type`, `status`, `owner`, `related`, `tags`, `last_updated`) e bloco `<!-- ai-summary ... -->`, como em `00_docs/estudo-do-contexto.md` (este arquivo segue o mesmo formato). Nem todos os arquivos de `00_docs/` a seguem; o levantamento não verificou arquivo por arquivo.
- Regras de commit e de pastas da documentação: `00_docs/projeto/plano-gestao-configuracao.md` §1.2 e `05_infra/README.md` (DEC-09).

## Procurado e não encontrado

Verificado com `git ls-files` (arquivos rastreados); não existem:

- `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING*`, `.github/copilot-instructions.md`, `BACKLOG.md` (a "Regra de pronto do BACKLOG.md" citada na tarefa não foi localizada em nenhum `.md`; o backlog existente é `00_docs/projeto/backlog-tarefas.md`).
- Arquivos `.rst`, `.ipynb` e `.txt` de documentação (o único `.txt` rastreado é `04_backend/requirements.txt`, lista de dependências).
- Pasta de wiki ou `docs/`: não há. Wiki hospedada no GitHub: não determinado (não verificado).
- `02_prototipos/` contém 7 arquivos `.html` (protótipos), não listados por serem protótipos e não documentação textual.
- Comentários e docstrings em `03_frontend/` (53 arquivos `.ts`/`.tsx`): não determinado, não varridos.

## Arquivos de documentação

### `.github/agents` (16)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `.github/agents/arquiteto-software.agent.md` | Agente (Copilot) | 1,8 KB | 2026-07-19 | Use quando precisar definir a arquitetura de software: escolha de stack, estrutura de pastas, separação de camadas, padrões de projeto, modelo de dados, contratos de API e diagramas. Consome o estudo do contexto e produz o blueprint técnico. |
| `.github/agents/backend.agent.md` | Agente (Copilot) | 1,5 KB | 2026-07-19 | Use quando precisar desenvolver o backend: APIs REST/GraphQL, modelos e migrações de banco de dados, regras de negócio, autenticação/autorização, validações, serviços e testes de servidor. |
| `.github/agents/contratos-juridicos.agent.md` | Agente (Copilot) | 4,6 KB | 2026-07-19 | Use quando precisar analisar, revisar, redigir ou interpretar contratos jurídicos: contratos de prestação de serviços, contratos de obras, laudos periciais, vistorias cautelares, contratos de compra e venda, cláusulas de responsabilidade, multas contratuais, rescisão, inadimplência, NDA, contratos de empreitada, contrato de engenharia, análise de risco jurídico, revisão de minutas, identificar cláusulas abusivas, obrigações das partes, prazo contratual, foro de eleição, legislação brasileira. |
| `.github/agents/conversor-documentos-md.agent.md` | Agente (Copilot) | 2,0 KB | 2026-07-19 | Use quando precisar converter documentos do contexto (xlsx, xlsm, docx, pdf, csv, pptx) em arquivos Markdown (.md) estruturados e fiéis. Extrai tabelas, textos, planilhas e metadados preservando a estrutura original. |
| `.github/agents/criador-de-prompts.agent.md` | Agente (Copilot) | 3,4 KB | 2026-07-19 | Use quando precisar criar, melhorar ou adaptar prompts para qualquer um dos agentes especializados do projeto; gerar o prompt de ativação completo do fluxo; ou criar um prompt do zero para uma tarefa específica. Conhece o papel, ferramentas e saídas esperadas de todos os agentes. |
| `.github/agents/design-ui-ux.agent.md` | Agente (Copilot) | 2,1 KB | 2026-08-12 | Use quando precisar criar, revisar ou evoluir experiencias de UI/UX: descoberta de requisitos, fluxos, arquitetura de informacao, wireframes, design system, microinteracoes, acessibilidade e handoff para desenvolvimento. |
| `.github/agents/devops.agent.md` | Agente (Copilot) | 5,3 KB | 2026-07-19 | Use quando precisar configurar infraestrutura, CI/CD, containers, deploy, monitoramento, backup, segurança de ambiente e automação operacional do sistema. Cobre Docker, pipelines, cloud, variáveis de ambiente, logs, alertas e estratégias de release. |
| `.github/agents/engenheiro-ia.agent.md` | Agente (Copilot) | 7,1 KB | 2026-07-29 | Use quando precisar integrar o sistema a modelos de IA (LLMs, transcrição, embeddings), configurar ou consumir servidores MCP, ou avaliar/implementar features baseadas em IA generativa (sugestão de classificação, resumo de laudos, transcrição de áudio de campo, assistentes). |
| `.github/agents/engenheiro-software.agent.md` | Agente (Copilot) | 1,4 KB | 2026-07-19 | Use quando precisar implementar funcionalidades de ponta a ponta, escrever testes, refatorar código, integrar backend e frontend, configurar build/CI e garantir qualidade seguindo a arquitetura definida. |
| `.github/agents/estudo-contexto.agent.md` | Agente (Copilot) | 1,8 KB | 2026-07-19 | Use quando precisar estudar e analisar o contexto do projeto: ler documentos, planilhas e relatórios do domínio, extrair regras de negócio, entidades, requisitos e restrições, e produzir um documento de entendimento consolidado. |
| `.github/agents/frontend.agent.md` | Agente (Copilot) | 1,4 KB | 2026-07-19 | Use quando precisar desenvolver o frontend: componentes de UI, telas, formulários, consumo de APIs, gerenciamento de estado, roteamento, responsividade, acessibilidade e testes de interface. |
| `.github/agents/gestor-projeto-arquiteto-solucoes.agent.md` | Agente (Copilot) | 3,7 KB | 2026-07-19 | Use quando precisar gerenciar o projeto de ponta a ponta ou definir a solução no nível executivo: escopo, cronograma, riscos, decisões de arquitetura de alto nível, coordenação entre agentes especializados, status do projeto e comunicação com stakeholders. Orquestra os demais agentes (Conversor, Estudo do Contexto, Arquiteto, Backend, Frontend, Prototipagem, Organizador) no fluxo correto. |
| `.github/agents/guia_passo_a_passo_segundo_cerebro_projeto_novo.md` | Metodologia (genérico) | 8,5 KB | 2026-07-19 | Guia passo a passo para montar um "segundo cérebro" (base de conhecimento em Markdown para IA), baseado em uma palestra; não trata do domínio do projeto. |
| `.github/agents/organizador-pastas.agent.md` | Agente (Copilot) | 2,1 KB | 2026-07-19 | Use quando precisar organizar a estrutura de pastas e arquivos do projeto: definir e aplicar convenções de nomenclatura, mover/agrupar arquivos por tipo ou domínio, criar estrutura de diretórios padrão, limpar arquivos temporários/soltos e manter o repositório arrumado. |
| `.github/agents/prompt_infra_segundo_cerebro_projeto_novo.md` | Metodologia (genérico) | 14,0 KB | 2026-07-19 | Prompt autocontido para outro agente construir a infraestrutura de conhecimento (frontmatter YAML, ai-summary, cross-linking, rubrica de confiança). |
| `.github/agents/prototipagem-documentacao-cliente.agent.md` | Agente (Copilot) | 2,4 KB | 2026-07-19 | Use quando precisar prototipar a solução e produzir documentação orientada ao cliente: protótipos e wireframes de baixa/alta fidelidade, mockups de telas, protótipos navegáveis, propostas, manuais de uso e apresentações. Traduz requisitos técnicos em linguagem clara para o cliente. |

### `.github/prompts` (45)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `.github/prompts/00-ativar-fluxo-completo.prompt.md` | Prompt (Copilot) | 1,9 KB | 2026-07-19 | Ativa o fluxo completo do projeto: invoca o Gestor de Projeto para orquestrar todos os agentes especializados na sequência correta, do contexto até a entrega final. |
| `.github/prompts/01-converter-documentos.prompt.md` | Prompt (Copilot) | 1,2 KB | 2026-07-19 | Ativa o agente Conversor de Documentos para Markdown para converter todos os documentos de 01_output-context/ em arquivos .md estruturados. |
| `.github/prompts/02-estudo-contexto.prompt.md` | Prompt (Copilot) | 1,2 KB | 2026-07-19 | Ativa o agente Estudo do Contexto para analisar os documentos convertidos e produzir o documento de entendimento consolidado do domínio. |
| `.github/prompts/03-organizar-pastas.prompt.md` | Prompt (Copilot) | 1,4 KB | 2026-07-19 | Ativa o agente Organizador de Pastas para inventariar e reorganizar a estrutura de diretórios do repositório. |
| `.github/prompts/04-arquitetura.prompt.md` | Prompt (Copilot) | 1,2 KB | 2026-07-19 | Ativa o agente Arquiteto de Software para definir stack, modelo de dados, contratos de API e blueprint técnico da solução. |
| `.github/prompts/05-prototipagem.prompt.md` | Prompt (Copilot) | 1,3 KB | 2026-07-19 | Ativa o agente Prototipagem e Documentação para Cliente para criar wireframes, mockups e documentação orientada ao cliente. |
| `.github/prompts/06-backend.prompt.md` | Prompt (Copilot) | 1,1 KB | 2026-07-19 | Ativa o agente Engenheiro Backend para implementar APIs, modelos de banco de dados e regras de negócio. |
| `.github/prompts/07-frontend.prompt.md` | Prompt (Copilot) | 1,1 KB | 2026-07-19 | Ativa o agente Engenheiro Frontend para implementar telas, componentes de UI e integração com as APIs do backend. |
| `.github/prompts/08-engenheiro-software.prompt.md` | Prompt (Copilot) | 1,1 KB | 2026-07-19 | Ativa o agente Engenheiro de Software para integrar backend e frontend, escrever testes ponta a ponta e configurar build/CI. |
| `.github/prompts/09-criar-prompt.prompt.md` | Prompt (Copilot) | 1,2 KB | 2026-07-19 | Ativa o agente Criador de Prompts para gerar, refinar ou adaptar um prompt para qualquer agente especializado do projeto. |
| `.github/prompts/10-iniciar-documentacao-sistema-predial.prompt.md` | Prompt (Copilot) | 7,2 KB | 2026-07-19 | Prompt mestre para iniciar a documentação e arquitetura do sistema de automação de relatórios prediais da Garra Engenharia. Ativa os agentes Estudo do Contexto e Arquiteto de Software em sequência. |
| `.github/prompts/11-projetar-sistema-predial.prompt.md` | Prompt (Copilot) | 13,3 KB | 2026-07-19 | Prompt mestre completo para projetar o sistema de automação de relatórios prediais da Garra Engenharia: estudo do contexto, arquitetura, prototipagem para o cliente, especificação de backend, especificação de frontend e plano de implementação faseado. Ativa todos os agentes de engenharia e arquitetura em sequência. |
| `.github/prompts/12-devops.prompt.md` | Prompt (Copilot) | 3,4 KB | 2026-07-19 | Ativa o agente Engenheiro DevOps para configurar infraestrutura, CI/CD, containers, deploy, monitoramento e backup do sistema de relatórios prediais. |
| `.github/prompts/12-proposta-comercial-e-prototipo.prompt.md` | Prompt (Copilot) | 10,3 KB | 2026-07-19 | Ativa o agente Prototipagem e Documentação para Cliente para criar proposta comercial em PDF, protótipo visual de alta fidelidade e apresentação em PPTX. |
| `.github/prompts/13-planejar-ciclo-vida-e-tarefas.prompt.md` | Prompt (Copilot) | 4,9 KB | 2026-07-19 | Ativa o agente Engenheiro de Software para ler o escopo, escolher o modelo de ciclo de vida, definir etapas, documentar requisitos detalhados, montar cronograma, ordenar o backlog de tarefas de forma crescente e gerar os prompts das tarefas iniciais. |
| `.github/prompts/14-setup-ambiente-desenvolvimento.prompt.md` | Prompt (Copilot) | 2,5 KB | 2026-07-19 | Ativa o agente Engenheiro DevOps para configurar o ambiente de desenvolvimento local com Docker Compose (PostgreSQL + MinIO) do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/15-scaffold-backend-fastapi.prompt.md` | Prompt (Copilot) | 2,6 KB | 2026-07-19 | Ativa o agente Engenheiro Backend para criar o scaffold inicial do backend FastAPI do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/16-scaffold-frontend-nextjs-pwa.prompt.md` | Prompt (Copilot) | 2,6 KB | 2026-07-19 | Ativa o agente Engenheiro Frontend para criar o scaffold inicial do frontend Next.js 14 PWA do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/17-modelagem-dados-migrations.prompt.md` | Prompt (Copilot) | 2,5 KB | 2026-07-19 | Ativa o agente Engenheiro Backend para modelar as entidades de dados e criar as migrations Alembic do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/17-templates-ltip-relatorio-fotografico.prompt.md` | Prompt (Copilot) | 3,8 KB | 2026-09-10 | Ativa o agente de Prototipagem/Backend para derivar os templates HTML/CSS e DOCX do LTIP e do relatório fotográfico por sistema a partir do PDF original do cliente. |
| `.github/prompts/18-seed-gabarito-sistemas-prediais.prompt.md` | Prompt (Copilot) | 3,4 KB | 2026-07-19 | Ativa o agente Engenheiro Backend para popular os dados mestre (gabarito de sistemas prediais, subsistemas, classificações e localizações) do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/19-autenticacao-jwt.prompt.md` | Prompt (Copilot) | 2,8 KB | 2026-07-19 | Ativa o agente Engenheiro Backend para implementar autenticação JWT + bcrypt do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/20-storage-service-minio.prompt.md` | Prompt (Copilot) | 3,0 KB | 2026-07-20 | Ativa o agente Engenheiro Backend para implementar o serviço de armazenamento de arquivos (MinIO/S3) do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/21-crud-edificacoes.prompt.md` | Prompt (Copilot) | 3,1 KB | 2026-07-20 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o CRUD completo de Edificações do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/22-crud-contratos.prompt.md` | Prompt (Copilot) | 3,5 KB | 2026-07-20 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o CRUD de Contratos com múltiplas empresas executoras e NBRs do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/23-registro-visitas-rfo.prompt.md` | Prompt (Copilot) | 3,4 KB | 2026-07-20 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o registro de Visitas do RFO (equipe, serviços, medições) do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/24-upload-fotos-lightshot.prompt.md` | Prompt (Copilot) | 4,2 KB | 2026-07-20 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o upload de fotos (clipboard paste do Lightshot + upload manual) vinculado a Visitas e Ocorrências do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/25-crud-ocorrencias.prompt.md` | Prompt (Copilot) | 4,1 KB | 2026-07-20 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o CRUD de Ocorrências (LTIP) do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/26-dashboard-saude-edificacao.prompt.md` | Prompt (Copilot) | 3,6 KB | 2026-07-20 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o Dashboard de saúde por edificação/sistema predial do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/27-docker-compose-prod-nginx.prompt.md` | Prompt (Copilot) | 3,2 KB | 2026-07-20 | Ativa o agente Engenheiro DevOps para implementar docker-compose.prod.yml e o reverse proxy Nginx com HTTPS do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/28-backup-restore-scripts.prompt.md` | Prompt (Copilot) | 2,8 KB | 2026-07-20 | Ativa o agente Engenheiro DevOps para implementar os scripts de backup e restore do PostgreSQL/MinIO do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/29-testes-e2e-rfo-ltip.prompt.md` | Prompt (Copilot) | 2,6 KB | 2026-07-20 | Ativa o agente Engenheiro de Software para implementar os testes E2E dos fluxos RFO e LTIP do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/30-benchmark-geracao-relatorios.prompt.md` | Prompt (Copilot) | 2,7 KB | 2026-07-20 | Ativa o agente Engenheiro de Software (com apoio do Engenheiro DevOps) para realizar o benchmark de geração de PDF/DOCX do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/31-revisao-seguranca-owasp.prompt.md` | Prompt (Copilot) | 3,3 KB | 2026-07-20 | Ativa o agente Engenheiro de Software (ou Engenheiro Backend) para realizar a revisão de segurança OWASP Top 10 do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/32-rbac-portal-cliente-acesso.prompt.md` | Prompt (Copilot) | 5,0 KB | 2026-07-29 | Ativa o agente Engenheiro Backend para implementar o RBAC (perfis auditor/cliente), o vínculo de login do contratante e a base de acesso do Portal do Cliente do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/33-editor-anotacao-fotos.prompt.md` | Prompt (Copilot) | 4,1 KB | 2026-07-29 | Ativa o agente Engenheiro Frontend para implementar o editor de anotação de fotos (setas, formas, texto, traço livre) integrado ao upload de fotos do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/34-portal-cliente-dashboard-acompanhamento.prompt.md` | Prompt (Copilot) | 4,2 KB | 2026-07-29 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o dashboard e o acompanhamento da auditoria no Portal do Cliente do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/35-portal-cliente-documentos.prompt.md` | Prompt (Copilot) | 4,2 KB | 2026-07-29 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar a listagem e o download de documentos/relatórios no Portal do Cliente do Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/36-extensao-modelagem-legendas-ia.prompt.md` | Prompt (Copilot) | 2,4 KB | 2026-07-29 | Ativa o agente Engenheiro Backend para estender a modelagem de dados do fluxo de legendas assistidas por IA no Sistema de Automação de Relatórios Prediais. |
| `.github/prompts/37-storage-legendas-ia.prompt.md` | Prompt (Copilot) | 1,7 KB | 2026-07-29 | Ativa o agente Engenheiro Backend para integrar o armazenamento e a rastreabilidade dos artefatos do fluxo de legendas assistidas por IA. |
| `.github/prompts/38-integracao-upload-legendas-ia.prompt.md` | Prompt (Copilot) | 1,7 KB | 2026-07-29 | Ativa os agentes Engenheiro Backend e Engenheiro Frontend para integrar o fluxo de upload/edição de fotos com a geração de legendas assistidas por IA. |
| `.github/prompts/39-integracao-anotacao-legendas-ia.prompt.md` | Prompt (Copilot) | 1,4 KB | 2026-07-29 | Ativa o agente Engenheiro Frontend para integrar o editor de anotação de fotos ao fluxo de aprovação de legendas assistidas por IA. |
| `.github/prompts/40-template-docx-contrato-prestacao-servicos.prompt.md` | Prompt (Copilot) | 3,2 KB | 2026-08-05 | Ativa o agente Engenheiro Backend para gerar um template DOCX reutilizável (Jinja/docxtpl) do Contrato de Prestação de Serviços a partir do documento revisado enviado pelo cliente. |
| `.github/prompts/41-refatoracao-branding-frontend-uiux.prompt.md` | Prompt (Copilot) | 4,1 KB | 2026-08-12 | Ativa o agente Especialista UI/UX para refatorar a identidade visual do frontend e aplicar as logos oficiais da Garra Perícias e Avaliações. |
| `.github/prompts/42-rbac-perfil-auxiliar.prompt.md` | Prompt (Copilot) | 4,0 KB | 2026-09-10 | Ativa o agente Engenheiro Backend (com etapa final de Frontend) para implementar o terceiro perfil de acesso `auxiliar` — escrita limitada a dados de campo e autoria rastreável — no Sistema de Automação de Relatórios Prediais. |

### `.github (raiz)` (1)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `.github/pull_request_template.md` | Governança | 728 B | 2026-07-19 | Modelo de PR: descrição, referências (BL/RF/RN/DEC) e checklist de testes (`pytest`, `npm run lint`/`build`). |

### `00_docs` (35)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `00_docs/analise-comparativa-contratos.md` | Jurídico/contrato | 17,7 KB | 2026-07-19 | Comparação, sob a ótica do CONTRATADO, entre o contrato original de desenvolvimento e a versão revisada proposta pela CONTRATANTE. |
| `00_docs/arquitetura.md` | Arquitetura | 68,7 KB | 2026-09-10 | Blueprint técnico: Next.js PWA → FastAPI → PostgreSQL + MinIO, geração de PDF/DOCX (WeasyPrint + docxtpl), ADRs, segurança (ai-summary do próprio arquivo). |
| `00_docs/cliente/apresentacao-comercial.md` | Comercial | 10,1 KB | 2026-07-19 | Roteiro de 15 slides da apresentação comercial do sistema (paleta e tipografia indicadas no cabeçalho). |
| `00_docs/cliente/briefing-tecnico-para-ia.md` | Cliente/briefing | 11,2 KB | 2026-09-10 | Briefing técnico para o cliente colar em outras ferramentas de IA ao explicar ou pedir opinião sobre o projeto. |
| `00_docs/cliente/prompt-lado-cliente.md` | Cliente/prompt | 41,5 KB | 2026-07-29 | Prompt-sistema universal do cliente para transcrição de áudio e redação de legendas fotográficas técnicas. |
| `00_docs/cliente/proposta-comercial.md` | Comercial | 10,4 KB | 2026-07-19 | Proposta comercial do Sistema de Automação de Relatórios Prediais, preparada para conversão em PDF. |
| `00_docs/cliente/relatorio-situacao-mvp.docx` | Status (cliente) | 29,1 KB | 2026-09-10 | Documento Word com a situação do MVP; conteúdo não lido (formato binário), resumo não determinado. |
| `00_docs/cliente/solicitacao-templates-docx.md` | Cliente/pendência | 3,7 KB | 2026-08-12 | Minuta de pedido ao cliente dos modelos originais (.docx/.xlsm) e do logo (HT-02), que resolve o bloqueio B-02. |
| `00_docs/contrato-prestacao-servicos-desenvolvimento.md` | Jurídico/contrato | 19,6 KB | 2026-07-19 | Minuta de contrato de prestação de serviços de desenvolvimento e manutenção de software, com campos em branco. |
| `00_docs/convertidos/COND.md` | Insumo convertido | 17,0 KB | 2026-07-19 | Conversão para Markdown de `COND.pdf` (título "COND"). |
| `00_docs/convertidos/Contrato_Prestacao_Servicos_Software.md` | Insumo convertido | 28,2 KB | 2026-07-19 | Conversão de contrato de prestação de serviços de desenvolvimento, implantação, manutenção e suporte de software. |
| `00_docs/convertidos/Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md` | Insumo convertido | 368,0 KB | 2026-07-19 | Conversão do Laudo Técnico de Inspeção Predial 2026 do Cond. Cortina D'Ampezzo. |
| `00_docs/convertidos/Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md` | Insumo convertido | 157,5 KB | 2026-07-19 | Conversão do Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York (V01). |
| `00_docs/convertidos/Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md` | Insumo convertido | 93,7 KB | 2026-07-19 | Conversão do Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404. |
| `00_docs/convertidos/README.md` | Índice | 4,7 KB | 2026-07-19 | Índice dos 9 documentos convertidos para Markdown nesta pasta (origem, tipo, tamanho e status). |
| `00_docs/convertidos/RFO_INSPECAO.md` | Insumo convertido | 346,4 KB | 2026-07-19 | Conversão do modelo "RFO INSPEÇÃO" (origem registrada no README da pasta). |
| `00_docs/convertidos/Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md` | Insumo convertido | 416,0 KB | 2026-07-19 | Conversão do Relatório Fotográfico de Inspeção Predial - Cortina D'Amparezzo (versão final). |
| `00_docs/convertidos/Relatorio_de_Fiscalizacao.md` | Insumo convertido | 458,4 KB | 2026-07-19 | Conversão do "Relatório de Fiscalização". |
| `00_docs/convertidos/Relatorio_de_Fiscalizacao_1.md` | Insumo convertido | 160,6 KB | 2026-07-19 | Conversão do "Relatório de Fiscalização 1" (versão da pasta de convertidos). |
| `00_docs/estudo-do-contexto.md` | Requisitos/domínio | 26,3 KB | 2026-09-10 | Entendimento consolidado do domínio: RF/RNF/RN, entidades, perfis, portal do cliente, legendas por IA e lacunas (§9). |
| `00_docs/projeto/ata-validacao-lacunas.md` | Gestão | 5,5 KB | 2026-09-10 | Ata da validação parcial das lacunas com o cliente (Bloco 1, 2026-09-10), que gerou DEC-26, DEC-27 e DEC-28. |
| `00_docs/projeto/backlog-kanban.md` | Gestão | 7,0 KB | 2026-09-10 | Espelho local do board Kanban no Notion (DEC-20/ADR-11) com os cartões BL e HT. |
| `00_docs/projeto/backlog-tarefas-humanas.md` | Gestão | 33,6 KB | 2026-09-10 | Backlog das tarefas que só uma pessoa pode executar (decisão, cliente, credenciais, atos legais). |
| `00_docs/projeto/backlog-tarefas.md` | Gestão | 34,4 KB | 2026-09-10 | Backlog de tarefas de engenharia (BL-XX), ordenado por complexidade/dependência, ligado ao ciclo de vida e aos RF/RNF/RN. |
| `00_docs/projeto/ciclo-de-vida.md` | Gestão | 6,5 KB | 2026-09-10 | Modelo de ciclo de vida de desenvolvimento e suas etapas (frontmatter: type gestao, status aprovado). |
| `00_docs/projeto/cronograma.md` | Gestão | 3,1 KB | 2026-07-19 | Cronograma por etapa em semanas úteis, com início em 2026-07-17 e dependências. |
| `00_docs/projeto/decisoes.md` | Gestão | 63,2 KB | 2026-09-10 | Registro de decisões (DEC-XX), datadas e justificadas, a partir de DEC-01 (WeasyPrint + Jinja2). |
| `00_docs/projeto/escopo.md` | Gestão | 5,7 KB | 2026-09-10 | Identificação do projeto e o que está dentro e fora do escopo. |
| `00_docs/projeto/pauta-validacao-lacunas.md` | Gestão | 5,7 KB | 2026-09-10 | Pauta da sessão de validação das lacunas com o cliente; Bloco 1 respondido, Blocos 2 a 4 pendentes. |
| `00_docs/projeto/plano-gestao-configuracao.md` | Gestão/DevOps | 15,9 KB | 2026-08-12 | Plano de gestão de configuração: monorepo, Git, CI/CD e deploy. |
| `00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md` | Relatório técnico | 11,9 KB | 2026-08-12 | Resultado do benchmark de geração de PDF/DOCX do RFO (BL-22). |
| `00_docs/projeto/resumo-executivo.md` | Gestão | 4,5 KB | 2026-07-19 | Resumo executivo: o problema (relatórios manuais de engenharia predial) e a solução proposta. |
| `00_docs/projeto/revisao-seguranca-owasp.md` | Segurança | 9,3 KB | 2026-09-10 | Revisão de segurança do backend e frontend contra o OWASP Top 10:2021 (BL-23, RNF-05). |
| `00_docs/projeto/riscos.md` | Gestão | 10,7 KB | 2026-09-10 | Registro de riscos (R-XX) com probabilidade, impacto e prioridade. |
| `00_docs/projeto/status.md` | Gestão | 27,9 KB | 2026-09-10 | Status do projeto: fase atual e andamento do MVP. |

### `01_output-context` (3)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `01_output-context/Contrato_Revisado_Garra_Software.md` | Insumo do cliente | 24,5 KB | 2026-07-19 | Contrato revisado de prestação de serviços de software (18 cláusulas + 2 anexos), convertido de DOCX. |
| `01_output-context/README.md` | Índice | 2,4 KB | 2026-07-19 | Índice dos 2 arquivos Markdown gerados a partir dos originais do cliente nesta pasta. |
| `01_output-context/Relatorio_de_Fiscalizacao_1.md` | Insumo do cliente | 162,7 KB | 2026-07-19 | Conversão de `Relatório de Fiscalização 1.xlsm` (11 abas). |

### `03_frontend` (1)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `03_frontend/README.md` | Frontend | 10,1 KB | 2026-09-10 | Descreve o frontend Next.js 14 (App Router) PWA e seu estado funcional. |

### `04_backend` (7)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `04_backend/README.md` | Backend | 12,9 KB | 2026-09-10 | Descreve o backend FastAPI (Python 3.12) e seu estado funcional. |
| `04_backend/alembic/README` | Backend | 58 B | 2026-07-19 | Texto padrão do Alembic: "Generic single-database configuration with an async dbapi." |
| `04_backend/templates/contracts/contrato_revisado_template.docx` | Backend/template | 45,1 KB | 2026-08-05 | Template DOCX do contrato revisado (binário; campos listados no .placeholders.md). |
| `04_backend/templates/contracts/contrato_revisado_template.placeholders.md` | Backend/template | 851 B | 2026-08-05 | Lista dos campos Jinja2 usados em `contrato_revisado_template.docx` (para `docxtpl`). |
| `04_backend/templates/ltip/ltip_template.docx` | Backend/template | 37,3 KB | 2026-09-10 | Template DOCX do LTIP (binário; gerado por `build_ltip_templates.py`). |
| `04_backend/templates/rfo/rfo_template.docx` | Backend/template | 36,8 KB | 2026-09-10 | Template DOCX do RFO (binário; gerado por `build_rfo_templates.py`). |
| `04_backend/templates/rfo_benchmark_template.docx` | Backend/template | 36,0 KB | 2026-08-12 | Template DOCX base do benchmark do RFO, fidelidade aproximada (gerado por `build_rfo_benchmark_docx_template.py`). |

### `05_infra` (1)

| Caminho | Tema | Tamanho | Último commit | Resumo |
|---|---|---|---|---|
| `05_infra/README.md` | Infra | 10,7 KB | 2026-08-12 | Infraestrutura local e deploy: decisão DEC-09/ADR-05 (tudo em `05_infra/`), comandos `docker compose`. |

## Cabeçalhos de scripts e configs

| Caminho | Tamanho | Último commit | Resumo |
|---|---|---|---|
| `.github/dependabot.yml` | 726 B | 2026-07-19 | Comentário de cabeçalho: mantém dependências atualizadas e escaneadas; complementa o scan Trivy do `ci.yml`. |
| `.github/workflows/ci.yml` | 6,8 KB | 2026-08-12 | Cabeçalho: integração contínua, roda em todo PR e em push para o trunk (`main`) e branches de deploy. |
| `.github/workflows/cd-production.yml` | 4,2 KB | 2026-08-05 | Cabeçalho: deploy em produção via SSH/VPS, fallback manual (DEC-17). |
| `.github/workflows/cd-staging.yml` | 3,1 KB | 2026-08-05 | Cabeçalho: deploy contínuo em staging via SSH/VPS, desativado por padrão (DEC-17). |
| `.github/workflows/sync-deploy-branches.yml` | 2,5 KB | 2026-08-05 | Cabeçalho: propaga push em `main` para `main_back` e `main_front` (DEC-22). |
| `05_infra/backup/backup-db.sh` | 3,5 KB | 2026-08-12 | Cabeçalho: dump lógico do PostgreSQL e espelho do bucket MinIO com política de retenção (BL-29); inclui uso e agendamento sugerido. |
| `05_infra/backup/restore-db.sh` | 2,5 KB | 2026-08-12 | Cabeçalho: restaura um dump gerado por `backup-db.sh`; operação destrutiva que recria o schema do banco alvo e exige confirmação (BL-29). |
| `05_infra/docker-compose.prod.yml` | 6,2 KB | 2026-08-12 | Cabeçalho: stack de produção/staging em VPS próprio (Docker + Nginx), BL-27; explica quando o arquivo é e não é usado, já que a hospedagem oficial é o Render. |
| `05_infra/docker-compose.yml` | 7,0 KB | 2026-07-29 | Cabeçalho: ambiente de desenvolvimento local; lembra a convenção DEC-09 (executar a partir de `05_infra/`). |
| `render.yaml` | 6,4 KB | 2026-09-04 | Cabeçalho: blueprint de deploy no Render (IaC), monorepo com branches dedicadas de deploy (DEC-17, DEC-22). |

## Docstrings de módulo (Python)

Contagem por pasta, obtida com `ast.get_docstring` sobre os `.py` rastreados. Nos exemplos lidos, a primeira linha descreve o módulo e costuma citar tarefa/requisito (BL, RF, RN, DEC, ADR); em `alembic/versions` é o título da migration. Quantidade de arquivos `.py` sem docstring de módulo: não calculada.

| Pasta | Arquivos com docstring de módulo |
|---|---|
| `04_backend` | 1 |
| `04_backend/alembic/versions` | 5 |
| `04_backend/app` | 1 |
| `04_backend/app/api` | 1 |
| `04_backend/app/api/v1` | 11 |
| `04_backend/app/core` | 8 |
| `04_backend/app/models` | 20 |
| `04_backend/app/repositories` | 7 |
| `04_backend/app/schemas` | 23 |
| `04_backend/app/scripts` | 12 |
| `04_backend/app/services` | 13 |
| `04_backend/tests` | 17 |
| **Total** | **119** |

Exemplos: `04_backend/app/main.py` ("Ponto de entrada da API FastAPI — scaffold inicial (BL-02)"), `04_backend/app/core/config.py` ("Configurações da aplicação, carregadas de variáveis de ambiente / `.env`"), `04_backend/app/scripts/build_ltip_templates.py` (deriva os templates do LTIP a partir do PDF do cliente).

