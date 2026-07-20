---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o CRUD completo de Edificações do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-08 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 3 (Incremento RFO) de `00_docs/projeto/ciclo-de-vida.md`.
Requisito RF-01 de `00_docs/estudo-do-contexto.md`: cadastro de edificação com nome, endereço, tipologia, sistema construtivo, descrição de pavimentos, área total, proprietário/síndico e documentos técnicos.
Modelo `Edificacao` já existe (BL-04, `00_docs/arquitetura.md` Seção 3) com migration aplicada. Contratos de API previstos em `00_docs/arquitetura.md` Seção 4 (`/edificacoes`).
Frontend já possui a rota `03_frontend/app/edificacoes/page.tsx` (placeholder de scaffold). Não depende de B-01 nem B-02 — telas de cadastro são genéricas.

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. Implemente o repository (`app/repositories/edificacao_repository.py`) e o service (`app/services/edificacao_service.py`) para `Edificacao`.
2. Implemente os endpoints conforme `00_docs/arquitetura.md` Seção 4:
   - `GET /api/v1/edificacoes` (paginado, filtro por nome/endereço)
   - `POST /api/v1/edificacoes`
   - `GET /api/v1/edificacoes/{id}` (com histórico de contratos vinculados)
   - `PUT /api/v1/edificacoes/{id}`
3. Valide entradas com Pydantic (campos obrigatórios de RF-01) e trate erros conforme RFC 7807 (DEC-11).
4. Suporte upload de documentos técnicos (projetos, ARTs) associados à edificação — pode reaproveitar o serviço de storage se `20-storage-service-minio.prompt.md` já tiver sido executado; caso contrário, registre como pendência para BL-07.
5. Escreva testes de integração para os 4 endpoints (casos de sucesso e de erro/validação).

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Implemente a tela de listagem de edificações em `03_frontend/app/edificacoes/page.tsx`, consumindo `GET /edificacoes` com paginação e busca.
2. Implemente formulário de criação/edição de edificação (modal ou rota dedicada), consumindo `POST`/`PUT`, com validação client-side espelhando as regras do backend.
3. Implemente a tela de detalhe da edificação exibindo o histórico de contratos.
4. Trate erros da API no formato RFC 7807 (DEC-11) exibindo mensagens de campo específicas.
5. Garanta responsividade mobile (RNF-01) usando os componentes shadcn/ui já disponíveis em `03_frontend/components/ui/`.

## Saída Esperada
- Endpoints de Edificação implementados, validados e testados
- Telas de listagem, criação/edição e detalhe de Edificação funcionando e responsivas
- Resumo: endpoints criados, rotas de frontend criadas, como testar manualmente o fluxo completo

## Restrições
- NÃO exponha dados sensíveis sem autenticação — proteja os endpoints com a dependency `get_current_user` (BL-06).
- NÃO desvie dos contratos de API definidos em `00_docs/arquitetura.md` sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- SEMPRE valide entradas nos dois lados (frontend e backend).
- Leia os arquivos antes de modificá-los.
