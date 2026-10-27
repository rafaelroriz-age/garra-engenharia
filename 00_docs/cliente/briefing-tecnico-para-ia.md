---
title: Briefing Técnico do Projeto — Para uso com Inteligência Artificial
type: cliente
status: ativo
owner: Garra Engenharia
audience: cliente (para repassar a outra IA/LLM)
last_updated: 2026-07-24
---

# Briefing Técnico do Projeto — Sistema de Automação de Relatórios Prediais

> **Como usar este documento:** este arquivo foi escrito especificamente para você (cliente) copiar e colar em outra ferramenta de Inteligência Artificial (ChatGPT, Claude, Gemini, etc.) quando precisar gerar um prompt, pedir uma opinião técnica, ou explicar o projeto para terceiros. Ele resume, em um único lugar, **que tipo de serviço está sendo prestado**, as **especificações técnicas**, a **arquitetura**, as **regras de negócio** e as decisões de **infraestrutura/DevOps** do projeto. Não é necessário conhecimento técnico para lê-lo — mas ele é denso o suficiente para que uma IA entenda o contexto completo do projeto.

---

## 1. Resposta direta: "Que tipo de serviço vocês estão executando?"

Não se trata apenas de "programação para gerar [algo]". O serviço prestado é **desenvolvimento de software sob medida (custom software development)** — ou seja, a construção completa de um **sistema web próprio**, do zero, especificamente para a rotina de trabalho da Garra Engenharia. Isso envolve, de forma integrada:

| Frente de trabalho | O que significa na prática |
|---|---|
| **Levantamento de requisitos** | Entender o negócio (engenharia predial/fiscalização) e traduzir a rotina manual atual (planilhas, Word, Lightshot) em processos digitais. |
| **Arquitetura de software** | Desenhar como o sistema é estruturado por dentro: banco de dados, API, camadas, segurança, integrações. |
| **Programação (desenvolvimento)** | Escrever o código do backend (API/regras de negócio) e do frontend (telas que o usuário usa). |
| **Geração automática de documentos** | Programar a lógica que transforma dados cadastrados em PDF/Word fiéis aos modelos técnicos atuais (laudos, relatórios de fiscalização). |
| **DevOps / Infraestrutura** | Configurar onde e como o sistema roda (servidores, banco de dados, backups, deploy automático, ambientes de teste e produção). |
| **Documentação de projeto** | Registrar decisões, escopo, cronograma e regras para dar rastreabilidade e permitir que qualquer profissional (ou IA) entenda o projeto no futuro. |

Em resumo: **é a criação de um produto de software completo e funcional**, não apenas um script ou automação pontual.

---

## 2. Visão Geral do Projeto

- **Nome do projeto:** Sistema de Automação de Relatórios Prediais — Garra Engenharia.
- **Cliente final:** Eng. Civil Esp. Roniel Ribeiro Costa (CREA-GO nº 1020613386/D-GO), atuando pela Garra Engenharia (Aparecida de Goiânia/GO).
- **Domínio de negócio:** inspeção predial, fiscalização de obras e vistorias técnicas de engenharia civil.
- **Problema que resolve:** hoje os laudos e relatórios técnicos (que podem ter de 20 a 200+ páginas e centenas de fotos) são produzidos manualmente em planilhas Excel/XLSM e Word, processo lento (8 a 16 horas por documento) e sujeito a erros.
- **Solução:** um sistema web (utilizável também como app no celular, sem loja de aplicativos — tecnologia PWA) onde o engenheiro registra os dados uma única vez em campo, e o sistema gera automaticamente o relatório final em PDF e Word, fiel ao layout que o cliente já usa hoje, em menos de 1 minuto.
- **Documentos que o sistema produz:**
  1. Relatório de Fiscalização de Obra (RFO) — acompanhamento periódico de obras.
  2. Laudo Técnico de Inspeção Predial (LTIP) — conforme NBR 16747 e IBAPE-NA.
  3. Laudo de Vistoria Cautelar de Recebimento — conformidade de obra concluída.
  4. Vistoria de Imóvel Residencial — diagnóstico técnico por cômodo.
  5. Relatório Fotográfico de Inspeção Predial (RFIP) — fotos organizadas por sistema predial.

