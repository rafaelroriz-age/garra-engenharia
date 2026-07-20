---
description: "Ativa o agente Engenheiro de Software (com apoio do Engenheiro DevOps) para realizar o benchmark de geração de PDF/DOCX do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-22 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 6/7 (Integração, Testes e Deploy) de `00_docs/projeto/ciclo-de-vida.md`. Depende de BL-12/BL-13 (pipeline de geração de PDF/DOCX do RFO) estarem implementados.
Requisito RNF-06 de `00_docs/estudo-do-contexto.md`: relatórios de até 200 páginas com 150+ fotos devem ser gerados em menos de 60 segundos.
Risco R-03 (`00_docs/projeto/riscos.md`) associado a esse requisito.
Arquitetura de processamento assíncrono via Celery/Redis (ADR-06, `00_docs/arquitetura.md` Seção 10.2): timeout de job, política de retry, idempotency key.

## Tarefa
Assuma o papel de **Engenheiro de Software** (com apoio do **Engenheiro DevOps** para infraestrutura de teste) e:

1. Prepare um conjunto de dados de teste representativo do pior caso: uma inspeção com volume equivalente a 200 páginas de relatório e 150+ fotos (pode ser gerado por script de seed, reaproveitando/estendendo `04_backend/app/scripts/seed_gabarito.py` como referência de padrão de seed).
2. Meça o tempo de geração do pipeline PDF (WeasyPrint) e DOCX (docxtpl) separadamente, do disparo do job até a conclusão (`RELATORIO.status = concluido`), incluindo o tempo de leitura de fotos do MinIO.
3. Identifique gargalos (ex.: compressão/redimensionamento de imagens antes da renderização, tamanho do HTML intermediário, I/O do storage) e implemente otimizações necessárias para ficar dentro do limite de 60s (RNF-06).
4. Documente os resultados do benchmark (tempo medido, hardware/ambiente utilizado, otimizações aplicadas) em um relatório dentro de `00_docs/projeto/` (ex.: seção nova em `riscos.md` ou arquivo dedicado, a critério do agente).
5. Caso o limite de 60s não seja atingido mesmo após otimizações, registre isso como risco atualizado em `00_docs/projeto/riscos.md` com plano de mitigação (ex.: aumentar o timeout de job, paralelizar renderização de fotos, considerar geração incremental).

## Saída Esperada
- Resultados de benchmark documentados (tempo de geração PDF e DOCX, ambiente de teste)
- Otimizações implementadas no pipeline de geração, se necessárias
- Atualização de `00_docs/projeto/riscos.md` caso o requisito RNF-06 não seja atingido integralmente
- Resumo: tempo final medido, principais gargalos encontrados, otimizações aplicadas

## Restrições
- NÃO afirme conformidade com RNF-06 sem medição real reproduzível.
- NÃO otimize prematuramente sem antes medir onde está o gargalo real.
- Leia os arquivos antes de modificá-los.
