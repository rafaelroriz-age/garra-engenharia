# 03_frontend

Aplicação **Next.js 14 (App Router) PWA** que funciona como interface web/mobile-first do sistema de automação de relatórios prediais.

> O frontend já está em uma fase funcional para o fluxo principal do produto: autenticação, dashboard, CRUD de edificações e contratos, gestão de inspeções/visitas/ocorrências, upload e anotação de fotos, além do portal do cliente. O que ainda depende de integração e do recebimento de templates originais do cliente é a geração final de relatórios em PDF/DOCX com fidelidade total.

## Estrutura atual

```
03_frontend/
├── app/
│   ├── (auth)/login/            # tela de login autenticada via JWT
│   ├── dashboard/                # dashboard de saúde por edificação e sistema predial
│   ├── edificacoes/              # CRUD de edificações e anexos de documentos técnicos
│   ├── contratos/                # CRUD de contratos, executoras, ARTs e vínculos com inspeção
│   ├── inspecoes/[id]/
│   │   ├── visitas/              # cadastro de visitas, equipe, serviços, medições e mão de obra
│   │   ├── ocorrencias/          # lançamento de ocorrências, classificação e fotos
│   │   └── relatorio/            # espaço reservado para o pipeline de relatório final
│   ├── portal/                   # portal do cliente com acompanhamento e documentos
│   ├── layout.tsx                # layout raiz: fontes (Inter/Manrope), metadata, PWA
│   └── page.tsx                  # página inicial navegável (hub de rotas)
├── components/
│   ├── ui/                       # shadcn/ui (button, card, badge, sheet, avatar, skeleton...)
│   ├── brand/
│   │   └── logo.tsx              # componente `<Logo variant="..." />` — única forma de renderizar a marca oficial
│   ├── layout/
│   │   ├── nav-items.ts          # itens de navegação principal
│   │   └── app-shell.tsx         # sidebar desktop + menu mobile (Sheet), a11y
│   ├── legenda-ia-painel.tsx     # painel «Gerar legenda com IA»: rascunho editável, alertas, pendências e aprovação (BL-35)
│   ├── page-header.tsx           # cabeçalho padrão de tela
│   └── under-construction.tsx    # placeholder padrão para telas ainda não implementadas
├── public/
│   ├── brand/
│   │   ├── logo-garra*.svg        # marca vetorizada do JPEG oficial (gerada por `app.scripts.build_brand_assets`, DEC-30)
│   │   └── logos/                # JPEGs originais do cliente — referência histórica, ver convenção de uso abaixo
│   ├── manifest.json             # manifest da PWA (display: standalone)
│   └── icon.svg                  # símbolo derivado do skyline oficial (favicon/PWA, BL-41)
├── Dockerfile                    # imagem de desenvolvimento (`next dev`)
├── components.json               # config shadcn/ui (style "new-york", Tailwind v3)
└── tailwind.config.ts / app/globals.css  # tema (cores da marca + tokens shadcn)
```

## Como rodar localmente (sem Docker)

```powershell
cd 03_frontend
npm install
npm run dev
```

Abre em `http://localhost:3000`. As telas principais já carregam com formulários e integração real com a API. Os templates de relatório (RFO e LTIP) já são derivados dos originais do cliente (ADR-13), mas o RFIP e o pipeline de renderização do LTIP seguem pendentes.

## Como rodar via Docker Compose

```powershell
cd 05_infra
docker compose up -d --build frontend
```

## Como validar

```powershell
cd 03_frontend
npm run build   # build de produção — valida todas as rotas
npm run lint    # ESLint
```

> **Vulnerabilidades (T03, 2026-11-04):** `npm audit` aponta 30 pacotes (2 críticos, 11 altos, 17 moderados), 13 deles em produção; o principal é `next` 14.2.35, cuja correção está só em 15.5.x/16.x. **Atualização (T07):** o `npm audit fix` sem `--force` já foi aplicado só ao `package-lock.json` (30 → 26 achados; produção 13 → 10); Next, fabric e `brace-expansion` 1.1.16 seguem pendentes, ver [npm-audit-fix.md](../00_docs/backlog-auto/npm-audit-fix.md). Não use `npm audit fix --force`. Análise e plano em [npm-audit.md](../00_docs/backlog-auto/npm-audit.md); ver R-12 e DEC-32 (proposta).

