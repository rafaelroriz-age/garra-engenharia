# T81 — Snapshot cifrado da leitura da equipe (DEC-57)

Com o PC do dono desligado, o site estático (GitHub Pages, DEC-57 P3/P5) abre em modo leitura a partir de `snapshot.enc`, publicado na branch `snapshot` do repositório público. Esta tarefa gera o arquivo; o agente do PC (T82) publica; o front (T83) decifra com WebCrypto.

## 1. O que foi feito

| Caminho | Papel |
|---|---|
| `04_backend/app/services/snapshot/cifra.py` | `cifrar_snapshot`, `decifrar_snapshot` (usada no teste), `hash_rotas`, `SnapshotSenhaInvalida` |
| `04_backend/app/services/snapshot/coletor.py` | `coletar_rotas(app, session_factory, email_servico=...)` e `garantir_usuario_servico` |
| `04_backend/app/scripts/gerar_snapshot.py` | CLI `--saida` / `--somente-se-mudou` |
| `04_backend/tests/test_snapshot.py` | 11 testes (cifra, vetor fixo, coleta com seed, usuário de serviço, script) |
| `04_backend/requirements.txt` | `cryptography>=42.0,<51.0` explícita (antes vinha só transitiva pelo `python-jose[cryptography]`) |
| `04_backend/.env.example` | `SNAPSHOT_SENHA`, `SNAPSHOT_USUARIO_EMAIL` |

## 2. Uso

```powershell
# a partir de 04_backend/, com o .env apontando para o banco do PC
$env:SNAPSHOT_SENHA = '<senha da equipe, >= 16 caracteres>'
python -m app.scripts.gerar_snapshot --saida C:\caminho\snapshot.enc
python -m app.scripts.gerar_snapshot --saida C:\caminho\snapshot.enc --somente-se-mudou
```

| Variável | Obrigatória | Padrão | Uso |
|---|---|---|---|
| `SNAPSHOT_SENHA` | sim | — | Senha da equipe; < 16 caracteres sai com código 2 sem gravar (DEC-57: a força da senha é a proteção do arquivo público). |
| `SNAPSHOT_USUARIO_EMAIL` | não | `snapshot.servico@garra-engenharia.com.br` | Auditor de serviço da coleta. Criado (role `auditor`, ativo, senha aleatória de 32 bytes descartada) se não existir. Se o e-mail já pertencer a uma conta que não é auditor ativo, o script falha (código 1) e não altera a conta. |

Códigos de saída (para o agente T82): `0` gravou, `3` nada mudou (só com `--somente-se-mudou`), `2` configuração inválida, `1` erro.

Saídas gravadas, ambas com escrita atômica (`.tmp` + `os.replace`):

- `<saida>`: o envelope JSON (seção 3);
- `<saida>.sha256`: SHA-256 hex do texto claro **das rotas** (JSON estável, chaves ordenadas, sem `gerado_em`). `--somente-se-mudou` compara a coleta nova com este arquivo; igual ⇒ não grava nada e sai com 3. Sem a flag, grava sempre. Como `/ia/uso` devolve o período `de`/`ate` relativo a hoje, o hash muda pelo menos uma vez por dia (uma publicação diária a mais, sem impacto).

O script coleta em processo (não precisa de uvicorn no ar): `httpx.AsyncClient(transport=ASGITransport(app, raise_app_exceptions=False))`, com `get_db` sobrescrito durante a coleta por um engine próprio (`pool_size=8`), até 8 requisições simultâneas. Um 4xx/5xx numa rota não aborta: a rota fica fora do snapshot e é listada no stdout ("Rotas que falharam").

## 3. Formato do arquivo

`snapshot.enc` é JSON UTF-8 (binários em base64 **padrão**, com `=`):

```json
{
  "v": 1,
  "kdf": {"alg": "PBKDF2-SHA256", "iter": 600000, "salt": "<16 bytes b64>"},
  "cifra": "AES-256-GCM",
  "iv": "<12 bytes b64>",
  "ct": "<texto cifrado || tag de 16 bytes, b64>",
  "gerado_em": "2026-11-17T12:00:00+00:00"
}
```

