import { defineConfig, devices } from "@playwright/test";

/**
 * Config próprio do E2E offline da DEC-26 (T78/R-22). Não altera `playwright.config.ts`.
 *
 * O Service Worker só registra em build de produção, então o `webServer` faz `npm run build` e
 * serve `out/`. Como o app usa `output: "export"`, `next start` não serve o export; usa-se
 * `e2e/servir-out.mjs` (Node puro). A API é 100% mockada no spec (`context.route`): não precisa de
 * backend. Descoberta de API desligada (NEXT_PUBLIC_API_DISCOVERY_URL vazio) para que a falha de
 * rede apareça como erro explícito, não como modo leitura (DEC-57).
 *
 * Execução (a partir de 03_frontend/):  npx playwright test -c playwright.offline.config.ts
 */
export const PORTA_OFFLINE = Number(process.env.E2E_OFFLINE_PORTA ?? 3120);
export const API_OFFLINE = "http://api.e2e.test:8000/api/v1";

export default defineConfig({
  testDir: "./e2e",
  testMatch: /offline-dec26\.spec\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  timeout: 90_000,
  use: {
    baseURL: `http://localhost:${PORTA_OFFLINE}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run build && node e2e/servir-out.mjs",
    url: `http://localhost:${PORTA_OFFLINE}/login/`,
    reuseExistingServer: !process.env.CI,
    timeout: 600_000,
    env: {
      E2E_OFFLINE_PORTA: String(PORTA_OFFLINE),
      NEXT_PUBLIC_API_URL: API_OFFLINE,
      NEXT_PUBLIC_API_DISCOVERY_URL: "",
      NEXT_PUBLIC_BASE_PATH: "",
    },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
