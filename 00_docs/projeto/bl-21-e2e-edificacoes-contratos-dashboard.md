# BL-21 — E2E de edificações, contratos e dashboard (frontend)

Status.md (próximos passos, item 9): validação ponta a ponta em navegador. Specs novos, sem alterar os existentes.

## O que foi coberto

`03_frontend/e2e/edificacoes-contratos.spec.ts` (RF-01, RF-02, RN-06, RN-09; BL-08/BL-09)
1. Login como auditor; lista de edificações; criar edificação pela UI e vê-la na lista; busca por nome, por endereço e sem resultado (estado vazio); abertura do detalhe.
2. Lista de contratos; validação client-side da ART de Fiscalização (RN-09); criação de contrato com **2 empresas executoras** e **2 NBRs** pela UI (resposta 201 com 2 executores, 2 NBRs e Inspeção 1:1); filtros de edificação, tipo de serviço e status (coerentes mantêm, incoerentes escondem); detalhe com as duas executoras e as duas NBRs.

`03_frontend/e2e/dashboard.spec.ts` (RF-07; BL-16)
- Semeia via API: edificação nova, contrato (origina a Inspeção) e 3 ocorrências no mesmo sistema predial (1 CONFORME/MÍNIMO, 1 NÃO CONFORME/MÉDIO, 1 NÃO CONFORME/CRÍTICO, GUT gravidade 1/3/5). Confere o agregado da API e a tela: total 3, Conforme 1 (33%), Não Conforme 2 (67%), 1 crítico, "1 conforme · 2 não conforme", "1 mínimo, 1 médio, 1 crítico", barra de progresso 33% e gravidade GUT média 3.0 do subsistema.
- `app/scripts/seed_demo.py` **não existe** no repositório; o seed foi feito pela API, com nomes "E2E" únicos por execução.

## Limpeza
Ocorrências criadas são apagadas (`DELETE /ocorrencias/{id}`). A API não tem DELETE para edificação, contrato e responsável, então esses registros "E2E" permanecem no banco de dev.

## Resultado
`3 passed (18.7s)` (Playwright, chromium, contra o PostgreSQL de 05_infra em localhost:5433).
`npm run lint`: sem avisos. `npx tsc --noEmit`: sem erros. `npm run build`: ok. Specs existentes (rfo, ltip, relatorio, portal) **não foram executados** nem alterados.

## Bug real na UI (não corrigido)
- **Seletor de edificação capado em 100, sem ordenação**: o formulário de contrato e o filtro da lista de contratos carregam `GET /edificacoes?page=1&page_size=100`, e `listar` não tem `order_by`. Com mais de 100 edificações no banco (138 no dev), a recém-criada não aparece no `<select>`, e é impossível criar contrato por ela pela UI ou filtrar por ela. Isso também afeta o `rfo.spec.ts`/`ltip.spec.ts` existentes em bancos grandes. No spec, quando a opção falta, o contrato é criado via API (anotação `bug-ui`) e os filtros são verificados na API; nesta execução foi esse o caminho, então o preenchimento do formulário com 2 executoras/2 NBRs **pela UI** ficou escrito mas não exercitado. Sugestão: ordenar por nome/criação desc e/ou trocar o `<select>` por busca (autocomplete).
- Dashboard: o seletor usa `GET /edificacoes` (20 por página, sem `page_size`), então só lista as 20 primeiras; a navegação direta por `?edificacaoId=` funciona e é o que o teste usa.

## Ambiente (como rodar e o que deu errado)
- O backend já no ar em :8000 usa `bcrypt 5.0.0`, incompatível com o passlib e com o pin `bcrypt>=4.0,<4.1` do requirements: `seed_admin` e `POST /auth/register` falham. Criei venv próprio (Python 3.14; Pillow 13 porque não há wheel do pin `<11`) e subi o backend em **:8001** (`BACKEND_CORS_ORIGINS=http://localhost:3001`) e o frontend em **:3001** (`NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1 npm run build && npx next start -p 3001`).
- `python -m app.scripts.seed_admin` criou o admin de bootstrap no banco de dev (idempotente).
- `alembic upgrade head` falhou: o banco compartilhado está numa revisão (`f7c2a9d4e6b1`) que esta branch não tem. Não alterei o schema; as rotas usadas funcionaram.
- `npm ci` teve OOM/ENOSPC na primeira tentativa (disco cheio); refeito com `NODE_OPTIONS=--max-old-space-size=4096`.
- Comando: `E2E_BASE_URL=http://localhost:3001 E2E_API_BASE_URL=http://localhost:8001/api/v1 npx playwright test e2e/edificacoes-contratos.spec.ts e2e/dashboard.spec.ts` (a partir de `03_frontend/`). Em ambiente padrão basta `npx playwright test` com a stack em :3000/:8000.

## Para o fechamento de lote
- BL-21: marcar a cobertura de edificações/contratos/dashboard; abrir pendência para o bug do seletor (acima) e para a divergência de bcrypt no ambiente local.
- Proposta de decisão: nenhuma.