- Chave: `PBKDF2-HMAC-SHA256(senha em UTF-8, salt, 600000) → 32 bytes`.
- Cifra: AES-256-GCM, iv de 12 bytes, **sem AAD**, tag de 128 bits anexada ao fim de `ct` (layout que `crypto.subtle.decrypt({name:"AES-GCM", iv}, key, ct)` aceita direto).
- Salt e iv novos (aleatórios) a cada geração.
- `gerado_em` fica também em claro no envelope, para a faixa "Modo leitura — dados de <data>" antes de pedir a senha.
- Texto claro após decifrar: **gzip** (`DecompressionStream('gzip')`) de JSON UTF-8:

```json
{"gerado_em": "...", "rotas": {"/api/v1/edificacoes?page=1&page_size=10": {"items": [...], "total": 79, "page": 1, "page_size": 10}, "...": "..."}}
```

Os corpos são exatamente as respostas 200 da API (mesmo `response_model`).

### Receita WebCrypto (referência para T83)

```ts
const b64 = (s: string) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(senha), "PBKDF2", false, ["deriveKey"]);
const chave = await crypto.subtle.deriveKey(
  { name: "PBKDF2", hash: "SHA-256", salt: b64(env.kdf.salt), iterations: env.kdf.iter },
  base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
const gz = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(env.iv) }, chave, b64(env.ct)); // senha errada ⇒ OperationError
const texto = await new Response(new Blob([gz]).stream().pipeThrough(new DecompressionStream("gzip"))).text();
const { gerado_em, rotas } = JSON.parse(texto);
```

## 4. Chave das rotas

Chave = `"/api/v1" + path`, onde `path` é **exatamente** o argumento que a tela passa para `api.get`/`apiFetch` (relativo a `NEXT_PUBLIC_API_URL`, que termina em `/api/v1`), sem host. A query segue a ordem de inserção do `URLSearchParams` de cada tela; valores codificados como `URLSearchParams` (espaço vira `+`); o tipo do conteúdo de relatório como `encodeURIComponent(tipo.toLowerCase())`. No T83: `chave = "/api/v1" + path`.

| Rota (chave) | De onde vem no front | Como os IDs são descobertos |
|---|---|---|
| `/api/v1/auth/me` | `lib/use-usuario-atual.ts` | — (perfil do auditor de serviço, role `auditor`) |
| `/api/v1/ia/uso` | nenhuma tela chama hoje (pedido pela tarefa); sem query = últimos 30 dias | — |
| `/api/v1/sistemas-prediais`, `/api/v1/gabarito/tipos-anomalia`, `/api/v1/gabarito/tipos-falha`, `/api/v1/gabarito/localizacoes` | `app/inspecoes/ocorrencias/page.tsx` | — |
| `/api/v1/responsaveis`, `/api/v1/responsaveis/{id}` | `lib/api-client.ts` `responsaveis.listar` | itens da lista |
| `/api/v1/edificacoes` | `app/dashboard/page.tsx` (sem query) | — |
| `/api/v1/edificacoes?page=1&page_size=100` | `app/contratos/page.tsx` (select de edificação) | — |
| `/api/v1/edificacoes?page=N&page_size=10` | `app/edificacoes/page.tsx` (todas as páginas) | percorre até `total` |
| `/api/v1/edificacoes/{id}`, `/api/v1/edificacoes/{id}/dashboard` | `app/edificacoes/detalhe`, `app/dashboard` | itens das páginas |
| `/api/v1/contratos?page=N&page_size=10` | `app/contratos/page.tsx` sem filtro (todas as páginas) | percorre até `total` |
| `/api/v1/contratos?page=N&page_size=10&tipo_servico=X` / `&status=X` / `&edificacao_id=X` | idem, um filtro por vez, valores **presentes** nos dados | `tipo_servico`/`status` dos contratos; ids das edificações |
| `/api/v1/contratos/{id}` | `app/contratos/detalhe` | itens das páginas |
| `/api/v1/inspecoes/{id}`, `/api/v1/inspecoes/{id}/relatorios` | `app/inspecoes/visitas`, `app/inspecoes/relatorio`, `relatorios.listar` | `inspecao.id` do detalhe do contrato |
| `/api/v1/inspecoes/{id}/conteudo/{tipo}` | `conteudo.obter` (tipo = da inspeção, minúsculo) | `inspecao.tipo` |
| `/api/v1/visitas/{id}`, `/api/v1/visitas/{id}/mao-obra`, `/api/v1/visitas/{id}/medicoes` | (detalhe; hoje as telas usam `visitas` embutidas no detalhe da inspeção) | `visitas[]` do detalhe da inspeção |
| `/api/v1/inspecoes/{id}/ocorrencias` | `app/inspecoes/ocorrencias/page.tsx` (lista completa) | — |
| `/api/v1/inspecoes/{id}/ocorrencias?sistema_id=X`, `?grau_risco=Y`, `?sistema_id=X&grau_risco=Y` | idem, filtros da tabela | combinações **presentes** nas ocorrências |
| `/api/v1/ocorrencias/{id}` | detalhe | itens da lista |