---

## 3. Escopo Funcional (o que o sistema faz)

- Cadastro de **edificações** (endereço, tipologia, sistema construtivo, documentos técnicos).
- Cadastro de **contratos** de serviço (partes envolvidas, ARTs, NBRs aplicáveis, empresas executoras).
- Registro de **visitas** de fiscalização (equipe, serviços executados, medições, fotos).
- Registro de **ocorrências** técnicas (sistema predial, subsistema, classificação de anomalia/falha, grau de risco, prioridade, fotos).
- **Editor de anotação de imagens** embutido no sistema (setas, formas, texto, traço livre sobre a foto) — reproduz dentro do próprio sistema a marcação hoje feita externamente na ferramenta Lightshot.
- **Geração automática** de relatório em PDF (WeasyPrint) e Word/DOCX editável (docxtpl), fiéis ao modelo atual do cliente.
- **Dashboard de saúde da edificação**: proporção de itens conformes/não conformes e distribuição por grau de risco (Mínimo/Médio/Crítico), por sistema predial.
- **Portal do Cliente**: área somente leitura para o contratante/síndico acompanhar a auditoria em andamento e baixar os relatórios já emitidos — com controle de acesso (RBAC) que impede ver dados de outros clientes.
- **Histórico de inspeções** por edificação, com versionamento de relatórios emitidos (V01, V02...).
- **Gabarito pré-carregado** de sistemas e subsistemas prediais (dados mestre editáveis).
- **Autenticação** com login e senha (JWT + bcrypt).

**Fora do escopo atual:** app nativo iOS/Android, integração com API do CREA, módulo financeiro/NF, integração direta com Power BI, **assinatura digital ICP-Brasil** e **suporte offline completo** — estes dois últimos confirmados fora de escopo pelo cliente em 2026-09-10 (há 4G/Wi-Fi em campo; a responsabilidade técnica é atestada por CREA/ART impressos).

---

## 4. Regras de Negócio Principais

- Um Relatório de Fiscalização de Obra tem 1 contrato e N visitas (uma por dia de obra acompanhado).
- Toda ocorrência de laudo/vistoria deve ter ao menos 1 foto vinculada.
- Toda ocorrência é classificada por: situação (conforme/não conforme), tipo de anomalia/falha, grau de risco (Crítico/Médio/Mínimo) e prioridade (0 a 5).
- O grau de risco crítico corresponde à maior prioridade padrão (5); médio, prioridade 3; mínimo, prioridade 1.
- Um contrato pode ter mais de uma empresa executora, cada uma com seu próprio responsável técnico (RTE) e ART de execução.
- O documento final deve ser **visualmente idêntico** ao modelo atual do cliente — nenhuma diferença de layout é aceitável.
- Um relatório só pode ser "emitido" com todos os campos obrigatórios preenchidos e ao menos uma foto por ocorrência não conforme.
- Um usuário do tipo "cliente" (Portal do Cliente) só enxerga dados das edificações/contratos em que é o contratante — nunca dados de terceiros.
- A imagem anotada (com marcações) substitui a foto original como a versão definitiva vinculada à ocorrência.

---

## 5. Arquitetura Técnica e Stack

