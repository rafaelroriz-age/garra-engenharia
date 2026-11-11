# npm audit — frontend (03_frontend)

Análise de vulnerabilidades reportadas pelo `npm ci` em 03_frontend (T01 · diagnóstico §3.3, item 5 de §4). **Só análise:** nenhum código, `package.json` ou `package-lock.json` foi alterado. Nenhum `npm audit fix` foi executado sem `--dry-run`.

## 1. Resultado

| Escopo | Pacotes | Critical | High | Moderate | Low | Advisories únicos (GHSA) |
|---|---:|---:|---:|---:|---:|---:|
| `npm audit` (tudo) | 30 | 2 | 11 | 17 | 0 | 55 (prod + dev) |
| `npm audit --omit=dev` (produção) | 13 | 2 | 7 | 4 | 0 | 53 |

Os números batem com o diagnóstico §3.3 (30 vulnerabilidades: 17 moderadas, 11 altas, 2 críticas) — o lock não mudou.

Nota: os 55 advisories incluem 2 de `js-yaml`, que só existe no escopo dev. Em produção, são 53 advisories nos 13 pacotes listados abaixo.

Os pacotes de produção são a parte que importa para o deploy. A imagem de produção (`03_frontend/Dockerfile.render`, `node:20-alpine`, `node server.js` em modo `standalone`) roda o Next.js em runtime.

## 2. Tabela por pacote

Severidade = pior advisory do pacote. "Direta" = listada em `package.json`. "Prod" = alcançável por `dependencies`; "dev" = só em `devDependencies`. Fix = sugestão de `npm audit fix --dry-run`. Advisories são os títulos do próprio `npm audit`; o texto completo não foi lido.