**Fora, por desenho:** `/portal/*`, `/auth/login`, `/inspecoes/{id}/relatorios/{rid}/download/{formato}`, bytes de fotos e documentos (o coletor recusa chaves com `/portal`, `/auth/login`, `/download/`, `/documentos`, `/fotos/`). Os JSON incluem campos de URL de fotos/documentos tal como a API devolve; no modo leitura o front deve mostrar o placeholder em vez de carregá-los.

**Lacunas para o T83 tratar (chave ausente):**

- busca livre da tela de edificações (`nome`/`endereco` com texto digitado): imprevisível; sugestão: filtrar localmente as páginas sem filtro;
- filtros de contratos combinados (dois ou mais ao mesmo tempo) e filtros de valores sem nenhum resultado: filtrar localmente a lista sem filtro (todos os contratos estão nas páginas sem filtro);
- filtros de ocorrências com combinação ausente = lista vazia (todas as combinações com resultado estão no snapshot);
- `/ia/uso` com período diferente do padrão; `/mao-obra/{item}` e `/medicoes/{item}` (nenhuma tela chama).

## 5. Tamanho e tempo típicos

Medido no banco de dev local (`garra_engenharia`: 79 edificações, 79 contratos, 19 inspeções, 191 visitas, 2 ocorrências), só leitura, com um auditor já existente como `SNAPSHOT_USUARIO_EMAIL` (nada criado nem alterado):

| Medida | Valor |
|---|---|
| Rotas capturadas | 996 |
| JSON claro | 1 890 656 bytes (~1,8 MB) |
| gzip | 209 104 bytes |
| `snapshot.enc` (base64 + envelope) | 279 007 bytes (~273 KB) |
| Tempo da coleta + cifra | ~48 s (2 execuções: 48,6 s e 48,4 s) |
| 2ª execução com `--somente-se-mudou` | `Snapshot sem mudanças (996 rotas, sha256 78c1640cc70a…)`, código 3 |

Distribuição das 996 rotas: visitas 191 × 3; edificações 79 × 2 (+ 8 páginas + 2 listas); contratos 79 detalhes + 79 listas por edificação + 27 páginas de listas; inspeções 19 × 3; ocorrências 2 + 6 listas filtradas; 4 de gabarito; `/auth/me`.

O banco de dev está atrás nas migrations (`relation "chamadas_ia" does not exist`): por isso `/ia/uso`, `/responsaveis` e os conteúdos RFO/LTIP responderam 500 e ficaram fora (21 rotas listadas no stdout); 7 inspeções antigas têm tipo legado `fiscalização de obra` e o conteúdo responde 422. No PC do dono, com o banco migrado (`alembic upgrade head`), só sobram os 422 dos tipos legados, se existirem. Não migrei o banco de dev (regra de não alterar dados existentes).

## 6. Vetor de teste (para o T83 validar a mesma cifra)

Senha: `garra-vetor-de-teste-2026` (iterações 600000; salt = bytes 0x00..0x0f; iv = bytes 0x64..0x6f).

Envelope:

```json
{
  "v": 1,
  "kdf": {"alg": "PBKDF2-SHA256", "iter": 600000, "salt": "AAECAwQFBgcICQoLDA0ODw=="},
  "cifra": "AES-256-GCM",
  "iv": "ZGVmZ2hpamtsbW5v",
  "ct": "LS0+PjfaRdi0+WO5lD5DRc89s4wxV+TCZUANmOA1UrzmHO7qjPSmqwGI00eU2I4LxAKVDSu0g7qQuJolJdIMME/Tn09fMmxTMFfPmLfGkKEfK4UHX9UMhYF7P9CYWpH+G6Rk6jMm3mnUj3Hp5TXjORUECdJwyZ7tqpCUxp7gKbLItpUgf0tbxXswcoXkCE80VxlUnde+/aYeJAg/KWcCmOO0uh9Hn5g2kLV+ZObQBr9p5b7EnGq4p30F8P/2X76dmv3ZSjKeP4HXllsuiyODZUnx9ONVSGBx8u7hTDScEnCZUnQ8BM3X0Ot/ug==",
  "gerado_em": "2026-11-17T12:00:00+00:00"
}
```

