---
description: "Ativa o agente Engenheiro de Software (ou Engenheiro Backend) para realizar a revisão de segurança OWASP Top 10 do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-23 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 6/7 (Integração, Testes e Deploy) de `00_docs/projeto/ciclo-de-vida.md`. Depende das etapas anteriores estarem implementadas (auth, upload de fotos, CRUDs principais).
Requisito RNF-05 de `00_docs/estudo-do-contexto.md`: autenticação segura e proteção de dados de clientes.
Mapeamento OWASP Top 10:2021 já registrado em `00_docs/arquitetura.md` Seção 10.1, cobrindo A01 a A10 com as mitigações arquiteturais previstas. Esta tarefa audita se a implementação real corresponde ao que foi projetado.

## Tarefa
Assuma o papel de **Engenheiro de Software** (ou **Engenheiro Backend**, se a revisão focar exclusivamente no backend) e:

1. Percorra cada categoria da tabela de `00_docs/arquitetura.md` Seção 10.1 (A01 a A10) e verifique, no código já implementado, se a mitigação prevista foi de fato aplicada:
   - **A01** — toda query filtra por proprietário/posse? IDs são UUID não sequenciais?
   - **A02** — HTTPS obrigatório, bcrypt em senhas, segredos fora do repositório, URLs do MinIO pré-assinadas com expiração curta?
   - **A03** — 100% das queries usam bind parameters do SQLAlchemy (sem concatenação de SQL)?
   - **A04** — idempotency key no job de geração, RN-08 (bloqueio de emissão sem campos obrigatórios) implementado?
   - **A05** — CORS restrito, `/docs`/`/redoc` desabilitados fora de `development`?
   - **A06** — lockfiles versionados, dependências sem CVEs conhecidas de alta severidade (rodar auditoria: `pip-audit`/`npm audit`)?
   - **A07** — rate limiting em `/auth/login`, JWT de curta duração implementados (ver BL-06)?
   - **A08** — validação de mime-type real (magic bytes) e reprocessamento via Pillow no upload de fotos (ver BL-11)?
   - **A09** — logging estruturado com `request_id`/`user_id`/`job_id`, campos de auditoria nas entidades sensíveis?
   - **A10** — nenhum endpoint aceita URL externa fornecida pelo cliente para buscar conteúdo?
2. Para cada item não conforme encontrado, corrija diretamente no código (se for um ajuste pequeno e local) ou registre como item de backlog com prioridade e risco associado (se exigir mudança maior de arquitetura).
3. Execute uma auditoria automatizada de dependências (`pip-audit` no backend, `npm audit` no frontend) e trate vulnerabilidades de severidade alta/crítica.
4. Documente os resultados da revisão (o que foi encontrado, o que foi corrigido, o que ficou pendente) em `00_docs/projeto/riscos.md` ou em um relatório dedicado dentro de `00_docs/projeto/`.

## Saída Esperada
- Checklist OWASP Top 10 revisado item a item, com status de conformidade
- Correções aplicadas para os itens não conformes de baixo esforço
- Relatório de auditoria de dependências (`pip-audit`/`npm audit`) com vulnerabilidades tratadas
- Resumo: itens corrigidos, itens pendentes com justificativa e prioridade

## Restrições
- NÃO ignore vulnerabilidades de severidade alta/crítica encontradas na auditoria de dependências sem justificativa registrada.
- NÃO faça mudanças arquiteturais grandes sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- Leia os arquivos antes de modificá-los.
