import { defineConfig, devices } from "@playwright/test";

/**
 * Config próprio do E2E do Service Worker com basePath do Pages (R-22, T90). Não altera
 * `playwright.config.ts`.
 *
 * O spec `e2e/sw-basepath.spec.ts` builda o export estático com `NEXT_PUBLIC_BASE_PATH=/garra-engenharia`
 * (NODE_ENV=production, exigido para o SW registrar) e sobe ele mesmo um servidor estático mínimo em Node
 * servindo `out/` sob esse prefixo. Por isso não há `webServer` aqui. A API é toda mockada
 * (`context.route`); não precisa de backend nem de rede.
 *
 * Execução (a partir de 03_frontend/):
 *   npx playwright test -c playwright.sw.config.ts
 */
export const PORTA_SW = Number(process.env.E2E_SW_PORTA ?? 3110);
export const BASE_PATH_SW = "/garra-engenharia";

export default defineConfig({
  testDir: "./e2e",
  testMatch: /sw-basepath\.spec\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  timeout: 120_000,
  use: {
    baseURL: `http://localhost:${PORTA_SW}${BASE_PATH_SW}/`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
