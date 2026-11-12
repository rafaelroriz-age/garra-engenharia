# Re-medição pós-T28 dos pipelines de geração (R-03)

**Status desta medição: NÃO EXECUTADA — bloqueada por ambiente.**
Nenhum número novo foi produzido. Este documento registra o bloqueio, o estado
verificado do ambiente, a linha de base já existente (T17, medida em 2026-08-05)
e o procedimento a rodar quando o ambiente estiver disponível.

- Tarefa: T73 (papel arquiteto-software), medição e documentação, sem alteração de código de produção nem de testes.
- Data da verificação: 2026-11-12.
- Branch: `worktree-backlog-T73`.
- Risco: R-03 (`00_docs/projeto/riscos.md`).

## 1. Bloqueios encontrados

| # | Item exigido | Situação verificada | Consequência |
|---|---|---|---|
| B1 | Docker Desktop / `docker compose up -d` em `05_infra/` | `docker` não encontrado no PATH (`/usr/local/bin/docker` inexistente). Serviço `com.docker.service` existe com status **Stopped**. | Não há PostgreSQL em `localhost:5433` nem o banco `garra_engenharia_test`. `alembic upgrade head` e a semeadura não foram executados. |
| B2 | WeasyPrint com Pango no host Windows | `python -m app.scripts.benchmark_relatorio_geracao --help` falha ao importar `weasyprint`: `cannot load library 'libpango-1.0-0'`. Não há MSYS2 nem Pango no `/mingw64/bin`. | O script não roda fora do container. O próprio relatório da T17 já registrava isso e por isso mediu dentro do container `garra-backend`. |
| B3 | Ambiente Python do backend | `04_backend/.venv` inexistente. O `python` disponível é o Anaconda 3.14 (`C:\Users\dynatest\anaconda3\python.exe`), que não é o `python:3.12-slim` do `Dockerfile`. | Mesmo sem B1 e B2, a versão do Python e as dependências não correspondem às da medição de referência. |
| B4 | Método de referência citado no briefing | `00_docs/backlog-auto/benchmark-pipelines-finais.md` e `00_docs/backlog-auto/ltip-desempenho.md` **não existem** neste worktree. Em `00_docs/backlog-auto/` há apenas `BACKLOG-MANUAL.md` e `CELULAR.md`. A busca em `git ls-files` também não os encontrou. | O limite de RNF-06 usado aqui é o do próprio `estudo-do-contexto.md` (linha 187), e o método é o do relatório T17 (`00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md`). Não há como verificar a margem de 5 % da T17 da Vistoria Residencial nem o detalhe do `url_fetcher` do T28 contra as fontes citadas no briefing. |

Como o método de referência não foi encontrado, as comparações com a T20 e com a
margem de 5 % da Vistoria Residencial ficam **não verificadas** neste documento.

## 2. Ambiente do host (verificado)

- CPU: Intel Core i7-1355U (13.ª geração), 10 núcleos físicos, 12 lógicos.
- RAM: 15,7 GB.
- SO: Microsoft Windows 11 Pro 10.0.26200.
- Python: Anaconda 3.14 (`C:\Users\dynatest\anaconda3\python.exe`), sem `.venv` do projeto.
- Docker: ausente. Postgres local: ausente (`psql` não encontrado).
- Shell: Git Bash (MSYS). `pytest` e `npm` existem, mas não foram usados porque nenhum código foi alterado e os testes do backend dependem do PostgreSQL.

## 3. Testes

Não foram executados `pytest` nem `ruff check .` em `04_backend`, nem `npm run lint` e `npm run build` em `03_frontend`. Motivo: esta tarefa não altera código, e `pytest` do backend depende do PostgreSQL indisponível (B1). A "Regra de pronto" de tarefas sem código se aplica aqui, e a única alteração é este arquivo de documentação.

## 4. Linha de base existente (T17, não é medição nova)

Fonte: `00_docs/projeto/relatorio-benchmark-geracao-pdf-docx.md`, medido em 2026-08-05 dentro do container `garra-backend`, pior caso de 190 visitas, 570 fotos e 191 páginas. Fotos sintéticas em 2400×1800 px, qualidade 85.

| Cálculo fim-a-fim por job (PDF + DOCX) | Total | RNF-06 (< 60 s) |
|---|---|---|
| Sem otimização de imagem | 112,8 s | Viola |
| Otimizando a cada geração | 83,2 s | Viola |
| Fotos já otimizadas no upload (fix da T17) | 44,2 s | Atende, margem de cerca de 26 % |

Esse cenário de 44,2 s é o único com margem positiva no relatório T17. Ele é
específico do pipeline aproximado de 2026-08-05, síncrono e sem Celery, e não
mede os tipos RFO, LTIP, Cautelar, Residencial e Vistoria da arquitetura final.

