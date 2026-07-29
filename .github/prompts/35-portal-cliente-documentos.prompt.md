---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar a listagem e o download de documentos/relatórios no Portal do Cliente do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-33 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 4.5 (RBAC, Editor de Anotação de Fotos e Portal do Cliente). Depende de BL-30 (RBAC + router `/portal` base, `32-rbac-portal-cliente-acesso.prompt.md`).
Origem: esclarecimento direto do usuário (2026-07-24) — o "cliente" acompanha a auditoria através, entre outras coisas, dos seus documentos. Requisitos/decisões: RF-13, RN-14 (`00_docs/estudo-do-contexto.md`), DEC-18 (`00_docs/projeto/decisoes.md`), ADR-09 e Seção 4 "Portal do Cliente" (`00_docs/arquitetura.md`).
**Atenção:** o download real do PDF/DOCX gerado depende do motor de geração de relatórios (BL-12/BL-13), ainda bloqueado por B-02 (templates `.docx` não recebidos do cliente, ver `00_docs/projeto/status.md`). Esta tarefa deve implementar a listagem e a estrutura de download de forma completa e correta, mas o download efetivo só retornará arquivo quando BL-12/BL-13 estiverem concluídas — trate a ausência de relatório emitido como um estado normal da tela (lista vazia), não como erro.

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. No router `app/api/v1/portal.py` (criado em BL-30), implemente:
   - `GET /portal/relatorios`: lista os `Relatorio` (ver `app/models/relatorio.py`) vinculados às Inspeções/Contratos das Edificações em que o cliente autenticado é contratante (via `Contrato.contratante_id`, BL-30), com paginação, incluindo apenas relatórios com status "emitido"/concluído (nunca rascunhos internos do auditor).
   - `GET /portal/relatorios/{id}/download/pdf` e `GET /portal/relatorios/{id}/download/docx`: valida que o relatório pertence ao escopo do cliente autenticado antes de delegar ao `StorageClient` (BL-07) para gerar a URL pré-assinada de download (ou fazer o proxy do arquivo, seguindo o mesmo padrão já usado pelos endpoints internos de download, se existentes).
2. Todos os endpoints devem responder 404 (Problem Details, DEC-11) se o relatório não existir, não estiver emitido, ou não pertencer ao escopo do cliente — nunca vazar a existência de um relatório de outro cliente (RN-14, mitigação A01 OWASP).
3. Escreva testes de integração cobrindo: cliente vê apenas os relatórios emitidos das próprias edificações; cliente não vê relatórios de outro contratante (404); cliente não vê relatórios não emitidos/rascunho; download aciona a validação de escopo antes de chamar o storage.

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Na área `03_frontend/app/portal/` (criada em BL-32), adicione uma tela de listagem de documentos (`GET /portal/relatorios`) com nome do documento, tipo (RFO/LTIP/etc.), edificação, versão (RF-11) e data de emissão.
2. Implemente os botões de download (PDF/DOCX), consumindo `GET /portal/relatorios/{id}/download/pdf` e `/docx`.
3. Trate o estado vazio (nenhum relatório emitido ainda) com uma mensagem clara ao cliente (ex.: "Nenhum documento emitido até o momento"), já que isso é esperado enquanto BL-12/BL-13 não estiverem concluídas.
4. Garanta responsividade mobile (RNF-01).
5. Trate erros da API no formato RFC 7807 (DEC-11).

## Saída Esperada
- Endpoints `/portal/relatorios` e `/portal/relatorios/{id}/download/{pdf,docx}` implementados, escopados e testados
- Tela de documentos do Portal do Cliente funcional, com estado vazio tratado
- Resumo: endpoints criados, como testar com um usuário `role="cliente"` e um `Relatorio` de teste emitido (via seed/fixture, já que a geração real ainda depende de B-02)

## Restrições
- NÃO exponha relatórios com status diferente de "emitido"/concluído ao cliente.
- NÃO permita que o endpoint de download aceite um `relatorio_id` fora do escopo do cliente (RN-14).
- NÃO bloqueie esta tarefa esperando a conclusão de BL-12/BL-13 — implemente a estrutura completa e valide com dados de teste/seed.
- Proteja todas as rotas com `require_role("cliente")` (BL-30).
- Leia os arquivos antes de modificá-los.
