# BL-24 — Repasse das variáveis `LEGENDA_IA_*` ao container e ao Render

Pendência 2 de `00_docs/backlog-auto/legenda-ia-limites.md` (T35, DEC-42 C): as variáveis de
limite e de teto da saída da legenda por IA estavam nos dois `.env.example`, mas não no
`environment:` do serviço `backend` nem no `render.yaml`. Em Docker e no Render valiam só os defaults.

## 1. Conferência com o código

Fonte: `04_backend/app/core/config.py` (campos de `Settings`, linhas 48–56). São 8 variáveis, todas com default:

| Variável | Tipo | Default em `config.py` | Restrição |
|---|---|---|---|
| `LEGENDA_IA_LIMITE_POR_USUARIO` | int | 10 | `ge=1` |
| `LEGENDA_IA_JANELA_USUARIO_SEGUNDOS` | int | 60 | `ge=1` |
| `LEGENDA_IA_LIMITE_DIARIO_POR_USUARIO` | int | 200 | `ge=1` |
| `LEGENDA_IA_LIMITE_POR_FOTO` | int | 5 | `ge=1` |
| `LEGENDA_IA_JANELA_FOTO_SEGUNDOS` | int | 3600 | `ge=1` |
| `LEGENDA_IA_SAIDA_MAX_CARACTERES` | int | 500 | `ge=1`, `le=500` |
| `LEGENDA_IA_SAIDA_MAX_ITENS` | int | 20 | `ge=1` |
| `LEGENDA_IA_SAIDA_MAX_CARACTERES_ITEM` | int | 300 | `ge=1` |

Os dois `.env.example` já tinham as 8, com os mesmos valores. Nenhuma faltava, então não foi preciso
acrescentar nada neles.

## 2. Alterações

| Variável | `05_infra/docker-compose.yml` | `05_infra/docker-compose.prod.yml` | `render.yaml` (`garra-backend`) | `04_backend/.env.example` | `05_infra/.env.example` |
|---|---|---|---|---|---|
| `LEGENDA_IA_LIMITE_POR_USUARIO` | `${…:-10}` (adicionada) | `${…:-10}` (adicionada) | `value: "10"` (adicionada) | já existia | já existia |
| `LEGENDA_IA_JANELA_USUARIO_SEGUNDOS` | `${…:-60}` | `${…:-60}` | `value: "60"` | já existia | já existia |
| `LEGENDA_IA_LIMITE_DIARIO_POR_USUARIO` | `${…:-200}` | `${…:-200}` | `value: "200"` | já existia | já existia |
| `LEGENDA_IA_LIMITE_POR_FOTO` | `${…:-5}` | `${…:-5}` | `value: "5"` | já existia | já existia |
| `LEGENDA_IA_JANELA_FOTO_SEGUNDOS` | `${…:-3600}` | `${…:-3600}` | `value: "3600"` | já existia | já existia |
| `LEGENDA_IA_SAIDA_MAX_CARACTERES` | `${…:-500}` | `${…:-500}` | `value: "500"` | já existia | já existia |
| `LEGENDA_IA_SAIDA_MAX_ITENS` | `${…:-20}` | `${…:-20}` | `value: "20"` | já existia | já existia |
| `LEGENDA_IA_SAIDA_MAX_CARACTERES_ITEM` | `${…:-300}` | `${…:-300}` | `value: "300"` | já existia | já existia |

- Compose: segue o padrão `${VAR:-padrão}` das demais variáveis do serviço. O default é o mesmo de `config.py` e do `.env.example`.
- `render.yaml`: as variáveis não são segredos, então usam `value:` fixo, como `JWT_ALGORITHM` e `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`. Nenhum valor sensível foi escrito.
- Nenhum segredo, `.env` ou chave foi criado ou versionado.
- Nenhum código Python, teste, migration ou doc de gestão (`00_docs/projeto/*`) foi alterado.

## 3. Validação

### 3.1 Docker Compose (não executada)

```
$ docker compose -f docker-compose.yml config
docker: command not found
$ docker compose -f docker-compose.prod.yml config
docker: command not found
```

Docker não está instalado nesta máquina, então `docker compose config` não rodou. Em vez disso,
validei a sintaxe YAML e a presença das chaves com PyYAML (abaixo).

### 3.2 Sintaxe YAML e chaves

```
$ python -c "import yaml; yaml.safe_load(open('render.yaml', encoding='utf-8'))"
render.yaml OK

$ python -c "import yaml; yaml.safe_load(open('05_infra/docker-compose.yml', encoding='utf-8'))"
dev compose YAML OK (sem erro)

$ (prod) python -c "...yaml.safe_load(open('05_infra/docker-compose.prod.yml'))..."
yaml.scanner.ScannerError: mapping values are not allowed here
  in "05_infra/docker-compose.prod.yml", line 89, column 117
```

**Erro pré-existente, fora do escopo desta tarefa.** A linha 89 é a `image:` do serviço `backend`:
`...backend:${IMAGE_TAG:?defina IMAGE_TAG (ex.: v1.0.0 ou staging-<sha>)}`. O `: ` dentro do texto de
ajuda do `${…:?…}` quebra o YAML. O mesmo trecho existe em `main` (verificado com `git show main:05_infra/docker-compose.prod.yml`).
Não corrigi porque não é parte de BL-24. Sugestão: pôr a `image:` entre aspas, ou trocar `ex.: ` por `ex. `.

Para verificar só as minhas inclusões, parseei uma cópia em memória com a linha 89 entre aspas:

```
prod backend env keys with LEGENDA_IA: 8
dev backend env keys with LEGENDA_IA: 8
render backend LEGENDA_IA keys: 8
```

### 3.3 Testes e lint

Nenhum arquivo Python, de teste ou de frontend foi alterado. Por isso não rodei `pytest`, `ruff check .`,
`npm run lint` nem `npm run build`. Para esta alteração, o checklist de `.github/pull_request_template.md`
se aplica só ao item de `.env.example` (já atendido, ver §1).

## 4. Pendências e decisões propostas

- **Prod compose, linha 89 (pré-existente):** corrigir o YAML antes do próximo deploy por VPS (ver §3.2). Proposta: aspas na `image:` do backend (e do frontend, se o mesmo problema ocorrer).
- **Validação com Docker pendente:** rodar `docker compose -f docker-compose.yml config` e `docker compose -f docker-compose.prod.yml config` (com `IMAGE_TAG` e os segredos fictícios via ambiente) numa máquina com Docker, depois do item acima.
- **Render:** as 8 variáveis só valem no serviço `garra-backend` quando o Blueprint for aplicado ou o serviço for sincronizado com o `render.yaml`. O doc do `render.yaml` diz que o serviço real foi criado via MCP, então talvez seja preciso definir as variáveis manualmente no Dashboard. Isso é ação do humano.

## 5. Referências

- Código: `04_backend/app/core/config.py` (linhas 48–56).
- Origem da pendência: `00_docs/backlog-auto/legenda-ia-limites.md` §6, pendência 2.
- Decisão: DEC-42 (`00_docs/projeto/decisoes.md`).
