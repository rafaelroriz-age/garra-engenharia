# E2E de Visitas, Ocorrências e Upload de fotos (BL-21, tarefa T75)

Reteste em navegador (Playwright/Chromium) dos frontends de Visitas (BL-10), Upload de fotos (BL-11) e Ocorrências (BL-14) depois das mudanças de regra das tarefas T21 (visitas), T19 (fotos) e T08 (ocorrências). `status.md`, backlog e decisões **não** foram editados. Nenhum bug real do produto foi encontrado.

## O que foi criado (specs existentes intactos)

| Arquivo | Cobertura |
|---|---|
| `03_frontend/e2e/visitas-ocorrencias.spec.ts` | **Visita (RFO):** cria pela UI; data futura (`2099-01-01`) rejeitada com "não pode ser futura"; segunda visita no mesmo dia rejeitada com "Já existe uma visita nesta inspeção na data …" (a lista segue com 1 visita); edita serviços e observações e confirma após `reload`. **Ocorrência (LTIP):** cria com sistema, subsistema, localização, situação, classificação (Anomalia + tipo), grau de risco; edita para Falha/Crítico; confere a linha na lista e, via API, os enums canônicos `NAO_CONFORME`/`FALHA`/`CRITICO`. A ocorrência é apagada no `finally` (`DELETE /ocorrencias/{id}`). |
| `03_frontend/e2e/fotos-upload.spec.ts` | Foto por upload manual (input de arquivo + editor de anotação) e foto por colagem (`navigator.clipboard.read()` simulado por `addInitScript`, pois o Chromium headless não concede leitura real), ambas vinculadas à mesma visita; as duas aparecem na seção "Fotos da visita" e continuam após `reload`. Imagem PNG 1x1 gerada no teste (`helpers.ts`); nada de `01_output-context/`. Fotos apagadas no `finally` (`DELETE /fotos/{id}`). |
| `03_frontend/e2e/inspecao-helpers.ts` | Apoio novo: cria edificação e contrato (RFO ou LTIP) pela UI e devolve o id da inspeção; `apagarRecursos` para a limpeza. |

Nomes únicos por execução (`nomeUnico`, `Date.now()`). A API não tem DELETE para edificação, contrato, inspeção nem visita: esses registros (marcador "E2E") permanecem no banco usado.

Observação: o enunciado cita `foto-origem.spec.ts` e `edificacoes-contratos.spec.ts`. O worktree nasceu de um commit antigo (14ead2f) sem eles; a branch foi avançada por fast-forward local até `main` (ef57fd0) antes de qualquer alteração. `foto-origem.spec.ts` mocka toda a API; como a T19 exige que a `storage_key` exista no bucket, o upload aqui usa o MinIO real em vez de mock.

## Ambiente e resultado

- **Sem Docker** (`docker: command not found`). Usei o PostgreSQL e o MinIO que já escutam em `localhost:5433` e `localhost:9000`.
- **Banco de dev (`garra_engenharia`) não pôde migrar:** `alembic upgrade head` aborta na migration `uq_relatorios_inspecao_tipo_versao` com 1 grupo duplicado em `relatorios` (`inspecao_id=22db6dc2-…`, `tipo=RFO`, `versao=BENCH-01`, 2 registros). A própria migration manda limpar à mão; não alterei dados existentes. Pendência do dono do banco (linhas do benchmark `seed_benchmark_rfo`).
- **Contornei com um banco novo e descartável** no mesmo servidor, `garra_e2e_t75` (criado por mim; pode ser removido com `DROP DATABASE garra_e2e_t75`): `alembic upgrade head` até `c6f2a8d4e1b9` sem erro, `python -m app.scripts.seed_admin`, `python -m app.scripts.seed_gabarito` (15 sistemas, 113 subsistemas).
- **Backend** a partir deste worktree em `:8001` (uvicorn, venv com `--system-site-packages` e `bcrypt<4.1`, porque o Python global tem bcrypt 5.0.0 e `seed_admin` quebra com "password cannot be longer than 72 bytes"; o `requirements.txt` já fixa `bcrypt<4.1`). **Frontend** `next start -p 3057` com `NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1`.
- Cuidado: as portas 3000/3001/8000 já estavam ocupadas por instâncias de outros processos (build antigo). A 1ª execução, na 3001, bateu num frontend antigo que enviava `origem: "upload"` e levou 422; foi falso positivo de ambiente, não bug do código atual.

Comandos (a partir de `03_frontend/`):

```
npm ci
npm run lint            -> ✔ No ESLint warnings or errors
npm run build           -> sucesso
E2E_BASE_URL=http://localhost:3057 E2E_API_BASE_URL=http://localhost:8001/api/v1 \
  npx playwright test e2e/visitas-ocorrencias.spec.ts e2e/fotos-upload.spec.ts
  -> 3 passed (40.7s): fotos-upload (18.0s), Visitas (8.6s), Ocorrências (10.8s)
```

Não rodei `pytest`/`ruff` (nenhum código do backend foi alterado) nem a suíte e2e inteira.

## Achados

- Nenhum bug real do produto. Regras revalidadas na UI: data futura e segunda visita no mesmo dia (T21), `storage_key` gerada pelo servidor e `origem` em `upload_manual`/`lightshot` (T19, DEC-43), enums de ocorrência (T08).
- Lacuna de teste: o 422 de data futura usa o texto do validador Pydantic; se a mensagem mudar, o regex `/não pode ser futura/i` precisa acompanhar.
- Proposta de fechamento de lote: registrar em `status.md` (item 9) que o reteste em navegador de BL-10/BL-11/BL-14 foi feito; anotar o duplicado `BENCH-01` em `relatorios` como bloqueio de migration no banco de dev compartilhado (`riscos.md`).
