# Campos Cidade e UF na Edificação — frontend (DEC-50)

Referência: DEC-50 P5 · migration `d3e7a1c5f9b2` (T97, backend). Escopo: somente `03_frontend/`.

## O que mudou (arquivo:linha)

- `03_frontend/lib/types.ts:34-37` — `Edificacao` ganha `cidade?: string | null` e `uf?: string | null` (`EdificacaoInput` deriva do tipo, então também os recebe).
- `03_frontend/app/edificacoes/edificacao-form.tsx`
  - `:32-33` estados `cidade` e `uf`, inicializados com o valor da edificação.
  - `:44-46` validação client-side: UF com 2 letras (`/^[A-Za-z]{2}$/`), senão erro no campo.
  - `:64-65` payload: `cidade` e `uf` enviados como `null` quando vazios; `uf` normalizada para maiúsculas.
  - `:136-170` campos Cidade (`maxLength=120`) e UF (`maxLength=2`, digitação forçada para maiúsculas) no grid CEP/Tipologia, com os mesmos `Input`/`Label` existentes.
  - Tratamento de 422: quando o erro vem no campo `uf` (ou `*.uf`), a mensagem exibida é "UF inválida. Informe a sigla de 2 letras do estado (ex.: SP)." — em português, independente do texto do backend.
- `03_frontend/app/edificacoes/page.tsx:157-165` — na coluna Endereço da lista, abaixo do endereço, aparece "Cidade / UF" quando existir.
- `03_frontend/app/edificacoes/detalhe/page.tsx:165-175` — no bloco "Dados da edificação", itens "Cidade" e "UF" exibidos somente quando preenchidos.

Nenhum componente novo foi criado; só `Input`, `Label` e a estrutura `dl`/`dd` já usada no detalhe.

## Comandos e saída

Antes: `node_modules` ausente no worktree; rodado `npm ci` em `03_frontend/` (apenas aviso `install-scripts` do `unrs-resolver`, sem erro).

```
> garra-frontend@0.1.0 lint
> next lint

✔ No ESLint warnings or errors
```
Exit code: 0.

```
> garra-frontend@0.1.0 build
> next build
...
Route (app)                              Size     First Load JS
├ ○ /edificacoes                         3.79 kB         133 kB
├ ○ /edificacoes/detalhe                 6.09 kB         120 kB
...
○  (Static)  prerendered as static content
```
Exit code: 0.

## Não testado

- Testes e2e (`03_frontend/e2e/edificacoes-contratos.spec.ts`) não foram executados; exigem backend e banco rodando.
- Comportamento real do 422 de UF contra a API não foi exercitado (o mapeamento assume que o backend retorna o campo `uf` em `errors[].field`; confirmar no primeiro teste manual).
- Nenhum teste unitário novo foi adicionado: o frontend não tem framework de teste unitário configurado no `package.json` verificado.
- Visual em telas estreitas (grid de 2 colunas nos campos) não foi inspecionado no navegador.

## Decisões propostas

- Nenhuma decisão nova. Sugestão para o integrador: o erro 422 de UF é mapeado no cliente por nome de campo; se o backend passar a usar outro identificador, ajustar `edificacao-form.tsx:` no bloco `err.errors.forEach`.