## Notas de implementação

- **UI kit**: [shadcn/ui](https://ui.shadcn.com) (CLI clássica `2.10.0`, estilo `new-york`, Tailwind v3.4 — **não** a v4/"Nova" preset, incompatível com este projeto).
- **Marca oficial "Garra Perícias e Avaliações" (BL-41/BL-19)**: vetorizada em SVG — `components/brand/garra-mark.tsx` (símbolo do skyline, `fill="currentColor"`) + texto real em `font-display` (Manrope), compostos por `components/brand/logo.tsx` (`<Logo variant="principal" | "horizontal" | "compacta" />`). Sem fundo embutido nem dimensões fixas de imagem: escala sem perda em qualquer tamanho e herda a cor certa da superfície via classe de texto (`text-primary` sobre fundo claro, `text-primary-foreground` sobre `bg-primary`).
	- `principal` → landing (Card institucional) e tela de login (fundo claro): ícone empilhado sobre o nome.
	- `horizontal` → header da landing (fundo navy, espaço horizontal amplo): ícone + nome em linha.
	- `compacta` → `AppShell` (sidebar desktop + topbar/menu mobile — espaço reduzido): ícone + nome em 2 linhas.

  Os 4 JPEGs originais do cliente permanecem em `public/brand/logos/` apenas como referência histórica (dimensões inconsistentes entre si e fundo/cores embutidos no arquivo) — **não são mais usados em nenhuma tela**; não importe esses arquivos diretamente em JSX/CSS. Desde 2026-09-17 (DEC-30/ADR-16), a marca completa também existe em vetor com fundo transparente em `public/brand/logo-garra.svg` (mais `logo-garra-negativa.svg` e `logo-garra-simbolo.svg`), gerada do JPEG oficial por `python -m app.scripts.build_brand_assets` — use esses arquivos quando precisar da marca com a tipografia original (ex.: documento impresso ou material enviado ao cliente); para a UI, prefira `<Logo />`, que recolore e escala melhor.
- **Ícone/favicon/PWA**: `public/icon.svg` usa o mesmo traço de skyline do `GarraMark`, em fundo ardósia (`#253341`) — legível em tamanhos pequenos onde a logo completa não caberia. `theme_color` do `manifest.json` e do `viewport` em `app/layout.tsx` foram alinhados ao mesmo tom.
- **Cores/fontes**: navy `#1e3a5f` (`--primary`) e laranja `#f97316` (`--brand-accent`) são a paleta funcional (botões, destaques, ícones dos cards da home) e agora também a paleta da marca vetorizada, via `text-primary`/`text-primary-foreground` — resolvendo a divergência de tom que antes existia entre os JPEGs (azul acinzentado/ardósia/creme) e o tema da aplicação. Fontes: Inter + Manrope.
- **Rotas de `inspecoes/[id]/*`**: não aparecem na navegação global (`components/layout/nav-items.ts`) — são acessadas a partir do contexto de uma edificação/contrato.

## Testes E2E (Playwright, BL-21)

Testes de ponta a ponta dos Fluxos 1 (RFO) e 2 (LTIP) de [00_docs/estudo-do-contexto.md](../00_docs/estudo-do-contexto.md#8-fluxos-principais), em `e2e/rfo.spec.ts` e `e2e/ltip.spec.ts`. Rodam contra uma instância local **já em execução** via `05_infra/docker-compose.yml` — não sobem a stack sozinhos.

### Pré-requisitos (stack local rodando e com dados mestre)

```powershell
cd 05_infra
Copy-Item .env.example .env   # se ainda não existir
docker compose up -d --build  # sobe postgres, minio, backend e frontend
docker compose ps             # confirme "healthy" em postgres/minio/backend

cd ..\04_backend
.venv\Scripts\Activate.ps1
alembic upgrade head                    # aplica as migrations (se ainda não aplicadas)
python -m app.scripts.seed_gabarito     # popula sistemas/subsistemas/tipos (RF-10) — idempotente
```

### Rodar os testes

```powershell
cd 03_frontend
npm install
npx playwright install --with-deps chromium   # 1x por máquina
npm run test:e2e                              # roda e2e/*.spec.ts (headless)
npm run test:e2e:ui                           # modo interativo (Playwright UI)
npm run test:e2e:report                       # abre o último relatório HTML
```

Variáveis opcionais (default já apontam para o `docker-compose.yml` local): `E2E_BASE_URL` (frontend, default `http://localhost:3000`) e `E2E_API_BASE_URL` (backend, default `http://localhost:8000/api/v1`).

### O que cada teste cobre

- **`rfo.spec.ts`**: login → cadastro de edificação → cadastro de contrato RFO (com executora e ART) → criação de visita com equipe/medições → upload de foto (via editor de anotação Fabric.js, DEC-19) → valida que a tela de Relatório mostra corretamente "Em construção" (RF-06 segue bloqueado por B-02/BL-12/BL-13 — o job de geração ainda não existe no backend).
- **`ltip.spec.ts`**: login → cadastro de edificação → cadastro de contrato LTIP → ocorrências em 2 sistemas prediais distintos, cada uma com classificação completa (RN-05) e foto → valida o dashboard de saúde (RF-07, BL-16) → mesma validação do placeholder de Relatório.

### Falhas de integração encontradas e corrigidas ao implementar estes testes (BL-21)

- **Fabric.js v6 API incompatível** (`components/photo-annotation-editor.tsx`): `Image.fromURL` no Fabric v6 retorna uma `Promise` (não aceita mais callback como no v5) — o código chamava a API antiga, então o callback nunca era invocado e o editor de anotação de fotos ficava travado para sempre em "Preparando editor..." em qualquer upload de foto (RF-14/BL-31). Corrigido para `await fabricLib.Image.fromURL(url, options)`.
- **Deadlock de montagem do `<canvas>`** (mesmo arquivo): o `<canvas>` só era renderizado quando `isLoading` virava `false`, mas nada definia `isLoading = false` sem o elemento `<canvas>` já montado (o efeito que carrega a imagem exige `canvasRef.current`) — travava por conta própria, independente do bug acima. Corrigido mantendo o `<canvas>` sempre montado (oculto via wrapper `hidden`, não removido do DOM).
- **`rte_id` vazio rejeitado pela API** (`app/contratos/contrato-form.tsx`): o campo opcional "RTE (ID)" enviava `""` quando não preenchido, mas o backend valida `rte_id` como UUID-ou-null e rejeita string vazia — qualquer contrato sem RTE informado falhava a criação. Corrigido para normalizar campos vazios para `null` antes do envio.
- **Sem forma de criar/consultar `Responsavel` via API**: o formulário de Contrato exige UUIDs de `Responsavel` (fiscal/executor) já existentes, mas não havia nenhum endpoint para isso — só era possível inserir via fixture de teste do backend. Criado `GET/POST /api/v1/responsaveis` (ver DEC-23 em [decisoes.md](../00_docs/projeto/decisoes.md)).
- **Sem navegação de Contrato para a Inspeção**: a página de detalhe do Contrato não tinha nenhum link para Visitas/Ocorrências/Relatório da Inspeção 1:1 associada (`ContratoDetail.inspecao` já vinha da API, mas não era usado). Adicionados os 3 links na tela.

## Referências

- Stack, arquitetura de frontend e contratos de API: [00_docs/arquitetura.md](../00_docs/arquitetura.md) (Seções 7, 9-11)
- Fluxos de usuário e wireframes de referência: [02_prototipos/](../02_prototipos/)
- Prompt de scaffold: [.github/prompts/16-scaffold-frontend-nextjs-pwa.prompt.md](../.github/prompts/16-scaffold-frontend-nextjs-pwa.prompt.md)

## Convenção de execução (DEC-09)

Comandos `npm`/`next` deste app são executados a partir desta pasta (`03_frontend/`). O `Dockerfile` de desenvolvimento também vive aqui; o `docker-compose.yml` que o referencia está em [05_infra/](../05_infra/) (build context `../03_frontend`).

