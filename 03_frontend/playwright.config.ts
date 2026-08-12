import { defineConfig, devices } from "@playwright/test";

/**
 * Configuração de testes E2E (BL-21, RNF-06) — Playwright apontando para uma
 * instância local já em execução via `05_infra/docker-compose.yml` (frontend
 * em `http://localhost:3000`, backend em `http://localhost:8000/api/v1`).
 *
 * Este arquivo NÃO sobe a stack (`webServer`) — os testes assumem que
 * `docker compose up -d --build` já rodou, com migrations e seed do gabarito
 * aplicados (ver `03_frontend/e2e/README.md`). Isso reflete o pedido da
 * tarefa (BL-21): testar contra o ambiente local real, não um mock.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // os testes de fluxo criam dados próprios, mas rodar em série evita sobrecarregar o Postgres de dev
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  timeout: 60_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
