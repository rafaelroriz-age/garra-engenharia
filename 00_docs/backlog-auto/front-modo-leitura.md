# T83: descoberta da API por api.json, modo leitura com snapshot cifrado e deploy no Pages (DEC-57)

Com o backend no PC do dono atrás de um túnel `cloudflared` (URL aleatória a cada boot), o front estático do GitHub Pages deixa de ter a URL da API fixa no build. Ele descobre a URL pelo `api.json` da branch `snapshot`. Com o PC desligado, abre em modo leitura com o `snapshot.enc` do T81, decifrado no navegador.

## 1. Arquivos

| Caminho | Papel |
|---|---|
| `03_frontend/lib/api-descoberta.ts` (novo) | Lê `NEXT_PUBLIC_API_DISCOVERY_URL` com cache-buster (`?t=<ms>`, `cache: "no-store"`) e cache em memória de 60 s, compartilhado entre chamadas simultâneas. A função pura `avaliarApiJson` decide online/offline. `urlSnapshot()` = mesmo diretório do `api.json` + `snapshot.enc`. Sem a variável (dev), devolve `NEXT_PUBLIC_API_URL` fixa. |
| `03_frontend/lib/modo-leitura.ts` (novo) | `decifrarSnapshot` (PBKDF2-SHA256 → AES-256-GCM via `crypto.subtle`, depois `DecompressionStream('gzip')`), `chaveRota`, `resolverRota`, o erro tipado `ModoLeituraErro`, o store global (`entrarModoLeitura`, `informarSenha`, `pedirSenha`, `cancelarSenha`, `sairModoLeitura`, `tentarReconectar`, `aguardarRotas`, `responderModoLeitura`), o evento `window` `garra:modo-leitura` e o hook `useModoLeitura()`. Não importa nada com alias `@/`, por isso o `node --test` consegue testá-lo. |
| `03_frontend/lib/modo-leitura.test.ts` (novo) | 7 testes `node --test` (seção 5). |
| `03_frontend/components/modo-leitura-banner.tsx` (novo) | Faixa fixa no rodapé "Modo leitura — dados de <data>" e diálogo da senha da equipe (componentes `ui/dialog`, `ui/input`, `ui/label`, `ui/button`). Na montagem dispara a checagem do `api.json`. Fora do modo leitura não renderiza nada. |
| `03_frontend/lib/api-client.ts` | Resolve a base de forma assíncrona antes de cada `fetch`. Entra em modo leitura nas falhas listadas na seção 2. Novo `ModoLeituraError extends ApiError` e novo `verificarServidorAoIniciar()`. Injeta no store o transporte: baixar o envelope e testar `/health`. |
| `03_frontend/app/layout.tsx` | `<ModoLeituraBanner />` depois do `AppShell`. |
| `03_frontend/components/layout/app-shell.tsx` | A guarda de rota também libera a navegação quando o snapshot está desbloqueado. Com o PC desligado o login é impossível, então a senha da equipe faz esse papel. |
| `03_frontend/app/(auth)/login/page.tsx` | Em modo leitura, "Entrar" fica desabilitado e aparece o botão "Ver dados em modo leitura" (pede a senha ou vai ao dashboard). |
| Telas (seção 3) | `useModoLeitura().bloquearEscrita` em `disabled`. Placeholder nas fotos. |
| `03_frontend/components/sw-register.tsx`, `public/sw.js`, `lib/sw-cache.ts`, `lib/sw-cache.test.ts` | SW com basePath. O `OFFLINE_URL` passa a ser relativo ao scope. `raw.githubusercontent.com` nunca é interceptado. Paridade e testes ampliados (seção 4). |
| `03_frontend/package.json` | `test:unit` passa a rodar também `lib/modo-leitura.test.ts`. |
| `.github/workflows/deploy-pages.yml` | `NEXT_PUBLIC_API_URL` (Render) trocada por `NEXT_PUBLIC_API_DISCOVERY_URL`. Comentário de cabeçalho atualizado. |
| `05_infra/.env.example` | Nova variável `NEXT_PUBLIC_API_DISCOVERY_URL`, vazia em dev. |