| # | Pacote | Sev. | Direta/Transitiva | Prod/Dev | Advisories | Fix sugerido | Breaking? | Exposição real |
|--:|---|---|---|---|--:|---|---|---|
| 1 | **next** (14.2.35, fixo) | critical | direta | prod | 25 | next@16.4.5 | **sim (major)** | **Alta.** Roda no container de produção. Advisories de RCE (Image Optimization com AVIF/SVG; Windows), DoS em Server Components/Server Actions, SSRF, cache poisoning. Nenhuma versão 14.x aparece como corrigida: os intervalos vão até 15.5.x. |
| 2 | tar (6.2.1) | critical | transitiva (fabric→canvas→@mapbox/node-pre-gyp→tar) | prod | 12 | via fabric@7.4.0 | **sim** | Baixa em runtime. Os advisories são de extração de arquivos (hardlink/symlink, DoS por parse). O app não extrai arquivos em runtime; só afetaria o install se fosse usado com tarballs não confiáveis. |
| 3 | fabric (6.9.1) | high | direta | prod | 2 | fabric@7.4.0 | **sim (major)** | Média. Usado no editor de anotação de fotos (`components/photo-annotation-editor.tsx`, `import("fabric")`). Advisories: XSS em exportação SVG e em `Gradient colorStops`. Exposição depende de o SVG exportado ser mostrado a outros usuários — **não determinado**. |
| 4 | canvas (2.11.2) | high | transitiva (opcional do fabric; ausente no Windows) | prod | herdado | via fabric@7.4.0 | sim | Baixa. Módulo nativo; risco só na instalação. |
| 5 | @mapbox/node-pre-gyp (1.0.11) | high | transitiva | prod | herdado | via fabric@7.4.0 | sim | Baixa. Ferramenta de instalação de binário nativo. |
| 6 | rimraf (3.0.2) | moderate | transitiva | prod | herdado | via fabric@7.4.0 | sim | Baixa. Remoção de arquivos no build/install. |
| 7 | glob | high | transitiva | prod | 2 | eslint-config-next@0.2.4 (**inválido**) | sim | Baixa. Injeção de comando (`glob -c`) afeta só o CLI do pacote; o app não usa o CLI. Corrige-se com a atualização de fabric/next. |
| 8 | brace-expansion | high | transitiva | prod | 5 | `fix: true` | não | Baixa. DoS por padrões de expansão; relevante só se padrões vierem de entrada não confiável. **Corrigível sem major.** |
| 9 | minimatch | moderate | transitiva | prod | 1 | eslint@4.0.0 (**inválido**) | sim | Baixa. DoS por amplificação de globparts. Corrige-se com glob/rimraf. |
| 10 | nanoid | high | transitiva | prod | 1 | `fix: true` | não | Baixa. Loop infinito com `size: 0` em gerador customizado. **Corrigível sem major.** |
| 11 | postcss | high | direta (devDep ^8) + aninhado no next | prod (via next) | 3 | next@16.4.5 | sim | Baixa. Advisories tratam CSS não confiável e `sourceMappingURL`; o CSS do app é gerado no build (Tailwind). |
| 12 | postcss-selector-parser | moderate | transitiva | prod | 1 | `fix: true` | não | Baixa. CPU em seletores. **Corrigível sem major.** |
| 13 | source-map-js | high | transitiva | prod | 1 | `fix: true` | não | Baixa. DoS em source map. **Corrigível sem major.** |
| 14 | eslint (8.57.1) | moderate | direta | dev | herdado | eslint@4.0.0 (**downgrade inválido**) | indefinido | Nula em runtime. O intervalo do advisory cobre toda a série 8; **a versão corrigida não é determinada pelo audit**. |
| 15 | eslint-config-next (14.2.35, fixo) | high | direta | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | sim | Nula em runtime. Acompanha a atualização do Next. |
| 16 | @next/eslint-plugin-next | high | transitiva | dev | 1 | intervalo 14.0.5-canary.0 – 15.0.0-rc.1 | sim (com Next) | Nula em runtime. Corrige-se em 15.0.0+. |
| 17 | @typescript-eslint/eslint-plugin | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 18 | @typescript-eslint/parser | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 19 | @typescript-eslint/type-utils | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 20 | @typescript-eslint/typescript-estree | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 21 | @typescript-eslint/utils | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 22 | @eslint-community/eslint-utils | moderate | transitiva | dev | herdado | eslint@4.0.0 (**inválido**) | indefinido | Nula em runtime. |
| 23 | @eslint/eslintrc | moderate | transitiva | dev | herdado | eslint@4.0.0 (**inválido**) | indefinido | Nula em runtime. |
| 24 | @humanwhocodes/config-array | moderate | transitiva | dev | herdado | eslint@4.0.0 (**inválido**) | indefinido | Nula em runtime. |
| 25 | eslint-plugin-import | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 26 | eslint-plugin-jsx-a11y | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 27 | eslint-plugin-react | moderate | transitiva | dev | herdado | eslint-config-next@0.2.4 (**inválido**) | indefinido | Nula em runtime. |
| 28 | file-entry-cache | moderate | transitiva | dev | herdado | eslint@4.0.0 (**inválido**) | indefinido | Nula em runtime. |
| 29 | flat-cache | moderate | transitiva | dev | herdado | eslint@4.0.0 (**inválido**) | indefinido | Nula em runtime. |
| 30 | js-yaml | high | transitiva | dev | 2 | `fix: true` | não | Nula em runtime (só dev). **Corrigível sem major.** |

Contagem: 13 pacotes de produção (linhas 1–13) + 17 de dev (linhas 14–30) = 30.

"Inválido" = o `npm audit fix --force` sugeriria um downgrade ou um pacote sem relação. Não aplicar.

## 3. Pontos que pesam na análise

- **Next.js é o risco principal.** É o único pacote crítico em produção com correção fora de 14.x. O Dockerfile de produção expõe o servidor Next a tráfego externo. O código atual não usa `next/image`, middleware, route handlers nem Server Actions (busca em `03_frontend` no HEAD e em `main`), o que afasta alguns advisories — mas os de React Server Components atingem o App Router, que é usado em todas as páginas. Se o endpoint de Image Optimization (`/_next/image`) fica acessível no servidor standalone, os advisories de RCE valem: **não determinado** sem teste.
- **A RCE "windows-hosted" não se aplica** ao container atual (`node:20-alpine`).
- **Fabric e a cadeia `canvas`/`tar` somem com fabric@7.4.0**, que é major. Se o editor de fotos depende de API v6 (o README de `main` registra que `Image.fromURL` já mudou de callback para Promise na v6), a atualização exige teste do editor (RF-14).
- **Os 17 pacotes de dev não rodam em produção.** Pesam pouco para o deploy, mas ainda contam como vulnerabilidade no `npm audit` completo.
- **Limitação:** a análise usa os títulos e intervalos do `npm audit`. Não foi feita leitura dos advisories completos nem teste de exploração (fora do escopo, e não há base para isso sem o texto completo).

