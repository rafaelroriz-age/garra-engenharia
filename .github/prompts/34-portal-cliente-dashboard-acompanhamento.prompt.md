---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o dashboard e o acompanhamento da auditoria no Portal do Cliente do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-32 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 4.5 (RBAC, Editor de Anotação de Fotos e Portal do Cliente). Depende de BL-30 (RBAC + router `/portal` base, `32-rbac-portal-cliente-acesso.prompt.md`) e reaproveita a agregação de BL-16 (Dashboard de saúde por edificação, `26-dashboard-saude-edificacao.prompt.md`).
Origem: esclarecimento direto do usuário (2026-07-24) — o "cliente" acompanha a auditoria feita pelo "auditor" através de dashboards. Requisitos/decisões: RF-13, RN-14 (`00_docs/estudo-do-contexto.md`), DEC-18 (`00_docs/projeto/decisoes.md`), ADR-09 e Seção 4 "Portal do Cliente" (`00_docs/arquitetura.md`).

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. No router `app/api/v1/portal.py` (criado em BL-30), implemente:
   - `GET /portal/edificacoes/{id}/dashboard`: valida que a edificação pertence ao escopo do cliente autenticado (via `get_current_cliente_responsavel`, BL-30) e, em caso positivo, reaproveita a mesma query/serviço de agregação de `GET /edificacoes/{id}/dashboard` (BL-16) — não duplique a lógica de cálculo, extraia-a para uma função de serviço reutilizável se ainda não estiver isolada do endpoint original.
   - `GET /portal/edificacoes/{id}/acompanhamento`: retorna uma linha do tempo da inspeção em andamento da edificação (visitas e/ou ocorrências mais recentes, status da inspeção, contagem por grau de risco), pensada para o cliente acompanhar o progresso da auditoria sem acessar dados internos de edição.
2. Ambos os endpoints devem responder 404 (Problem Details, DEC-11) se a edificação não existir ou não pertencer ao escopo do cliente autenticado — nunca vazar a existência de uma edificação de outro cliente (RN-14, mitigação A01 OWASP).
3. Aplique a mesma estratégia de cache de BL-16 (Redis, TTL curto) ao endpoint de dashboard do portal, se a query subjacente for a mesma.
4. Escreva testes de integração cobrindo: cliente autenticado vê corretamente o dashboard/acompanhamento da própria edificação; cliente recebe 404 ao tentar acessar edificação de outro contratante; usuário `role="auditor"` não consegue usar as rotas `/portal/*` (403, `require_role`).

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Crie a área `03_frontend/app/portal/` (rota separada do restante do app, visível apenas a usuários `role="cliente"`) com:
   - Uma tela de listagem das edificações do cliente (`GET /portal/edificacoes`, endpoint já criado em BL-30)
   - Uma tela de dashboard por edificação (`GET /portal/edificacoes/{id}/dashboard`), reaproveitando componentes de visualização já criados em BL-16 quando possível
   - Uma tela/seção de acompanhamento da auditoria (`GET /portal/edificacoes/{id}/acompanhamento`) exibindo a linha do tempo/status de forma simples e não técnica (o cliente não é engenheiro)
2. Ajuste o guard de rota (`components/layout/app-shell.tsx` ou equivalente, criado em BL-06) para redirecionar usuários `role="cliente"` para `/portal` em vez das telas internas do auditor, e vice-versa (usuários `auditor` não devem ver `/portal`).
3. Garanta responsividade mobile (RNF-01) — o cliente pode acessar de smartphone.
4. Trate erros da API no formato RFC 7807 (DEC-11).

## Saída Esperada
- Endpoints `/portal/edificacoes/{id}/dashboard` e `/portal/edificacoes/{id}/acompanhamento` implementados, escopados e testados
- Área `03_frontend/app/portal/` funcional com listagem, dashboard e acompanhamento
- Guard de rota diferenciando `auditor` e `cliente`
- Resumo: endpoints criados, como testar com um usuário `role="cliente"` (criado via BL-30), telas implementadas

## Restrições
- NÃO duplique a lógica de cálculo do dashboard já existente em BL-16 — extraia/reaproveite.
- NÃO permita que o endpoint do portal aceite `edificacao_id` fora do escopo do cliente (RN-14).
- Proteja todas as rotas com `require_role("cliente")` (BL-30).
- Leia os arquivos antes de modificá-los.