`next.config.mjs` não precisou mudar: o `basePath` já vem de `NEXT_PUBLIC_BASE_PATH`, e o `withBasePath` de `lib/utils.ts` atende o SW.

## 2. Fluxo

```text
abertura do app ──► ModoLeituraBanner.useEffect ──► verificarServidorAoIniciar()
                                                     └─ api.json diz offline? ──► entrarModoLeitura(motivo)

apiFetch(path, opts)
 ├─ modo leitura ativo? ─────────────────────────────► responderModoLeitura(path, método)
 ├─ descobrirApi()  (cache 60 s; dev = NEXT_PUBLIC_API_URL)
 │   └─ online:false | heartbeat > 20 min | sem URL | api.json ilegível ─► entrar + responder
 ├─ fetch(`${apiBase}${path}`)
 │   ├─ erro de rede (só com descoberta) ─────────────────────────────► entrar + responder
 │   └─ 502 | 530 | 503 sem JSON (só com descoberta) ─────────────────► entrar + responder
 └─ resposta normal (4xx/5xx da API → ApiError, como antes)

responderModoLeitura
 ├─ método ≠ GET ─► ModoLeituraError (title "Servidor desligado — modo leitura", status 503)
 ├─ aguardarRotas()  (espera a senha do diálogo ou o download em curso)
 └─ resolverRota(rotas, "/api/v1" + path) ─► corpo | ModoLeituraError("sem-dados")

entrarModoLeitura
 ├─ baixa snapshot.enc (cache-buster); gerado_em em claro ─► faixa "Modo leitura — dados de <data>"
 ├─ senha em sessionStorage? decifra direto
 ├─ senão abre o diálogo; senha errada ⇒ "Senha incorreta." e o diálogo continua aberto
 └─ a cada 60 s: descobrirApi({forcar}) + GET <raiz>/health ⇒ ok ⇒ sairModoLeitura()
```

Decisões de comportamento:

- **Quando conta como PC desligado.** `online:false`, heartbeat com mais de 20 min (`HEARTBEAT_MAX_MS`, o dobro do intervalo do agente) ou `api.json` ilegível. Também contam, só em produção (com descoberta configurada), o erro de rede no `fetch` e as respostas 502 e 530 do túnel. O 503 só conta quando não vem em JSON: a própria API devolve 503 `problem+json` em `legenda-ia-indisponivel`, e isso não pode derrubar o app para o modo leitura. Após qualquer falha, o cache do `api.json` é invalidado.
- **Dev e docker-compose.** Sem `NEXT_PUBLIC_API_DISCOVERY_URL` nada muda: URL fixa, erro de rede vira `ApiError` com status 0, e o modo leitura nunca entra.
- **Erro tipado.** `ModoLeituraError` (em `api-client`) estende `ApiError`, então todas as telas já o exibem pelo `ApiErrorAlert`. O campo `motivo` vale `escrita`, `bloqueado`, `sem-dados` ou `indisponivel`.
- **Senha.** Fica só em `sessionStorage` (`garra:snapshot_senha`) e é apagada se deixar de abrir o arquivo. Cancelar o diálogo rejeita as leituras pendentes com "Informe a senha da equipe…". A faixa mostra o botão "Informar senha" para reabrir.
- **Saída automática.** A tentativa é repetida a cada 60 s (`RECONEXAO_MS`). Ao sair, o snapshot é descartado da memória e a faixa some. As telas não são recarregadas: os dados exibidos seguem os do snapshot até a próxima navegação, e os botões voltam a funcionar.
- **Filtros que não estão no snapshot (P-T81-2).** `resolverRota` tenta primeiro a chave exata. Se ela não existe, junta a lista sem filtro do mesmo caminho (o array direto, ou todas as páginas `?page&page_size`, deduplicadas por `id`), filtra localmente e pagina. Os filtros de texto `nome`, `endereco`, `q` e `busca` casam por "contém", sem acento nem caixa, combinados com OU entre si (a tela de edificações manda `nome` e `endereco` com o mesmo texto). Os demais filtros exigem igualdade, combinados com E. Um filtro que o item não tem como campo é ignorado. Isso cobre a busca livre de edificações, os filtros combinados de contratos e as combinações ausentes de ocorrências.
- **URLs de download (T80).** O backend devolve URL absoluta sempre que há request; a relativa só aparece em scripts (`storage-local.md` §6). Não precisei ajustar a montagem no front.