## 4. Plano priorizado

| Prioridade | Ação | Tipo | Impacto | Verificação |
|---|---|---|---|---|
| 1 | `npm audit fix` **sem `--force`**, só nos 5 pacotes `fix: true`: brace-expansion, js-yaml, nanoid, postcss-selector-parser, source-map-js | Sem major | Muda só `package-lock.json`. Resolve 5 dos 30 pacotes (4 high, 1 moderate) | `git diff` do lock; `npm run lint`; `npm run build`; `npm audit --omit=dev` |
| 2 | **Decisão:** upgrade do Next.js em tarefa própria. Alvo mínimo pelos intervalos: 15.5.28+. Alvo sugerido pelo npm: 16.4.5 | **Major** | Next 15+ exige React 19 no App Router (verificar nas notas de versão; o projeto pina `react ^18`). Atualiza `eslint-config-next` junto. Revisar todas as rotas | `npm run build`, `npm run lint`, Playwright (`e2e/rfo.spec.ts` e demais) |
| 3 | **Decisão:** upgrade do fabric 6.9.1 → 7.4.0 | **Major** | Remove a cadeia canvas/@mapbox/tar/rimraf/glob (produção). Exige adaptar `components/photo-annotation-editor.tsx` à API v7 | Teste manual do editor de fotos (RF-14); Playwright |
| 4 | **Decisão:** toolchain de lint (eslint 8 → 9 e @typescript-eslint) | **Major** (dev) | Sem impacto em runtime. Pode vir junto com o item 2 | `npm run lint` |
| — | **Não executar** `npm audit fix --force` | — | Propõe eslint@4.0.0 e eslint-config-next@0.2.4 (downgrades) e fabric@7.4.0 sem avaliação | — |

Ordem sugerida: 1 agora; 2 e 3 como decisões do dono (podem ser o mesmo lote, já que o alvo do Next define a versão do React); 4 por último.

## 5. Decisões propostas (não registradas em `decisoes.md`)

- **Proposta A:** tratar o upgrade do Next.js (item 2) como prioridade antes do próximo deploy de produção, por ser o único crítico exposto em runtime. Escolher alvo entre 15.5.28+ e 16.x, conforme a decisão sobre React 19.
- **Proposta B:** fabric 7 (item 3) junto com o Next, ou depois, com teste do editor de fotos.
- **Proposta C:** não usar `npm audit fix --force` em nenhum lote.
- **Proposta D (opcional):** adicionar `npm audit --omit=dev --audit-level=critical` ao CI como gate, para barrar só o que roda em produção e está em critical.

## 6. Comandos executados

```text
node --version / npm --version                           (contexto)
ls 03_frontend/node_modules                               -> ausente
npm ci --prefix 03_frontend                               -> OK (warn: 1 install-script não aprovado, unrs-resolver@1.12.2)
npm audit --prefix 03_frontend --json                     -> exit 1 (há vulnerabilidades); 30 pacotes (17 mod, 11 high, 2 crit)
npm audit --prefix 03_frontend --omit=dev --json          -> exit 1; 13 pacotes (4 mod, 7 high, 2 crit)
npm audit fix --prefix 03_frontend --dry-run              -> exit 0; sem alteração de arquivos
npm ls canvas tar fabric @mapbox/node-pre-gyp rimraf --prefix 03_frontend --all
                                                          -> fabric@6.9.1 instalado; canvas/tar não aparecem (canvas opcional, ausente no Windows)
npm run lint --prefix 03_frontend                         -> exit 0, "No ESLint warnings or errors"
npm run build --prefix 03_frontend                        -> OK; rotas geradas (estáticas e dinâmicas)
git grep (fabric, next/image, use server, middleware, route.ts) em HEAD e main -> sem uso de next/image, Server Actions, middleware ou route handlers
```

Os JSONs brutos do audit ficaram em `$CLAUDE_JOB_DIR/tmp` (não versionados).

## 7. Notas de rastreabilidade

- Este worktree (`worktree-backlog-T03`) não contém `00_docs/backlog-auto/diagnostico.md` nem a seção de §3.3 — o arquivo existe em `main`. A referência foi lida de `main` com `git show`.
- Nenhum arquivo de gestão (`backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`) foi editado. Propostas acima ficam para o fechamento de lote.
