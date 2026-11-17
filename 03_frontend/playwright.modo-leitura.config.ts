import { defineConfig, devices } from "@playwright/test";

/**
 * Config próprio do E2E do modo leitura (DEC-57, T86). Não altera `playwright.config.ts`.
 *
 * O spec `e2e/modo-leitura-dec57.spec.ts` constrói o front estático (`out/`) com o basePath de
 * produção (`/garra-engenharia`) e `NEXT_PUBLIC_API_DISCOVERY_URL` apontando para o servidor
 * estático de teste, e ele mesmo sobe esse servidor (porta 3100: serve `out/` sob o basePath e
 * um diretório de dados com `api.json` e `snapshot.enc` locais, sem GitHub). Por isso não há
 * `webServer` aqui. Pré-requisito: backend em `http://localhost:8000` com
 * `BACKEND_CORS_ORIGINS` incluindo `http://localhost:3100`, migrations e `seed_admin` aplicados.
 *
 * Execução (a partir de 03_frontend/):
 *   npx playwright test -c playwright.modo-leitura.config.ts
 */
export const PORTA_MODO_LEITURA = Number(process.env.E2E_ML_PORTA ?? 3100);
export const BASE_PATH_MODO_LEITURA = "/garra-engenharia";

export default defineConfig({
  testDir: "./e2e",
  testMatch: /modo-leitura-dec57\.spec\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  timeout: 120_000,
  use: {
    // Barra final: `page.goto("login/")` (relativo) resolve dentro do basePath.
    baseURL: `http://localhost:${PORTA_MODO_LEITURA}${BASE_PATH_MODO_LEITURA}/`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
