# Execução dos testes com banco (R-14)

Registro da tarefa que executa os testes do backend que dependem de PostgreSQL, sem alterar código. Referência: riscos R-13 / R-14 em `00_docs/projeto/riscos.md`; efeito colateral R-15 (queda por `asyncio.run`).

## Resultado: testes NÃO executados

Os testes com banco **não rodaram** nesta execução. Nenhum resultado foi inventado. Causa: ambiente sem Docker e sem o serviço exigido no ar.

## Data e ambiente

- Data: 2026-11-11
- Worktree: `.claude/worktrees/backlog-T52` (branch `worktree-backlog-T52`)
- Sistema: Windows 11 Pro 10.0.26200
- Docker: **não instalado** (`docker` ausente no PATH do Bash e do PowerShell)
- Python / pytest / alembic / ruff: não verificados (a execução parou antes, na etapa 1)

## Passos executados

1. **Verificação dos serviços (`05_infra/docker-compose.yml`)**
   - `docker compose ps`: não executado, pois o comando `docker` não existe.
   - `docker compose up -d`: não executado, pelo mesmo motivo.
   - Teste de porta (TCP localhost):

     | Porta | Serviço esperado | Situação |
     |---|---|---|
     | 5433 | PostgreSQL (compose) | fechada |
     | 9000 | MinIO (compose) | fechada |
     | 5432 | (não documentado no compose) | aberta |

   - A porta 5432 responde, mas não é a porta do compose do projeto. Não foi usada: testar contra um banco desconhecido geraria resultado sem valor e poderia tocar dados de outro ambiente.

2. **`alembic upgrade head`**: não executado (depende do banco na 5433).

3. **Testes por arquivo** (um por vez, por causa de R-15): não executados.
   - `tests/test_ocorrencias_regras.py`
   - `tests/test_visitas*.py`
   - `tests/test_fotos*.py`
   - `tests/test_relatorios_rfo_api.py`
   - `tests/test_rfo_contexto.py`
   - `tests/test_portal_cliente.py`

   Contagens (passed / failed / error / skipped): **N/A**, nenhum teste rodou.

## Falhas

Nenhuma falha foi observada, porque nenhum teste executou. Não há causa provável a classificar (ambiente x código).

## Correções propostas (não aplicadas)

1. **Ambiente (prioridade alta):** instalar Docker Desktop no host de execução e subir o compose de `05_infra/`:
   ```
   cd 05_infra
   docker compose up -d
   docker compose ps
   ```
   Confirmar PostgreSQL em `localhost:5433` e MinIO em `localhost:9000` antes de repetir esta execução.
2. **Agente de background:** se a execução rodar em ambiente sem Docker, esta tarefa não tem como concluir. Propõe-se que ela seja agendada apenas em máquina com Docker, ou que o runner use um PostgreSQL de serviço no mesmo host, com a `DATABASE_URL` documentada no `.env.example` do backend.
3. **Configuração de porta:** esclarecer se a `DATABASE_URL` de teste aponta para 5433 (compose). Hoje a porta 5432 responde localmente, o que pode induzir a rodar contra um banco errado. Sugere-se documentar a porta exata no `.env.example` do backend (sem alterar o arquivo nesta tarefa).
4. **R-15 (`asyncio.run`):** manter a execução por arquivo, como pedido, até o problema ser corrigido em código (tarefa separada).

## Decisões propostas (para o integrador, não aplicadas)

- Proposta: tratar a execução com banco como pré-requisito de ambiente, com checagem de Docker e de portas no início de qualquer tarefa que dependa de banco, falhando explicitamente em vez de registrar "passou".
- Esta tarefa não altera `00_docs/projeto/decisoes.md`, `riscos.md`, `status.md` nem o backlog. O status de R-14 permanece aberto.

## Próximo comando

Com Docker instalado, a partir da raiz do worktree:

```
docker compose -f 05_infra/docker-compose.yml up -d
```

Depois, a partir de `04_backend/`: `alembic upgrade head` e, um arquivo por vez, `pytest tests/<arquivo>`.
