import { test, expect, type Page, type Route } from "@playwright/test";

/**
 * Portal do Cliente — controle de acesso por perfil na UI (BL-32, RN-14).
 *
 * Só `cliente` vê o portal; `auditor`/`auxiliar` são levados à home interna
 * (`/dashboard`) sem que nenhum dado do portal seja buscado ou exibido; sem
 * sessão, vão ao login. API mockada com `page.route` (sem backend real).
 */

const API = "**/api/v1";
const ED_A = "11111111-1111-4111-8111-111111111111";

const edificacoes = [
  { id: ED_A, nome: "Edifício Alfa", endereco: "Rua A, 1", created_at: "2026-01-01T00:00:00Z" },
];

const json = (route: Route, body: unknown, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

/** Simula usuário logado (token no localStorage, como o login faz) com o perfil dado em `GET /auth/me`. */
async function autenticar(page: Page, role: "cliente" | "auditor" | "auxiliar") {
  await page.addInitScript(() => window.localStorage.setItem("garra:access_token", "token-fake-e2e"));
  await page.route(`${API}/auth/me`, (route) =>
    json(route, { id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", nome: "Usuário Mock", email: "mock@x.com", ativo: true, role })
  );
}

/**
 * Registra mocks genéricos (qualquer rota da API responde lista vazia) e conta
 * as chamadas a `/portal/*`. Devem ser registrados ANTES dos específicos.
 */
async function mockApi(page: Page) {
  const chamadasPortal: string[] = [];
  await page.route(`${API}/**`, (route) => {
    if (route.request().url().includes("/auth/me")) return route.fallback();
    return json(route, []);
  });
  await page.route(`${API}/portal/**`, (route) => {
    chamadasPortal.push(route.request().url());
    return route.fallback();
  });
  await page.route(`${API}/portal/edificacoes`, (route) => {
    chamadasPortal.push(route.request().url());
    return json(route, edificacoes);
  });
  return chamadasPortal;
}

test.describe("Portal do Cliente — controle de perfil na UI (BL-32)", () => {
  test("(1) auditor que abre /portal vai para a home interna sem ver dados do portal", async ({ page }) => {
    await autenticar(page, "auditor");
    const chamadasPortal = await mockApi(page);

    await page.goto("/portal");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    // seletor específico do portal (o dashboard também tem um campo "Edificação")
    await expect(page.locator("#portal-edificacao")).toHaveCount(0);
    await expect(page.getByText("Visitas realizadas", { exact: true })).toHaveCount(0);
    expect(chamadasPortal).toHaveLength(0);
  });

  test("(1b) auxiliar que abre /portal/documentos também é levado à home interna", async ({ page }) => {
    await autenticar(page, "auxiliar");
    const chamadasPortal = await mockApi(page);

    await page.goto("/portal/documentos");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect(page.locator("#portal-edificacao")).toHaveCount(0);
    await expect(page.getByText("Nenhum documento emitido até o momento.")).toHaveCount(0);
    expect(chamadasPortal).toHaveLength(0);
  });

  test("(2) cliente vê o portal normalmente", async ({ page }) => {
    await autenticar(page, "cliente");
    const chamadasPortal = await mockApi(page);
    await page.route(`${API}/portal/edificacoes/*/acompanhamento`, (route) =>
      json(route, { edificacao_id: ED_A, edificacao_nome: "Edifício Alfa", contratos: [] })
    );
    await page.route(`${API}/portal/edificacoes/*/dashboard`, (route) =>
      json(route, {
        edificacao_id: ED_A,
        edificacao_nome: "Edifício Alfa",
        conformidade_por_sistema: [],
        grau_risco_por_sistema: [],
        gravidade_por_subsistema: [],
      })
    );

    await page.goto("/portal");

    await expect(page).toHaveURL(new RegExp(`/portal/?\\?edificacaoId=${ED_A}`));
    await expect(page.getByText("Nenhum contrato em andamento para esta edificação.")).toBeVisible();
    await expect(page.getByLabel("Edificação")).toHaveValue(ED_A);
    await expect(page.getByLabel("Edificação").locator("option")).toHaveText(["Edifício Alfa"]);
    expect(chamadasPortal.length).toBeGreaterThan(0);
  });

  test("(3) sem sessão, /portal vai para o login", async ({ page }) => {
    await mockApi(page);

    await page.goto("/portal");

    await expect(page).toHaveURL(/\/login\/?$/);
  });
});