## 3. Ações desabilitadas em modo leitura (`useModoLeitura().bloquearEscrita`)

| Tela ou componente | Ações |
|---|---|
| `app/edificacoes/page.tsx` | Nova edificação |
| `app/edificacoes/detalhe/page.tsx` | Editar, Enviar documento |
| `app/contratos/page.tsx`, `app/contratos/detalhe/page.tsx` | Novo contrato, Editar |
| `app/inspecoes/visitas/page.tsx`, `visita-card.tsx` | Nova visita, Editar visita, Adicionar mão de obra, Adicionar medição |
| `app/inspecoes/ocorrencias/page.tsx` | Nova ocorrência, Editar, Excluir |
| `components/foto-upload.tsx` | Colar, Enviar arquivo, mover, anotar, legenda IA, remover, editar a legenda. A imagem vira o placeholder "Disponível com o servidor ligado" (o snapshot não traz bytes de fotos). |
| `components/relatorio/conteudo-form.tsx` | Salvar textos |
| `components/relatorio/emissao-versoes.tsx` | Emitir nova versão. PDF e DOCX ficam desabilitados com `title` "Disponível com o servidor ligado". |
| `app/responsaveis/page.tsx` | Novo responsável |

Os formulários só abrem por esses botões. Se uma escrita escapar mesmo assim, `apiFetch` recusa com `ModoLeituraError`. Fora do modo leitura o visual não muda. Em modo leitura entram só a faixa no rodapé (com um espaçador de 44 px para não cobrir o conteúdo), o diálogo e o botão extra no login.

## 4. Service Worker (fecha R-22)

- O registro passa a ser `navigator.serviceWorker.register(withBasePath("/sw.js"), { scope: withBasePath("/") })`. No `out/` minificado aparece como `register((0,s.w)("/sw.js"),{scope:(0,s.w)("/")})`, com `/garra-engenharia` embutido.
- Em `sw.js`, `OFFLINE_URL = new URL("offline.html", self.registration.scope).href`. O `CACHE_VERSION` foi para `v2`, para o `activate` apagar o shell antigo, cuja chave era `/offline.html`.
- `NEVER_HOSTS = [{ host: "raw.githubusercontent.com" }]` faz `api.json` e `snapshot.enc` irem sempre para a rede, sem `respondWith`. Em `sw-cache.ts` a mesma regra está em `NEVER_INTERCEPT_HOSTS` e `isNeverIntercepted`, e `isNeverCacheable` também a consulta. O teste de paridade agora compara `host:` além de `pattern:` e `never:`, e um teste novo garante o `OFFLINE_URL` relativo ao scope.
- Pendência pequena fora do escopo: `public/offline.html` usa `<img src="/icon.svg">`, que no Pages aponta para fora do basePath. Só o ícone da página offline quebra.

## 5. Deploy (`deploy-pages.yml`)

- Continua publicando `03_frontend/out` no Pages do próprio repositório, com `NEXT_PUBLIC_BASE_PATH=/garra-engenharia`.
- `NEXT_PUBLIC_API_URL: https://garra-backend.onrender.com/api/v1` deu lugar a `NEXT_PUBLIC_API_DISCOVERY_URL: https://raw.githubusercontent.com/rafaelroriz-age/garra-engenharia/snapshot/api.json`.
- Gatilho: `push` só em `branches: [main]` (com filtro de `paths`) e `workflow_dispatch`. O force-push do agente na branch `snapshot` não dispara este workflow. `ci.yml` (push `[main]`, PR `[main_front, main_back, main]`) e `sync-deploy-branches.yml` (push `[main]`) também não disparam nessa branch.

