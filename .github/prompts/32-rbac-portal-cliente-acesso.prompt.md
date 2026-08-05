---
description: "Ativa o agente Engenheiro Backend para implementar o RBAC (perfis auditor/cliente), o vínculo de login do contratante e a base de acesso do Portal do Cliente do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-30 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 4.5 (RBAC, Editor de Anotação de Fotos e Portal do Cliente) de `00_docs/projeto/backlog-tarefas.md`. Pré-requisito de BL-32 e BL-33 (Portal do Cliente — dashboard/acompanhamento e documentos).
Origem: esclarecimento direto do usuário (2026-07-24) — existe um papel "cliente" que precisa acompanhar a auditoria feita pelo "auditor" via dashboard e seus documentos. Isso resolve a lacuna #6 de `00_docs/estudo-do-contexto.md`.
Requisitos/decisões: RF-13, RN-14 (`00_docs/estudo-do-contexto.md`), DEC-18 (`00_docs/projeto/decisoes.md`), ADR-09 (`00_docs/arquitetura.md`).
Base já existente: `Usuario` (`app/models/usuario.py`, BL-06/DEC-15), `Responsavel` (`app/models/responsavel.py`), `Contrato` (`app/models/contrato.py`, hoje só tem `fiscal_id`, sem `contratante_id`). Dependency de autenticação atual: `app/api/deps.py` (`get_current_user`).

## Tarefa
Assuma o papel de **Engenheiro Backend**.

1. Adicione o campo `role` a `Usuario` (`app/models/usuario.py`): string/enum com valores `"auditor"` e `"cliente"`, `nullable=False`, default `"auditor"` (garante que todos os usuários existentes continuem funcionando como auditores sem migração de dados manual).
2. Adicione o campo opcional e único `usuario_id` a `Responsavel` (`app/models/responsavel.py`): FK nullable para `usuarios.id`, permitindo que um Responsavel (ex.: contratante/síndico) também tenha uma conta de login.
3. Adicione o campo opcional `contratante_id` a `Contrato` (`app/models/contrato.py`): FK nullable para `responsaveis.id`, distinto de `fiscal_id` já existente.
4. Gere e aplique a migration Alembic (`alembic revision --autogenerate -m "rbac_role_contratante_bl_30"` a partir de `04_backend/`, depois `alembic upgrade head`).
5. Atualize os schemas Pydantic afetados (`app/schemas/usuario.py`, `app/schemas/responsavel.py`, `app/schemas/contrato.py`) para expor/aceitar os novos campos onde fizer sentido (ex.: `role` em `UsuarioRead`; `contratante_id` em `ContratoCreatePayload`/`ContratoRead`; NÃO adicione `role` a `UsuarioCreate` público — ver restrições).
6. Implemente uma dependency `require_role(*roles: str)` em `app/api/deps.py` (reaproveitando `get_current_user`), retornando 403 (Problem Details, DEC-11) se o usuário autenticado não tiver um dos papéis exigidos.
7. Implemente uma dependency auxiliar `get_current_cliente_responsavel(current_user, db)` que resolve o `Responsavel` vinculado ao usuário autenticado (`Responsavel.usuario_id == current_user.id`) — lança `NotFoundError` (404) se não houver vínculo. Esta dependency será reutilizada pelos endpoints `/portal/*` de BL-32/BL-33.
8. Crie um router vazio `app/api/v1/portal.py` (registrado em `main.py` com prefixo `/api/v1/portal`) só com um endpoint `GET /portal/edificacoes` (lista as Edificações onde `Contrato.contratante_id` aponta para o Responsavel do usuário logado) — os demais endpoints do Portal (`/portal/edificacoes/{id}/dashboard`, `/acompanhamento`, `/relatorios`) ficam para BL-32/BL-33, mas a estrutura do router e a dependency de escopo devem estar prontas aqui.
9. Escreva testes de integração cobrindo: usuário com `role="auditor"` (default) continua acessando normalmente as rotas existentes; `require_role("cliente")` bloqueia usuário auditor (403); `GET /portal/edificacoes` retorna apenas as edificações do contratante logado, nunca as de outro cliente; usuário `cliente` sem `Responsavel` vinculado recebe 404 ao chamar qualquer rota `/portal/*`.

## Saída Esperada
- Migration aplicada com os 3 campos novos (`Usuario.role`, `Responsavel.usuario_id`, `Contrato.contratante_id`)
- `require_role()` e `get_current_cliente_responsavel()` implementados e testados
- Router `/api/v1/portal` criado com `GET /portal/edificacoes` funcional e escopado
- Resumo: campos/migration criados, como popular um usuário de teste com `role="cliente"` vinculado a um `Responsavel` existente (via script ou endpoint), resultado dos testes

## Restrições
- NÃO exponha `role` como campo editável em `POST /auth/register` (schema público de cadastro) — todo cadastro público continua criando `role="auditor"` por padrão; a promoção a `cliente` e o vínculo `usuario_id` em `Responsavel` são operações administrativas (sem endpoint público nesta tarefa — via script/seed ou futura tela administrativa).
- NÃO implemente os endpoints de dashboard/acompanhamento/relatórios do Portal nesta tarefa — apenas a base de RBAC e `GET /portal/edificacoes` (ficam para BL-32/BL-33).
- SEMPRE valide o escopo do cliente a partir de `Responsavel.usuario_id`, nunca aceitando um `edificacao_id`/`contrato_id` fornecido livremente pelo cliente sem checar o vínculo (RN-14, mitigação A01 OWASP).
- Proteja toda rota nova com autenticação (BL-06) e o `require_role` apropriado.
- Leia os arquivos antes de modificá-los.
