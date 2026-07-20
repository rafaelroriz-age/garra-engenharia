---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o CRUD de Contratos com múltiplas empresas executoras e NBRs do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-09 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 3 (Incremento RFO) de `00_docs/projeto/ciclo-de-vida.md`. Depende de BL-04 (modelo de dados) e BL-08 (CRUD de Edificações).
Requisitos RF-02 e RF-12 de `00_docs/estudo-do-contexto.md`: contrato com número, tipo de serviço, objeto, prazo, contratante, empresas executoras, engenheiro fiscal, RTE, ARTs e NBRs aplicáveis.
Regras de negócio RN-06 (múltiplas empresas executoras, cada uma com CNPJ/Responsável Legal/RTE próprios) e RN-09 (ARTs de Fiscalização e Execução devem constar no cabeçalho do relatório).
Modelos `Contrato`, `ContratoExecutor`, `ContratoNbr`, `Responsavel` já existem (BL-04). Contratos de API em `00_docs/arquitetura.md` Seção 4 (`/contratos`).
Frontend já possui a rota `03_frontend/app/contratos/page.tsx` (placeholder de scaffold).

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. Implemente repository e service para `Contrato`, incluindo a criação/atualização em cascata de `ContratoExecutor` (N empresas executoras por contrato, RN-06) e `ContratoNbr` (N NBRs por contrato) em uma única transação (Unit of Work, Seção 9.11).
2. Implemente os endpoints conforme `00_docs/arquitetura.md` Seção 4:
   - `GET /api/v1/contratos` (filtro por tipo, status, edificação)
   - `POST /api/v1/contratos` (aceita array de executores e de NBRs no payload)
   - `GET /api/v1/contratos/{id}` (detalhe completo, incluindo executores e NBRs)
   - `PUT /api/v1/contratos/{id}`
3. Valide que ART de Fiscalização é sempre obrigatória e ART de Execução é obrigatória por executor quando aplicável (RN-09).
4. Ao criar um `Contrato`, crie também a `Inspecao` vinculada (relação 1:1 do ER, `Contrato ||--|| Inspecao`), inicializando-a com status apropriado.
5. Escreva testes de integração cobrindo: contrato com uma executora, contrato com múltiplas executoras, validação de campos obrigatórios.

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Implemente a tela de listagem de contratos em `03_frontend/app/contratos/page.tsx`, com filtros por tipo de serviço, status e edificação.
2. Implemente formulário de criação/edição de contrato com suporte a adicionar/remover dinamicamente múltiplas empresas executoras e múltiplas NBRs (arrays no formulário).
3. Implemente a tela de detalhe do contrato exibindo dados completos, executoras e NBRs.
4. Trate erros da API no formato RFC 7807 (DEC-11).
5. Garanta responsividade mobile (RNF-01).

## Saída Esperada
- Endpoints de Contrato (com executores e NBRs em cascata) implementados, validados e testados
- Telas de listagem, criação/edição (com arrays dinâmicos) e detalhe de Contrato funcionando
- Resumo: endpoints criados, decisões de modelagem de payload (formato do array de executores/NBRs), como testar manualmente

## Restrições
- NÃO permita salvar um `Contrato` sem ART de Fiscalização preenchida (RN-09).
- NÃO desvie dos contratos de API definidos em `00_docs/arquitetura.md` sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- SEMPRE valide entradas nos dois lados (frontend e backend), incluindo CNPJ das executoras.
- Proteja os endpoints com autenticação (BL-06).
- Leia os arquivos antes de modificá-los.
