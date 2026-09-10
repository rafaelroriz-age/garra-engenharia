---
description: "Ativa o agente Engenheiro Backend (com etapa final de Frontend) para implementar o terceiro perfil de acesso `auxiliar` — escrita limitada a dados de campo e autoria rastreável — no Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-42 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 4.5. Origem: resposta do cliente ao Bloco 1 da sessão de validação de lacunas (2026-09-10, ver `00_docs/projeto/ata-validacao-lacunas.md`) — a lacuna #2 foi respondida com "há auxiliares que também registram ocorrências e fotos em campo".
Requisitos/decisões: RN-18 (`00_docs/estudo-do-contexto.md`), DEC-27 (`00_docs/projeto/decisoes.md`), ADR-14 (`00_docs/arquitetura.md`).
Base já existente (BL-30/DEC-18): `Usuario.role` (`String`, default `"auditor"`), `require_role(*roles)` e `get_current_cliente_responsavel()` em `app/api/deps.py`, router `/api/v1/portal` protegido por `require_role("cliente")`.

## Tarefa
Assuma o papel de **Engenheiro Backend** (etapas 1 a 6) e depois de **Engenheiro Frontend** (etapa 7).

1. Passe a aceitar `"auxiliar"` como terceiro valor de `Usuario.role` (`app/schemas/usuario.py`, `UsuarioCreate.role`). `usuarios.role` já é `String` no banco — não há alteração de tipo nem migration para esse campo.
2. Adicione a coluna `criado_por_id` (FK nullable para `usuarios.id`) a `Visita`, `Ocorrencia` e `Foto`. Nullable porque os registros anteriores à decisão não têm autor conhecido — não inventar retroativamente.
3. Gere a migration Alembic correspondente (`down_revision` = head atual) e aplique com `alembic upgrade head` a partir de `04_backend/`.
4. Defina em `app/api/deps.py` duas dependencies derivadas de `require_role`: uma exclusiva de `auditor` (operações administrativas e emissão) e outra para `auditor` + `auxiliar` (dados de campo e leitura interna).
5. Aplique as dependencies nos routers: **auditor apenas** em criação/edição de Edificação, Contrato, Responsável e documentos técnicos; **auditor + auxiliar** em Inspeção/Visita/Ocorrência/Foto, no dashboard e nas leituras internas de Edificação/Contrato/Responsável. Nenhuma rota interna pode continuar aceitando qualquer usuário autenticado — um `cliente` só acessa `/portal/*`. Os endpoints de dados mestre (`/sistemas-prediais`, `/gabarito/*`) são públicos por decisão anterior e ficam fora desta tarefa.
6. Propague o autor até o repositório: `criar_visita`, `criar` (ocorrência) e `vincular_a_ocorrencia`/`vincular_a_visita` recebem `criado_por_id` do usuário autenticado e o persistem. Exponha o campo nos schemas de leitura correspondentes.
7. No frontend, oculte as ações não permitidas ao `auxiliar` (criar/editar edificação, contrato e responsável) a partir do `role` retornado por `GET /auth/me` — sem jamais tratar isso como controle de acesso, que continua sendo do backend.
8. Escreva testes de integração cobrindo: auxiliar cria visita/ocorrência/foto com sucesso e o `criado_por_id` é gravado; auxiliar recebe 403 ao criar edificação, contrato e responsável; auxiliar recebe 403 em `POST /auth/register`; `cliente` recebe 403 nas rotas internas; auditor continua com acesso total.

## Saída Esperada
- Migration aplicada com `criado_por_id` nas 3 tabelas de dados de campo
- Dependencies de perfil aplicadas em todos os routers internos
- Autoria persistida e exposta nos schemas de leitura
- Testes de autorização por perfil passando
- Resumo: rotas alteradas, como criar um usuário `auxiliar` e resultado dos testes

## Restrições
- NÃO crie um sistema de permissões novo (tabela de permissões, hierarquia de equipes) — apenas o terceiro valor do enum já existente, conforme DEC-27 rejeita explicitamente a alternativa de multi-tenancy.
- NÃO permita que o `auxiliar` gere/emita relatórios, cadastre usuários ou acesse `/portal/*`.
- NÃO torne `criado_por_id` obrigatório (`nullable=False`) — quebraria os registros existentes.
- A ocultação de botões no frontend é usabilidade, nunca a única barreira: toda restrição precisa existir no backend.
- Leia os arquivos antes de modificá-los.
