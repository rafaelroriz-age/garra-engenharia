---
description: "Ativa o agente Engenheiro Backend para modelar as entidades de dados e criar as migrations Alembic do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-04 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 0 (Fundação Técnica) de `00_docs/projeto/ciclo-de-vida.md`.
Diagrama ER completo (14 entidades) em `00_docs/arquitetura.md` Seção 3. Regras de negócio associadas em `00_docs/estudo-do-contexto.md` Seção 5 (RN-01 a RN-13).
Depende do scaffold do backend (prompt `15-scaffold-backend-fastapi.prompt.md`). Não depende de B-01 nem B-02 — o modelo de dados já está aprovado independentemente das lacunas.

## Tarefa
Assuma o papel de **Engenheiro Backend** e implemente o modelo de dados:

1. Crie os modelos SQLAlchemy 2 (async) em `04_backend/app/models/` para as 14 entidades do diagrama ER de `00_docs/arquitetura.md` Seção 3: `Edificacao`, `Responsavel`, `Contrato`, `ContratoExecutor`, `ContratoNbr`, `Inspecao`, `Visita`, `VisitaMaoObra`, `VisitaMedicao`, `SistemaPredial`, `Subsistema`, `Ocorrencia`, `Foto`, `Relatorio`.
2. Respeite exatamente os campos, tipos e relacionamentos do diagrama ER (incluindo `jsonb` para `documentos_tecnicos`, chaves estrangeiras e cardinalidades).
3. Configure Alembic em `04_backend/alembic/` e gere a migration inicial criando todas as tabelas.
4. Aplique a migration no PostgreSQL do `05_infra/docker-compose.yml` e valide que as tabelas foram criadas corretamente.
5. Crie schemas Pydantic v2 básicos (`04_backend/app/schemas/`) de request/response para cada entidade (apenas os campos do modelo, sem lógica de negócio ainda).
6. Escreva testes de integração (`04_backend/tests/test_models.py`) validando a criação de um registro de cada entidade principal (`Edificacao`, `Contrato`, `Inspecao`) e seus relacionamentos.
7. Rode os testes e corrija falhas antes de concluir.

## Saída Esperada
- Modelos SQLAlchemy para as 14 entidades em `04_backend/app/models/`
- Migration Alembic inicial aplicada com sucesso
- Schemas Pydantic básicos em `04_backend/app/schemas/`
- Testes de integração passando
- Resumo: entidades criadas, comando para rodar migrations, comando para rodar os testes

## Restrições
- NÃO desvie do diagrama ER de `00_docs/arquitetura.md` sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- NÃO implemente ainda regras de negócio (validações RN-XX) nos schemas — isso é feito nas tarefas de CRUD (BL-08 em diante).
- SEMPRE valide entradas nos limites do sistema.
- Leia os arquivos antes de modificá-los.
