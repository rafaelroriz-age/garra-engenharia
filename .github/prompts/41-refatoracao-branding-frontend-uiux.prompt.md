---
description: "Ativa o agente Especialista UI/UX para refatorar a identidade visual do frontend e aplicar as logos oficiais da Garra Perícias e Avaliações."
---
## Contexto
Tarefa BL-41 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 7.5 (Refino UI/UX e Branding do Frontend).

O frontend em `03_frontend/` está funcional, mas a marca ainda está inconsistente: existe um placeholder em `03_frontend/public/icon.svg`, textos legados com "Garra Engenharia" e soluções tipográficas improvisadas em pontos visíveis da interface.

Os assets oficiais recebidos do usuário já foram organizados em `03_frontend/public/brand/logos/` com os nomes:
- `logo-principal-fundo-claro.jpg`
- `logo-horizontal-negativa-fundo-preto.jpg`
- `logo-contorno-fundo-preto.jpg`
- `logo-compacta-negativa-fundo-ardosia.jpg`

Pontos já mapeados para revisão de branding:
- `03_frontend/app/layout.tsx`
- `03_frontend/app/page.tsx`
- `03_frontend/app/(auth)/login/page.tsx`
- `03_frontend/components/layout/app-shell.tsx`
- `03_frontend/public/manifest.json`
- `03_frontend/README.md`

Objetivo: aplicar a identidade oficial "Garra Perícias e Avaliações" nas superfícies públicas e autenticadas do app, sem alterar regras de negócio nem abrir uma frente de redesign genérico.

## Tarefa
Assuma o papel de **Especialista UI/UX**.

1. Audite todas as ocorrências visuais e técnicas da marca no frontend e complete a varredura se houver outros pontos além dos já mapeados.
2. Padronize o naming visível do produto para `Garra Perícias e Avaliações`, removendo ocorrências legadas de `Garra Engenharia` quando fizerem papel de marca na interface.
3. Substitua a marca improvisada atual (letra `G` em bloco + wordmark textual) por componentes reais de logo, preservando boa leitura e hierarquia visual.
4. Aplique a variante correta da logo por superfície:
   - `logo-principal-fundo-claro.jpg` em landing e blocos institucionais sobre fundo claro
   - `logo-horizontal-negativa-fundo-preto.jpg` em headers/áreas escuras com espaço horizontal suficiente
   - `logo-compacta-negativa-fundo-ardosia.jpg` em shell autenticado, navegação mobile e áreas com largura reduzida
   - `logo-contorno-fundo-preto.jpg` apenas como recurso decorativo opcional, nunca como marca principal em navegação, login, manifest ou favicon
5. Refatore landing page, tela de login e shell autenticado para aplicar a marca com consistência de escala, respiro, contraste e comportamento responsivo.
6. Revise `metadata`, `title`, `description`, `appleWebApp.title`, `manifest.name`, `manifest.short_name` e `icons` para refletirem a marca oficial.
7. Se a logo completa não for legível em tamanhos pequenos de PWA/favicon, derive um símbolo simplificado a partir do elemento gráfico oficial da marca. Não reutilize o placeholder atual nem uma letra solta genérica.
8. Mantenha a estrutura de assets em `03_frontend/public/brand/logos/` e, se precisar gerar derivados web (`png`/`svg`), salve-os no mesmo namespace de branding com nomes semânticos.
9. Atualize `03_frontend/README.md` com a convenção final de uso da marca e dos assets.
10. Valide visualmente os principais pontos de contato em desktop e mobile para garantir consistência entre marketing, autenticação e app autenticado.

## Saída Esperada
- Frontend com branding consistente e sem placeholder visual
- Logos oficiais aplicadas nos locais corretos do app e dos metadados/PWA
- Naming da marca alinhado entre UI, metadata e manifest
- README do frontend atualizado com a convenção de branding
- Resumo final: quais superfícies foram refatoradas, quais variantes da logo foram usadas em cada contexto e como validar visualmente

## Restrições
- NÃO altere fluxos de negócio, contratos de API, autenticação ou navegação funcional além do necessário para aplicar a marca.
- NÃO use a variante de contorno como logo principal em áreas pequenas ou críticas de navegação.
- NÃO deixe `public/icon.svg` como ativo principal da marca ao final da tarefa; substitua-o por asset derivado da identidade oficial, se necessário.
- Preserve a responsividade e a legibilidade em mobile.
- Leia os arquivos antes de modificá-los.