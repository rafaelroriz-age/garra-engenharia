---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o registro de Visitas do RFO (equipe, serviços, medições) do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-10 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 3 (Incremento RFO) de `00_docs/projeto/ciclo-de-vida.md`. Depende de BL-09 (CRUD de Contratos).
Requisito RF-03 de `00_docs/estudo-do-contexto.md`: registro de visitas com data, serviços executados, equipe presente por função e quantidade, medições parciais, observações e fotos.
Regras de negócio RN-01 (um RFO tem exatamente um Contrato e N Visitas) e RN-02 (cada Visita deve registrar data, serviços executados, equipe presente e observações).
Modelos `Visita`, `VisitaMaoObra`, `VisitaMedicao` já existem (BL-04). Contratos de API em `00_docs/arquitetura.md` Seção 4 (`/inspecoes`, `/visitas`).
Frontend já possui a rota `03_frontend/app/inspecoes/[id]/` (placeholder de scaffold). Upload de fotos vinculado a Visitas é tratado separadamente em BL-11 (`24-upload-fotos-lightshot.prompt.md`) — esta tarefa cobre apenas o registro textual/numérico da visita.

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. Implemente repository e service para `Visita`, `VisitaMaoObra` e `VisitaMedicao`.
2. Implemente os endpoints conforme `00_docs/arquitetura.md` Seção 4:
   - `POST /api/v1/inspecoes/{id}/visitas` (cria visita)
   - `PUT /api/v1/visitas/{id}` (atualiza visita — equipe, serviços, medições)
   - `POST /api/v1/visitas/{id}/mao-obra` (adiciona registro de mão de obra)
   - `POST /api/v1/visitas/{id}/medicoes` (adiciona medição)
   - `GET /api/v1/inspecoes/{id}` (detalhe da inspeção com visitas, se ainda não implementado)
3. Garanta que `Visita.seq_numero` seja atribuído automaticamente em ordem sequencial por inspeção (uma visita por dia de obra acompanhado, RN-01).
4. Valide que uma Visita não pode ser criada sem data e sem ao menos uma referência a serviços executados (RN-02).
5. Escreva testes de integração cobrindo: criação de visita, adição de mão de obra, adição de medição, sequenciamento automático de `seq_numero`.

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Implemente, dentro de `03_frontend/app/inspecoes/[id]/`, a listagem de visitas da inspeção (ordenadas por `seq_numero`/data).
2. Implemente formulário de criação/edição de visita com: data, serviços executados (texto), observações, e sub-formulários dinâmicos para equipe (função + quantidade) e medições (descrição + quantidade + unidade).
3. Trate erros da API no formato RFC 7807 (DEC-11).
4. Garanta usabilidade mobile em campo (RNF-01) — este formulário é preenchido predominantemente em smartphone durante a visita à obra.

## Saída Esperada
- Endpoints de Visita, Mão de Obra e Medição implementados, validados e testados
- Tela de listagem e formulário de registro de visita funcionando, otimizados para uso mobile
- Resumo: endpoints criados, como o sequenciamento de visitas funciona, como testar manualmente

## Restrições
- NÃO permita registrar uma Visita sem data (RN-02).
- NÃO desvie dos contratos de API definidos em `00_docs/arquitetura.md` sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- SEMPRE valide entradas nos dois lados (frontend e backend).
- Proteja os endpoints com autenticação (BL-06).
- Leia os arquivos antes de modificá-los.