## 5. Tabela de resultados pós-T28

**Vazia de propósito.** Nenhum número foi produzido. A tabela deve ser preenchida
quando o item B1 for resolvido.

| Tipo | Formato | Mediana de 3 execuções (s) | Limite RNF-06 (s) | Margem | Veredito |
|---|---|---|---|---|---|
| RFO | PDF | não medido | 60 | não medido | não medido |
| RFO | DOCX | não medido | 60 | não medido | não medido |
| LTIP | PDF | não medido | 60 | não medido | não medido |
| LTIP | DOCX | não medido | 60 | não medido | não medido |
| Cautelar | PDF | não medido | 60 | não medido | não medido |
| Cautelar | DOCX | não medido | 60 | não medido | não medido |
| Residencial (Vistoria) | PDF | não medido | 60 | não medido (T17: 5 %, não verificado) | não medido |
| Residencial (Vistoria) | DOCX | não medido | 60 | não medido | não medido |

Veredito por tipo: **não determinado**. Não há medição nova para nenhum dos cinco tipos.

## 6. Procedimento para executar quando o ambiente estiver pronto

Premissa: Docker Desktop instalado e em execução, e o banco de teste isolado
`garra_engenharia_test`, conforme regra 6 do `BACKLOG.md`.

```powershell
# 1. Subir a stack (Postgres em localhost:5433)
cd 05_infra; docker compose up -d

# 2. Migrações no banco de teste, a partir de 04_backend
cd ..\04_backend; alembic upgrade head

# 3. Template DOCX base (uma vez)
docker exec garra-backend python -m app.scripts.build_rfo_benchmark_docx_template

# 4. Semear o volume da T17 (190 visitas × 3 fotos = 570 fotos, 2400×1800, qualidade 85)
docker exec garra-backend python -m app.scripts.seed_benchmark_rfo --visitas 190 --fotos-por-visita 3 --largura 2400 --altura 1800 --qualidade 85 --reset

# 5. Benchmark (repetir 3 vezes por tipo e formato; usar a mediana)
docker exec garra-backend python -m app.scripts.benchmark_relatorio_geracao --inspecao-id <uuid>
```

Pontos a conferir antes de rodar:

- Os tipos RFO, LTIP, Cautelar e Residencial precisam de seed próprio. O `seed_demo.py` foi citado no briefing, mas não foi localizado em `04_backend/app/scripts/` (há `seed_admin.py`, `seed_benchmark_rfo.py`, `seed_gabarito.py`). Confirmar antes de rodar.
- Usar o mesmo volume de fotos da T17 para todos os tipos, para que a comparação seja válida.
- Registrar a versão do WeasyPrint, do docxtpl e do Python da imagem, além de CPU e RAM do host, junto com os resultados.

## 7. Gargalo provável

Não aplicável nesta rodada, porque nenhuma medição nova foi feita. Pelo
relatório T17, o gargalo conhecido é a otimização de imagem (39 s para 570 fotos
antes da correção) e a `montagem_subdocs` do DOCX (13 s de 15 s no caso
otimizado). Se algum tipo ficar a menos de 20 % de margem na re-medição, o
gargalo deve ser confirmado por medição, não presumido.

## 8. Proposta de ajuste ao R-03 (não aplicada)

O R-03 consta como "Mitigado sob condição" em `00_docs/projeto/riscos.md`, linha
169. Proposta, a ser avaliada pelo integrador no fechamento de lote:

- Manter o status **"Mitigado sob condição"** até que esta re-medição seja executada.
- Acrescentar como condição pendente: medição pós-T28 dos cinco tipos, em Docker, com a mediana de 3 execuções.
- Acrescentar como risco novo: a extensão do `url_fetcher` de fotos para RFO, Cautelar e Residencial (T28) não foi medida, e o DOCX do LTIP ficou sem foto até a T56.
- Não há base nesta rodada para afirmar conformidade com RNF-06 em nenhum tipo.

Esta proposta não foi aplicada em `riscos.md`, conforme a regra de não editar documentos de gestão compartilhados.

## 9. Pendências para o integrador

1. Instalar Docker Desktop e iniciar o serviço, ou fornecer um host com Docker.
2. Confirmar a localização de `ltip-desempenho.md` e de `benchmark-pipelines-finais.md`, que o briefing cita e que não estão no worktree.
3. Confirmar o script de seed para LTIP, Cautelar e Residencial (`seed_demo.py` não foi encontrado).
4. Reexecutar esta tarefa com o ambiente disponível para preencher as seções 2, 5 e 7.
