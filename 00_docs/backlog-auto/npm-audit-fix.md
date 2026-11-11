# npm audit fix — frontend (03_frontend), sem `--force`

Aplicação da DEC-32, item 1, a partir do diagnóstico da T03 ([npm-audit.md](npm-audit.md), que está em `main`). **Escopo:** só `03_frontend/package-lock.json`. `package.json` não mudou (nenhum dos 5 pacotes é dependência direta). Nenhum `--force`, nenhum upgrade de major.

## 1. Resultado em uma linha

Correção aplicada. O `npm audit` caiu de 30 para 26 achados (produção: 13 → 10). **Brace-expansion não foi totalmente corrigido:** as cópias 2.x e 5.x subiram, mas a cópia 1.1.16 ainda aparece, dentro de `eslint@8` (dev) e na cadeia `fabric → canvas → @mapbox/node-pre-gyp → rimraf/glob/minimatch` (produção, via fabric 6). Ver §5.

## 2. Comandos executados

| # | Comando (em `03_frontend/`) | Resultado |
|--:|---|---|
| 1 | `npm ci` | OK. Aviso: 1 install script não aprovado (`unrs-resolver@1.12.2`). |
| 2 | `npm audit --json` / `npm audit --omit=dev --json` | exit 1 (há vulnerabilidades). Contagens "antes" abaixo. |
| 3 | `npm audit fix --dry-run` | Lista as correções sem major e as sugestões de `--force` (next 16.4.5, fabric 7.4.0, tar via fabric 7). Ver §3. |
| 4 | Simulação em cópia temporária: `npm audit fix --package-lock-only --ignore-scripts` + comparação de versões por caminho | 19 pacotes mudam de versão. Nenhum de next, react, react-dom, fabric, eslint ou eslint-config-next. Nenhuma mudança de major. Critério de §3 atendido. |
| 5 | `npm audit fix` (sem `--force`) | OK. Aviso de install script (mesmo da etapa 1). |
| 6 | `git diff --stat` | Só `03_frontend/package-lock.json` (85 inserções, 86 remoções). |
| 7 | `npm audit --json` / `npm audit --omit=dev --json` (depois) | exit 1. Contagens "depois" abaixo. |
| 8 | `npm run lint` | **Passou**: "No ESLint warnings or errors". |
| 9 | `npm run build` | **Passou**. Todas as rotas geradas (estáticas e dinâmicas). |

## 3. Decisão de aplicar o fix global

O dry-run imprime "Will install next@16.4.5" e "Will install fabric@7.4.0", mas essas linhas são sugestões de `--force`. O `npm audit fix` sem `--force` não as aplica. A simulação (etapa 4) confirmou isso no lock.

Os 19 pacotes que mudariam, com a versão antes → depois:

| Pacote | Antes | Depois | Tipo |
|---|---|---|---|
| brace-expansion | 2.1.2 | 2.1.7 | patch (alvo) |
| brace-expansion | 5.0.7 | 5.0.12 | patch (alvo) |
| js-yaml | 4.3.0 | 4.3.2 | patch (alvo) |
| nanoid | 3.3.16 | 3.3.20 | patch (alvo) |
| postcss-selector-parser | 6.1.4 | 6.1.5 | patch (alvo) |
| source-map-js | 1.2.1 | 1.2.2 | patch (alvo) |
| minimatch | 10.2.5 | 10.2.6 | patch |
| postcss | 8.5.19 | 8.5.32 | minor (mesma major) |
| @eslint-community/eslint-utils | 4.9.1 | 4.10.1 | minor |
| @typescript-eslint/* (11 pacotes: eslint-plugin, parser, type-utils, utils, typescript-estree, project-service, scope-manager, tsconfig-utils, types, visitor-keys) | 8.64.0 | 8.72.1 | minor (mesma major, dev) |

Nenhum pacote de next, fabric, react, react-dom, eslint ou eslint-config-next mudou. Por isso o fix global foi aplicado, e não os `npm update` individuais.

Nota de rastreabilidade: o dry-run informou "added 43 packages". A comparação do lock (que compara versão por caminho) não encontrou pacotes novos nem removidos; só as 19 trocas de versão acima. Não reconciliei a contagem do npm com o diff; o diff real do lock é o que vale.

## 4. Versões antes / depois

| Pacote direto | Antes | Depois |
|---|---|---|
| next | 14.2.35 | 14.2.35 |
| react | 18.3.1 | 18.3.1 |
| react-dom | 18.3.1 | 18.3.1 |
| fabric | 6.9.1 | 6.9.1 |
| eslint | 8.57.1 | 8.57.1 |
| eslint-config-next | 14.2.35 | 14.2.35 |

`package.json` sem alteração.

## 5. Contagens do `npm audit` (vulnerabilidades por severidade)

| Escopo | Momento | Critical | High | Moderate | Low | Total |
|---|---|---:|---:|---:|---:|---:|
| Tudo | antes | 2 | 11 | 17 | 0 | 30 |
| Tudo | depois | 2 | 8 | 16 | 0 | 26 |
| Produção (`--omit=dev`) | antes | 2 | 7 | 4 | 0 | 13 |
| Produção (`--omit=dev`) | depois | 2 | 5 | 3 | 0 | 10 |

### Por pacote (o que saiu da lista)

| Pacote | Antes | Depois |
|---|---|---|
| js-yaml | high (dev) | corrigido |
| nanoid | high (prod) | corrigido |
| source-map-js | high (prod) | corrigido |
| postcss-selector-parser | moderate (prod) | corrigido |
| brace-expansion 2.x / 5.x | high | corrigido nessas cópias |
| brace-expansion 1.1.16 | high | **ainda vulnerável** (≤ 1.1.20). Dev via `eslint@8 → minimatch@3`; prod via cadeia `fabric 6 → canvas → @mapbox/node-pre-gyp → rimraf/glob/minimatch`. |

Ainda na lista (depois), sem correção sem major: next (crítico), tar (crítico, via fabric), fabric (high), canvas, @mapbox/node-pre-gyp, rimraf, glob, minimatch, postcss (dentro do next), e os pacotes de lint (eslint 8, eslint-config-next, @typescript-eslint, eslint-plugin-*, @next/eslint-plugin-next).

## 6. O que continua pendente

- **Next.js 14.2.35 (crítico, runtime):** correção só em 15.5.28+ ou 16.x. Exige avaliar React 19 (o projeto pina `react ^18`). Tarefa própria, conforme DEC-32 item 2.
- **fabric 6.9.1 → 7.4.0 (major):** remove a cadeia `canvas`/`tar`/`rimraf`/`glob`/`brace-expansion 1.x` de produção. Exige adaptar `components/photo-annotation-editor.tsx` à API v7 e teste do editor (RF-14). DEC-32 item 3.
- **Lint toolchain (eslint 8 → 9, @typescript-eslint):** dev-only, DEC-32 item 4 (opcional).
- **brace-expansion 1.1.16:** só se resolve com as mudanças acima. Não há fix sem major para essa cópia.

## 7. Status

- `npm run lint`: **passou**.
- `npm run build`: **passou**.
- Backend: não tocado nesta tarefa.

## 8. Propostas (não registradas em decisoes.md)

- **Proposta E:** registrar em DEC-32 (no fechamento de lote) que o item 1 foi aplicado com exceção: brace-expansion 1.1.16 permanece até as tarefas dos itens 2–4. Não há ação adicional agora.
- **Proposta F:** o item 1 da DEC-32 não pede nada além do que foi feito. Se o dono quiser zerar os achados de dev sem major, a alternativa é só o item 4 (toolchain de lint), que é major.
