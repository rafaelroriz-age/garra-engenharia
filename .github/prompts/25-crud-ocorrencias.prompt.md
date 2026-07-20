---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o CRUD de Ocorrências (LTIP) do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-14 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 4 (Incremento LTIP + Dashboard) de `00_docs/projeto/ciclo-de-vida.md`.
Requisito RF-04 de `00_docs/estudo-do-contexto.md`: registro de ocorrências vinculadas a Sistema Predial, Subsistema, Localização, Situação, Classificação, Tipo de Anomalia/Falha, Grau de Risco CMM, Prioridade (0-5), descrição e fotos.
Regras de negócio: RN-03 (toda Ocorrência em LTIP/Vistoria deve ter ao menos 1 Foto vinculada), RN-05 (classificação completa obrigatória: Situação, Classificação, Tipo de Anomalia/Falha quando aplicável, Grau de Risco, Prioridade), RN-10 (cada sistema predial deve ser avaliado individualmente; ausência registrada como "Não se Aplica").
Modelo `Ocorrencia` já existe (BL-04) com campos de classificação como texto livre (sem FK para o gabarito — ver DEC-13). Tabelas de gabarito `tipos_anomalia`, `tipos_falha`, `localizacoes`, `SistemaPredial`, `Subsistema` já populadas (BL-05) e expostas via `/gabarito/*` e `/sistemas-prediais`.
**Esta tarefa NÃO inclui a regra de prioridade automática por Grau de Risco (RN-04)** — essa é a BL-15, bloqueada por B-01 (lacuna #10 sobre sobrescrita manual). Implemente `prioridade` como campo informado manualmente nesta tarefa; a automação será acrescentada quando BL-15 for destravada.

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. Implemente repository e service para `Ocorrencia`.
2. Implemente os endpoints conforme `00_docs/arquitetura.md` Seção 4:
   - `GET /api/v1/inspecoes/{id}/ocorrencias` (filtro por sistema, grau de risco)
   - `POST /api/v1/inspecoes/{id}/ocorrencias`
   - `PUT /api/v1/ocorrencias/{id}`
   - `DELETE /api/v1/ocorrencias/{id}`
3. Valide a classificação completa exigida por RN-05 usando enums/Value Objects (`GrauRisco`, `Situacao`, `Classificacao`, Seção 9.14 de `00_docs/arquitetura.md`) em vez de strings livres nos novos endpoints.
4. Valide RN-03 no momento da emissão do relatório (não necessariamente na criação da ocorrência) — documente essa decisão explicitamente na resposta final, já que a ocorrência pode ser criada antes das fotos serem anexadas.
5. Suporte o valor "Não se Aplica" para sistemas prediais não presentes na edificação (RN-10).
6. Escreva testes de integração cobrindo: criação com classificação completa, rejeição de classificação incompleta, filtro por sistema e por grau de risco, marcação "Não se Aplica".

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Implemente, dentro da rota de inspeção (`03_frontend/app/inspecoes/[id]/`), a listagem de ocorrências com filtros por sistema predial e grau de risco.
2. Implemente formulário de criação/edição de ocorrência consumindo os endpoints de gabarito (`/sistemas-prediais`, `/gabarito/tipos-anomalia`, `/gabarito/tipos-falha`, `/gabarito/localizacoes`) para popular selects.
3. Reutilize o componente de upload de fotos de `24-upload-fotos-lightshot.prompt.md` para vincular fotos à ocorrência.
4. Exiba visualmente quais sistemas prediais ainda não foram avaliados na inspeção atual, incentivando cobertura completa (RN-10).
5. Trate erros da API no formato RFC 7807 (DEC-11).

## Saída Esperada
- Endpoints de Ocorrência implementados, validados (classificação completa via enums) e testados
- Telas de listagem (com filtros) e formulário de ocorrência funcionando, integradas ao gabarito e ao upload de fotos
- Resumo: endpoints criados, enums adotados, como a prioridade manual funciona até BL-15 ser destravada

## Restrições
- NÃO implemente ainda a automação de prioridade por Grau de Risco (RN-04) — isso é escopo exclusivo de BL-15.
- NÃO desvie dos contratos de API definidos em `00_docs/arquitetura.md` sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- SEMPRE valide entradas nos dois lados (frontend e backend).
- Proteja os endpoints com autenticação (BL-06).
- Leia os arquivos antes de modificá-los.
