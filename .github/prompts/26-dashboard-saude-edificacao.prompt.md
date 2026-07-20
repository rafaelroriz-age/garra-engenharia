---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o Dashboard de saúde por edificação/sistema predial do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-16 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 4 (Incremento LTIP + Dashboard) de `00_docs/projeto/ciclo-de-vida.md`. Depende de BL-14 (CRUD de Ocorrências) para existirem dados a agregar.
Requisito RF-07 de `00_docs/estudo-do-contexto.md`: contagem e proporção de itens Conforme/Não Conforme, distribuição por Grau de Risco (Mínimo/Médio/Crítico), média de gravidade por subsistema (similar ao Power BI de `00_docs/convertidos/COND.md`).
Padrão de projeto CQRS leve (`00_docs/arquitetura.md` Seção 9.13): queries de leitura do dashboard separadas do modelo transacional de escrita, com cache curto.
Estratégia de cache (`00_docs/arquitetura.md` Seção 10.4): agregados do dashboard cacheados em Redis por ~60s por edificação, invalidados ao criar/editar Ocorrência daquela edificação.
Endpoint já previsto em `00_docs/arquitetura.md` Seção 4: `GET /edificacoes/{id}/dashboard`.
Frontend já possui a rota `03_frontend/app/dashboard/page.tsx` (placeholder de scaffold).

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. Implemente uma query de agregação (separada do service transacional de `Ocorrencia`, seguindo CQRS leve) que, para uma edificação, calcule:
   - Contagem e proporção de Ocorrências Conforme/Não Conforme, por sistema predial
   - Distribuição por Grau de Risco (Mínimo/Médio/Crítico), por sistema predial
   - Média de gravidade (GUT) por subsistema
2. Implemente o endpoint `GET /api/v1/edificacoes/{id}/dashboard` retornando esse agregado.
3. Adicione cache Redis com TTL curto (~60s) para o resultado por edificação, e invalide o cache ao criar/editar/remover uma `Ocorrencia` vinculada a essa edificação (via evento no service de Ocorrência, sem acoplar diretamente a lógica de cache ao repository).
4. Escreva testes de integração cobrindo: cálculo correto dos agregados com dados de exemplo, invalidação do cache ao criar nova ocorrência.

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Implemente a tela `03_frontend/app/dashboard/page.tsx` (ou uma tela de dashboard por edificação, acessível a partir do detalhe da edificação de BL-08) consumindo `GET /edificacoes/{id}/dashboard`.
2. Exiba os indicadores com componentes de visualização adequados (gráficos de barra/pizza ou cards de indicador, usando bibliotecas já disponíveis no `03_frontend/package.json` ou shadcn/ui).
3. Organize a visualização por sistema predial, destacando visualmente os sistemas em estado Crítico.
4. Garanta responsividade mobile (RNF-01).
5. Trate erros da API no formato RFC 7807 (DEC-11).

## Saída Esperada
- Endpoint de dashboard com agregações corretas e cache Redis com invalidação funcionando
- Tela de dashboard funcionando, exibindo indicadores por sistema predial
- Resumo: fórmulas de agregação usadas, estratégia de invalidação de cache adotada, como testar manualmente

## Restrições
- NÃO recompute os agregados a cada requisição sem cache — respeitar a estratégia de cache de `00_docs/arquitetura.md` Seção 10.4.
- NÃO desvie do contrato de API definido em `00_docs/arquitetura.md` sem registrar a decisão em `00_docs/projeto/decisoes.md`.
- SEMPRE valide que a edificação existe antes de calcular o dashboard (404 caso contrário).
- Proteja o endpoint com autenticação (BL-06).
- Leia os arquivos antes de modificá-los.