| Camada | Tecnologia escolhida | Por quê |
|---|---|---|
| Frontend | Next.js 14 (App Router), como PWA | Funciona como site e como app instalável no celular, sem loja de apps. |
| Estilo/UI | Tailwind CSS + shadcn/ui | Componentes prontos, acessíveis, produtivos para telas com muitos formulários e tabelas. |
| Backend | FastAPI (Python 3.12) | Mesmo ecossistema das bibliotecas de geração de PDF/DOCX; API assíncrona; documentação automática. |
| Banco de dados | PostgreSQL 16 | Modelo relacional robusto para as entidades do domínio (edificação, contrato, ocorrência, foto). |
| ORM | SQLAlchemy 2 + Alembic | Migrations de banco versionadas. |
| Armazenamento de arquivos | MinIO (self-hosted, compatível S3) | Fotos e relatórios gerados não sobrecarregam o banco de dados relacional. |
| Geração de PDF | WeasyPrint + Jinja2 (HTML → PDF) | Controle fino de layout para atingir fidelidade visual ao modelo atual. |
| Geração de DOCX | docxtpl (python-docx + Jinja2) | Usa o próprio arquivo .docx do cliente como template, preservando a formatação original. |
| Autenticação | JWT + bcrypt | Simples e seguro para uso individual/pequena equipe. |
| Autorização (RBAC) | Papéis `auditor` e `cliente` | Dois perfis de acesso: equipe técnica (escrita total) e contratante (leitura restrita ao próprio contrato). |
| Anotação de imagens | Fabric.js (canvas no navegador) | Desenho de setas/formas/texto sobre a foto direto no navegador, sem backend adicional. |
| Fila/cache | Redis 7 + Celery | Geração de relatórios grandes (até 200 páginas) roda em segundo plano, sem travar a API. |

**Fluxo arquitetural resumido:**
Next.js (navegador/PWA) → FastAPI (API REST) → PostgreSQL (dados) + MinIO (arquivos/fotos) → fila Redis/Celery → gerador de PDF/DOCX → arquivo final disponível para download.

---

## 6. DevOps e Infraestrutura

- **Hospedagem:** Render.com, usando arquivo `render.yaml` como Infraestrutura como Código (Blueprint).
- **Modelo de branches:** repositório único (monorepo) com 4 branches dedicadas, uma por serviço/ambiente:
  - `main_back` → produção do backend.
  - `main_front` → produção do frontend.
  - `staging_back` → ambiente de testes do backend.
  - `staging_front` → ambiente de testes do frontend.
- **Deploy automático:** cada push na branch correspondente dispara o deploy automático apenas daquele serviço (backend ou frontend, produção ou staging), isoladamente.
- **Migrations automáticas:** o schema do banco (Alembic) é sempre atualizado antes de cada deploy do backend.
- **Bancos de dados:** um banco PostgreSQL de produção (`garra-db`) e um de staging (`garra-db-staging`), sendo o de staging um custo adicional opcional.
- **Contêineres:** cada serviço (frontend e backend) tem seu próprio `Dockerfile` de produção (`Dockerfile.render`).
- **Ambiente local de desenvolvimento:** Docker Compose (`05_infra/docker-compose.yml`), reproduzindo localmente banco, backend e frontend.

---

## 7. Status Atual do Projeto

- Fase concluída: levantamento de contexto e documentação (estudo do domínio, arquitetura, escopo).
- Estrutura de código já criada: `03_frontend/` (Next.js) e `04_backend/` (FastAPI), com componentes, rotas de API, modelos de dados e testes iniciais.
- Protótipos de tela (HTML navegável) já produzidos em `02_prototipos/`.
- A validação de requisitos com o cliente foi **concluída**: uso offline, perfis de acesso da equipe e assinatura digital em 2026-09-10; periodicidade de re-inspeção, formato das medições do RFO, obrigatoriedade do DOCX, origem das fotos e integração com o CREA em 2026-09-17. Restam apenas duas escolhas operacionais, não de requisito: o provedor de IA para as legendas assistidas e o destino externo do backup.

---

## 8. Sugestão de uso deste documento com uma IA

Você pode colar este arquivo inteiro em outra IA e pedir, por exemplo:
- *"Com base neste briefing, crie um prompt para gerar [uma tela/funcionalidade/documento específico]."*
- *"Explique este projeto para uma pessoa não técnica em 3 parágrafos."*
- *"Liste riscos técnicos que este projeto pode ter, com base na arquitetura descrita."*

---

## Itens para aprovação do cliente

- [ ] Confirmar se este resumo representa corretamente o serviço contratado, para uso em comunicações externas.
- [ ] Indicar se há informações sensíveis (dados de contrato, valores, nomes) que **não** devem ser incluídas caso este documento seja repassado a terceiros ou a ferramentas de IA externas.
