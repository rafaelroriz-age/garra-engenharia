# 03_frontend

Aplicação **Next.js 14 (App Router) PWA** — interface web/mobile-first do sistema de automação de relatórios prediais.

> Scaffold inicial implementado (BL-03). Estrutura conforme [00_docs/arquitetura.md](../00_docs/arquitetura.md#7-estrutura-de-pastas-do-repositório) (Seção 7). Formulários com integração real à API, autenticação e regras de negócio chegam nas tarefas seguintes do backlog (BL-06, BL-08, BL-09...).

## Estrutura atual

```
03_frontend/
├── app/
│   ├── (auth)/login/            # placeholder de login (RNF-05, BL-06)
│   ├── dashboard/                # placeholder do Dashboard (RF-07, BL-16)
│   ├── edificacoes/              # placeholder do CRUD de edificações (RF-01, BL-08)
│   ├── contratos/                # placeholder do CRUD de contratos (RF-02, BL-09)
│   ├── inspecoes/[id]/
│   │   ├── visitas/              # placeholder de visitas do RFO (RF-03, BL-10)
│   │   ├── ocorrencias/          # placeholder de ocorrências (RF-04, BL-14)
│   │   └── relatorio/            # placeholder de geração de relatório (RF-06, BL-12/13)
│   ├── layout.tsx                # layout raiz: fontes (Inter/Manrope), metadata, PWA
│   └── page.tsx                  # página inicial navegável (hub de rotas)
├── components/
│   ├── ui/                       # shadcn/ui (button, card, badge, sheet, avatar, skeleton...)
│   ├── layout/
│   │   ├── nav-items.ts          # itens de navegação principal
│   │   └── app-shell.tsx         # sidebar desktop + menu mobile (Sheet), a11y
│   ├── page-header.tsx           # cabeçalho padrão de tela
│   └── under-construction.tsx    # placeholder padrão para telas ainda não implementadas
├── public/
│   ├── manifest.json             # manifest da PWA (display: standalone)
│   └── icon.svg                  # ícone placeholder (logo real do cliente pendente)
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

Abre em `http://localhost:3000`. Todas as rotas acima (e a página inicial, que lista links para cada uma) já carregam sem erro — apenas com conteúdo placeholder ("Em construção"), sem formulários nem integração com a API ainda.

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

## Notas de implementação

- **UI kit**: [shadcn/ui](https://ui.shadcn.com) (CLI clássica `2.10.0`, estilo `new-york`, Tailwind v3.4 — **não** a v4/"Nova" preset, incompatível com este projeto).
- **Ícones da PWA**: `public/icon.svg` é um placeholder (bloco navy + "G" laranja) até a entrega do logo oficial do cliente. Ao receber o arquivo real, gere os PNGs 192×192/512×512 e atualize `public/manifest.json`.
- **Cores/fontes**: extraídas dos wireframes em [02_prototipos/](../02_prototipos/) (navy `#1e3a5f`, laranja `#f97316`; fontes Inter + Manrope).
- **Rotas de `inspecoes/[id]/*`**: não aparecem na navegação global (`components/layout/nav-items.ts`) — são acessadas a partir do contexto de uma edificação/contrato.

## Referências

- Stack, arquitetura de frontend e contratos de API: [00_docs/arquitetura.md](../00_docs/arquitetura.md) (Seções 7, 9-11)
- Fluxos de usuário e wireframes de referência: [02_prototipos/](../02_prototipos/)
- Prompt de scaffold: [.github/prompts/16-scaffold-frontend-nextjs-pwa.prompt.md](../.github/prompts/16-scaffold-frontend-nextjs-pwa.prompt.md)

## Convenção de execução (DEC-09)

Comandos `npm`/`next` deste app são executados a partir desta pasta (`03_frontend/`). O `Dockerfile` de desenvolvimento também vive aqui; o `docker-compose.yml` que o referencia está em [05_infra/](../05_infra/) (build context `../03_frontend`).