## 6. Testes e saídas

Ambiente: Windows 11, Node v26.7.0 (strip-types nativo no `node --test`), `npm ci` limpo no worktree.

`npm run test:unit` (`node --test lib/sw-cache.test.ts lib/modo-leitura.test.ts`): **18 pass, 0 fail**.

```text
✔ decifra o vetor de teste do T81 e resolve as rotas
✔ senha errada falha com SenhaSnapshotInvalida
✔ envelope de versão desconhecida é recusado sem tentar decifrar
✔ filtros ausentes no snapshot são resolvidos localmente a partir da lista sem filtro
✔ store: entra, pede senha, responde GET, recusa escrita e sai quando o servidor volta
✔ store: cancelar o diálogo rejeita as leituras pendentes
✔ descoberta: online, desligado, heartbeat velho e sem URL
✔ (8 testes de sw-cache já existentes)
✔ api.json e snapshot.enc (raw.githubusercontent.com) nunca são interceptados nem cacheados
✔ public/sw.js duplica exatamente as regras deste módulo
✔ public/sw.js resolve a página offline pelo scope (basePath do Pages)
ℹ tests 18 · pass 18 · fail 0
```

O teste do vetor usa o envelope e a senha `garra-vetor-de-teste-2026` de `snapshot-cifrado.md` §6. O texto claro decifrado bate com `ROTAS_ESPERADAS`. `api.get("/edificacoes?page=1&page_size=10")` resolve para a página vazia, e `/auth/me` para o auditor. Com a senha `…2026x` a decifragem falha com `SenhaSnapshotInvalida`.

`npm run lint`: `✔ No ESLint warnings or errors`.

`npm run build`, com as mesmas variáveis do workflow (`NEXT_PUBLIC_API_DISCOVERY_URL=…/snapshot/api.json`, `NEXT_PUBLIC_BASE_PATH=/garra-engenharia`): `✓ Compiled successfully`, 16/16 páginas estáticas, First Load JS compartilhado de 87,5 kB. O primeiro build falhou por iterar `URLSearchParams`/`Map` com spread (o tsconfig não define `target`). Corrigi com `Array.from`/`forEach`.

Conferências no `out/` (PowerShell `Select-String`):

| Busca | Resultado |
|---|---|
| `onrender.com` em `out/**` | **0 arquivos** |
| `snapshot/api.json` em `out/**` | 1 arquivo (o chunk do api-client) |
| `out/sw.js`, `out/offline.html` | presentes |

Não rodados: os e2e Playwright (o T86 cobre online pelo túnel e modo leitura com o PC desligado) e o teste manual no navegador, porque o `api.json` e o `snapshot.enc` reais só existem depois do T82 publicar a branch `snapshot`. O backend não foi tocado: `pytest`/`ruff` não se aplicam.

## 7. Propostas de decisão

- **P-T83-1.** Um 503 só conta como "PC desligado" quando não vem em JSON. 502 e 530 sempre contam. Evita que o 503 `problem+json` da legenda IA derrube o app para o modo leitura.
- **P-T83-2.** A senha da equipe que desbloqueia o snapshot libera a navegação mesmo sem token de login. Com o PC desligado não existe login, e o snapshot já é o dado do auditor de serviço (T81).
- **P-T83-3.** Ao sair do modo leitura, as telas não são recarregadas: a faixa some e os botões voltam a funcionar. Recarregar perderia o estado e a navegação seguinte já busca dados frescos.
- **P-T83-4.** A URL do snapshot é derivada da URL de descoberta (mesmo diretório, `snapshot.enc`). Isso evita uma segunda variável de ambiente.
