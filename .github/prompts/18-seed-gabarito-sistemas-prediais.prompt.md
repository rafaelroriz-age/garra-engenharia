---
description: "Ativa o agente Engenheiro Backend para popular os dados mestre (gabarito de sistemas prediais, subsistemas, classificações e localizações) do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-05 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 0 (Fundação Técnica) de `00_docs/projeto/ciclo-de-vida.md`.
Requisito RF-10 de `00_docs/estudo-do-contexto.md`: gabarito de sistemas prediais pré-carregado.
Fonte definitiva dos dados mestre: `00_docs/convertidos/RFO_INSPECAO.md` (gabarito extraído de planilha XLSM), contendo: 15 Sistemas Prediais, seus Subsistemas, Situação (Conforme/Não Conforme), Classificação (Anomalia/Falha/Anomalia+Falha/Não se Aplica), Tipo de Anomalia, Tipo de Falha, Grau de Risco (Mínimo/Médio/Crítico), Prioridade (0-5) e Localizações padrão.
Depende dos modelos de dados (prompt `17-modelagem-dados-migrations.prompt.md`). Não depende de B-01 nem B-02 — o gabarito já é a fonte definitiva conforme premissa 6 de `00_docs/projeto/escopo.md`.

## Tarefa
Assuma o papel de **Engenheiro Backend** e implemente o carregamento dos dados mestre:

1. Leia `00_docs/convertidos/RFO_INSPECAO.md` e extraia de forma estruturada:
   - Os 15 Sistemas Prediais (ex.: Aberturas e Fechamentos, Acessibilidade, Circulações, Cobertura e Telhamento, Elementos Estruturais Aparentes, Impermeabilização, Instalações de Gás, Instalações de Telecomunicação, Revestimentos, Sistema de Esquadrias, Prevenção e Combate a Incêndios, SPDA, Sistemas Elétricos, Sistemas Hidrossanitários, Vedações Verticais).
   - Os Subsistemas de cada Sistema Predial.
   - Tipos de Anomalia, Tipos de Falha, Tipos de Anomalia/Falha combinados.
   - Localizações padrão listadas no gabarito.
2. Crie um script de seed (`04_backend/app/scripts/seed_gabarito.py` ou migration de dados Alembic) que popula as tabelas `SistemaPredial` e `Subsistema` (do modelo criado no prompt 17) com esses dados, respeitando a ordem definida no gabarito (campo `ordem`).
3. Para Tipos de Anomalia/Falha e Localizações que não tenham tabela própria no modelo ER, avalie se cabem como tabelas de domínio adicionais ou enums — registre a decisão em `00_docs/projeto/decisoes.md` caso desvie do modelo ER original.
4. Implemente os endpoints de leitura de dados mestre conforme `00_docs/arquitetura.md` Seção 4 ("Dados Mestre"): `GET /api/v1/sistemas-prediais`, `GET /api/v1/gabarito/tipos-anomalia`, `GET /api/v1/gabarito/tipos-falha`, `GET /api/v1/gabarito/localizacoes`.
5. Escreva testes validando que o seed populou os 15 sistemas prediais com seus subsistemas e que os endpoints retornam os dados corretamente.
6. Rode o seed no ambiente local e valide via `GET /api/v1/sistemas-prediais`.

## Saída Esperada
- Script de seed do gabarito de sistemas prediais/subsistemas
- Endpoints de dados mestre funcionando (`/sistemas-prediais`, `/gabarito/tipos-anomalia`, `/gabarito/tipos-falha`, `/gabarito/localizacoes`)
- Testes passando validando a contagem de sistemas e subsistemas carregados
- Resumo: como rodar o seed, endpoints criados, exemplo de resposta

## Restrições
- NÃO invente sistemas/subsistemas fora do gabarito de `RFO_INSPECAO.md` — é a fonte definitiva (premissa 6 do escopo).
- NÃO torne o gabarito hardcoded no código sem possibilidade de edição futura — mantenha como dados em tabelas (RF-10 exige "dados mestre editáveis").
- SEMPRE valide entradas nos endpoints.
- Leia os arquivos antes de modificá-los.
