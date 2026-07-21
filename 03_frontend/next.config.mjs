/** @type {import('next').NextConfig} */
const nextConfig = {
  // `standalone` gera um bundle mínimo em `.next/standalone` (server.js +
  // apenas as dependências realmente usadas), necessário para o build de
  // produção em container (ver 03_frontend/Dockerfile.render e render.yaml).
  // Não afeta `next dev` nem o Dockerfile de desenvolvimento existente.
  output: "standalone",
};

export default nextConfig;