Texto claro esperado após decifrar e descomprimir (JSON compacto, chaves ordenadas):

```json
{"gerado_em":"2026-11-17T12:00:00+00:00","rotas":{"/api/v1/auth/me":{"email":"snapshot.servico@garra-engenharia.com.br","nome":"Snapshot de leitura (serviço)","role":"auditor"},"/api/v1/edificacoes?page=1&page_size=10":{"items":[],"page":1,"page_size":10,"total":0}}}
```

Com a senha `garra-vetor-de-teste-2026x` a decifragem tem de falhar (tag GCM). O mesmo vetor está em `tests/test_snapshot.py` (`VETOR_*`): decifra, falha com senha errada e re-cifra byte a byte igual com salt/iv fixos.

## 7. Testes

PostgreSQL de `05_infra/docker-compose.yml` (localhost:5433), banco `garra_engenharia_test` migrado com `alembic upgrade head`; venv `04_backend/.venv` (Python 3.14.6, cryptography 50.0.1).

`pytest tests/test_snapshot.py`: **11 passed** em 135 s (o grosso é o `seed_demo` com fotos sintéticas e a coleta). Cobrem: ida e volta, salt/iv aleatórios, senha errada, envelope adulterado, vetor fixo (decifra e re-cifra igual), hash estável, coleta com o seed de demonstração (prefixo `SNAPTESTE`) contendo as rotas esperadas de edificação, contratos, as 5 inspeções (detalhe, relatórios, conteúdo, ocorrências), visitas (detalhe, mão de obra, medições), ocorrências (detalhe e filtros) e nenhuma chave de portal/login/download/fotos/documentos; usuário de serviço reutilizado sem trocar a senha e recusa sem alterar quando o e-mail é de um não auditor; script com `--somente-se-mudou` (0 → 3 → 0) e senha curta (2).

Suíte completa do backend: **não concluída nesta sessão.**

- 1ª tentativa (`pytest` inteiro no venv do Windows): interrompida na coleta por `tests/test_rfo_contexto.py` → `OSError: cannot load library 'libpango-1.0-0'` (WeasyPrint sem GTK no Windows, limitação conhecida descrita no `04_backend/README.md`; não tem relação com esta tarefa).
- 2ª tentativa (`pytest --ignore=tests/test_rfo_contexto.py`): o Claude Code encerrou o processo por **falta de memória na máquina** quando estava em ~9% (saída parcial: `............................................FFFF............FFFFFFFFFFFF [  9%]`). Pela ordem alfabética, esses ~72 primeiros testes são de `test_auth.py` a `test_edificacoes.py`, módulos que esta tarefa não toca (só arquivos novos, mais `requirements.txt` e `.env.example`); as falhas não foram investigadas e a suíte não foi relançada, por causa da memória.
- **Pendente no fechamento do lote:** rodar a suíte inteira no container (`docker exec garra-backend pytest` com o código desta branch, ou o venv com memória livre) e conferir se aquelas falhas já existiam na `main`.

`ruff check .` em `04_backend`: `All checks passed!`

## 8. Propostas de decisão

- **P-T81-1:** o envelope tem um campo extra `"cifra": "AES-256-GCM"` além do formato do Pronto, para o front recusar formatos futuros sem tentar decifrar.
- **P-T81-2:** rotas com filtros imprevisíveis (busca livre, filtros combinados de contratos) não entram no snapshot; o modo leitura do T83 filtra localmente a lista sem filtro quando a chave não existir.
- **P-T81-3:** o auditor de serviço é uma conta real ativa com senha aleatória nunca guardada (só serve para emitir o JWT em processo). Se quiserem impedir login por ela, uma tarefa futura pode marcar contas de serviço explicitamente (não alterei o modelo `Usuario`).
