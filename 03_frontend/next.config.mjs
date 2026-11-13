/** @type {import('next').NextConfig} */

// Prefixo de URL do app. No GitHub Pages (site de projeto) o front é servido em
// https://rafaelroriz-age.github.io/garra-engenharia/, então o build de deploy
// define NEXT_PUBLIC_BASE_PATH=/garra-engenharia (ver
// .github/workflows/deploy-pages.yml). Vazio em dev e no docker-compose local.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig = {
  // Export estático (HTML/JS/CSS em `out/`) para hospedagem no GitHub Pages.
  // Só funciona porque o app é 100% client-side (todas as páginas são
  // "use client", auth via token em localStorage, sem API routes/middleware).
  // Rotas com ID usam query string (`?id=`) em vez de segmentos `[id]`.
  output: "export",
  basePath,
  // Gera `rota/index.html`, que o GitHub Pages serve em `/rota/` sem 404 no F5.
  trailingSlash: true,
  // O otimizador de imagens precisa de servidor; desligado no export estático.
  images: { unoptimized: true },
};

export default nextConfig;
