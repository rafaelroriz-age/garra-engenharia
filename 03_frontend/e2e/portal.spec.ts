import { test, expect, type Page, type Route } from "@playwright/test";

/**
 * Portal do Cliente (RF-13, RN-14, BL-32/BL-33) — E2E com API mockada.
 *
 * Nenhum backend real: toda chamada à API é interceptada por `page.route`.
 * Os formatos de resposta seguem exatamente o que `app/portal/*` consome
 * (`lib/types.ts`: PortalAcompanhamento, PortalRelatorio, PortalDownload).
 */

const API = "**/api/v1";
const ED_A = "11111111-1111-4111-8111-111111111111";
const ED_B = "22222222-2222-4222-8222-222222222222";
const CONTRATO = "33333333-3333-4333-8333-333333333333";
const REL_1 = "44444444-4444-4444-8444-444444444444";
const REL_2 = "55555555-5555-4555-8555-555555555555";

const edificacoes = [
  { id: ED_A, nome: "Edifício Alfa", endereco: "Rua A, 1", created_at: "2026-01-01T00:00:00Z" },
  { id: ED_B, nome: "Edifício Beta", endereco: "Rua B, 2", created_at: "2026-01-02T00:00:00Z" },
];

const acompanhamento = {
  edificacao_id: ED_A,
  edificacao_nome: "Edifício Alfa",
  contratos: [
    {
      contrato_id: CONTRATO,
      numero: "CT-2026-007",
      tipo_servico: "LTIP",
      status: "ativo",
      data_inicio: "2026-02-10T12:00:00Z",
      inspecao_id: "66666666-6666-4666-8666-666666666666",
      inspecao_status: "em_andamento",
      total_visitas: 4,
      total_ocorrencias: 7,
      ocorrencias_por_grau_risco: { minimo: 3, medio: 2, critico: 2 },
      visitas: [
        {
          id: "77777777-7777-4777-8777-777777777771",
          seq_numero: 1,
          data: "2026-02-15T12:00:00Z",
          servicos_executados: "Vistoria de fachada",
          total_fotos: 12,
        },
      ],
      ocorrencias: [
        {
          id: "88888888-8888-4888-8888-888888888881",
          seq_numero: 1,
          sistema_nome: "Estrutura",
          subsistema_nome: "Pilares",
          localizacao: "Subsolo 2",
          situacao: "aberta",
          grau_risco: "CRITICO",
        },
      ],
    },
  ],
};

const dashboard = {
  edificacao_id: ED_A,
  edificacao_nome: "Edifício Alfa",
  conformidade_por_sistema: [],
  grau_risco_por_sistema: [
    { sistema_id: "99999999-9999-4999-8999-999999999991", sistema_nome: "Estrutura", minimo: 1, medio: 1, critico: 2 },
    { sistema_id: "99999999-9999-4999-8999-999999999992", sistema_nome: "Elétrica", minimo: 2, medio: 1, critico: 3 },
  ],
  gravidade_por_subsistema: [],
};

const relatorios = [
  {
    id: REL_1,
    versao: "v3",
    tipo: "LTIP",
    status: "emitido",
    emitido_em: "2026-03-20T12:00:00Z",
    tem_pdf: true,
    tem_docx: false,
    inspecao_id: "66666666-6666-4666-8666-666666666666",
    contrato_id: CONTRATO,
    contrato_numero: "CT-2026-007",
    edificacao_id: ED_A,
    edificacao_nome: "Edifício Alfa",
  },
  {
    id: REL_2,
    versao: "v1",
    tipo: "RFO",
    status: "emitido",
    emitido_em: null,
    tem_pdf: true,
    tem_docx: true,
    inspecao_id: "66666666-6666-4666-8666-666666666666",
    contrato_id: CONTRATO,
    contrato_numero: "CT-2026-007",
    edificacao_id: ED_A,
    edificacao_nome: "Edifício Alfa",
  },
];

/** Alerta da API (exclui o route-announcer do Next, que também tem role=alert). */
const alertaApi = (page: Page) => page.locator("div[role=alert]:not(#__next-route-announcer__)");

const json = (route: Route, body: unknown, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

const problema = (route: Route, status: number, title: string, detail: string) =>
  route.fulfill({
    status,
    contentType: "application/problem+json",
    body: JSON.stringify({ title, status, detail }),
  });

/** Simula usuário logado (token no localStorage, como o login faz) e `GET /auth/me` com o perfil dado. */
async function autenticar(page: Page, role: "cliente" | "auditor" | "auxiliar") {
  await page.addInitScript(() => window.localStorage.setItem("garra:access_token", "token-fake-e2e"));
  await page.route(`${API}/auth/me`, (route) =>
    json(route, { id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", nome: "Usuário Mock", email: "mock@x.com", ativo: true, role })
  );
}

async function mockPortal(page: Page) {
  await page.route(`${API}/portal/edificacoes`, (route) => json(route, edificacoes));
  await page.route(`${API}/portal/edificacoes/*/acompanhamento`, (route) => json(route, acompanhamento));
  await page.route(`${API}/portal/edificacoes/*/dashboard`, (route) => json(route, dashboard));
  await page.route(`${API}/portal/relatorios`, (route) => json(route, relatorios));
}

test.describe("Portal do Cliente (API mockada)", () => {
  test("(a) cliente vê a lista de edificações do portal", async ({ page }) => {
    await autenticar(page, "cliente");
    await mockPortal(page);

    await page.goto("/portal");

    const seletor = page.getByLabel("Edificação");
    await expect(seletor.locator("option")).toHaveText(["Edifício Alfa", "Edifício Beta"]);
    // a primeira edificação é selecionada automaticamente via redirect
    await expect(page).toHaveURL(new RegExp(`/portal/?\\?edificacaoId=${ED_A}`));
    await expect(seletor).toHaveValue(ED_A);
    // navegação específica do portal
    const nav = page.getByRole("navigation", { name: "Navegação principal" });
    await expect(nav.getByRole("link", { name: "Acompanhamento" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Meus documentos" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Contratos" })).toHaveCount(0);
  });

  test("(b) abre o acompanhamento e vê os números mockados", async ({ page }) => {
    await autenticar(page, "cliente");
    await mockPortal(page);

    await page.goto(`/portal?edificacaoId=${ED_A}`);

    const card = (titulo: string) =>
      page
        .getByText(titulo, { exact: true })
        .locator("xpath=../..");
    await expect(page.getByText("Visitas realizadas", { exact: true })).toBeVisible();
    await expect(card("Visitas realizadas")).toContainText("4");
    await expect(card("Ocorrências")).toContainText("7");
    // crítico = soma de grau_risco_por_sistema.critico do dashboard (2 + 3)
    await expect(card("Grau de risco crítico")).toContainText("5");

    await expect(page.getByText("Contrato CT-2026-007")).toBeVisible();
    await expect(page.getByText("Vistoria de fachada")).toBeVisible();
    await expect(page.getByText("Estrutura / Pilares")).toBeVisible();
    await expect(page.getByText("Subsolo 2")).toBeVisible();
    await expect(page.getByText("CRITICO", { exact: true })).toBeVisible();
    await expect(page.getByText(/crítico: 2, médio: 2, mínimo: 3/)).toBeVisible();
  });

  test("(c) documentos: lista relatórios e o download usa a URL pré-assinada sem expor a chave do storage", async ({
    page,
    context,
  }) => {
    await autenticar(page, "cliente");
    await mockPortal(page);

    const chaveStorage = "relatorios/chave-secreta-do-bucket/laudo-v3.pdf";
    const urlPreAssinada = "https://storage.exemplo.test/presigned/abc123?X-Signature=assinatura";
    let downloadChamado = 0;
    await page.route(`${API}/portal/relatorios/${REL_1}/download/pdf`, (route) => {
      downloadChamado += 1;
      return json(route, { relatorio_id: REL_1, formato: "pdf", url: urlPreAssinada, expira_em_segundos: 300 });
    });
    // o destino da URL pré-assinada não deve sair para a rede
    await context.route("https://storage.exemplo.test/**", (route) =>
      route.fulfill({ status: 200, contentType: "text/plain", body: "pdf-fake" })
    );

    await page.goto("/portal/documentos");

    const linhas = page.getByRole("row");
    await expect(linhas.filter({ hasText: "LTIP" })).toContainText("Edifício Alfa");
    await expect(linhas.filter({ hasText: "LTIP" })).toContainText("CT-2026-007");
    await expect(linhas.filter({ hasText: "LTIP" })).toContainText("v3");
    await expect(linhas.filter({ hasText: "RFO" })).toContainText("v1");
    // relatório sem DOCX: botão desabilitado
    await expect(linhas.filter({ hasText: "LTIP" }).getByRole("button", { name: "DOCX" })).toBeDisabled();

    const [popup] = await Promise.all([
      page.waitForEvent("popup"),
      linhas.filter({ hasText: "LTIP" }).getByRole("button", { name: "PDF" }).click(),
    ]);
    expect(downloadChamado).toBe(1);
    await popup.waitForLoadState("domcontentloaded").catch(() => undefined);
    expect(popup.url()).toBe(urlPreAssinada);

    // a chave do objeto no storage nunca aparece na interface
    await expect(page.locator("body")).not.toContainText(chaveStorage);
    await expect(page.locator("body")).not.toContainText("chave-secreta-do-bucket");
  });

  test("(d1) estado vazio: sem edificações e sem documentos", async ({ page }) => {
    await autenticar(page, "cliente");
    await page.route(`${API}/portal/edificacoes`, (route) => json(route, []));
    await page.route(`${API}/portal/relatorios`, (route) => json(route, []));

    await page.goto("/portal");
    await expect(page.getByText(/Nenhuma edificação vinculada ao seu acesso/)).toBeVisible();

    await page.goto("/portal/documentos");
    await expect(page.getByText("Nenhum documento emitido até o momento.")).toBeVisible();
  });

  test("(d2) estado vazio: edificação sem contratos", async ({ page }) => {
    await autenticar(page, "cliente");
    await mockPortal(page);
    await page.route(`${API}/portal/edificacoes/*/acompanhamento`, (route) =>
      json(route, { edificacao_id: ED_A, edificacao_nome: "Edifício Alfa", contratos: [] })
    );

    await page.goto(`/portal?edificacaoId=${ED_A}`);
    await expect(page.getByText("Nenhum contrato em andamento para esta edificação.")).toBeVisible();
  });

  test("(d3) erro 404 no acompanhamento mostra o alerta da API", async ({ page }) => {
    await autenticar(page, "cliente");
    await mockPortal(page);
    await page.route(`${API}/portal/edificacoes/*/acompanhamento`, (route) =>
      problema(route, 404, "Não encontrado", "Edificação não encontrada.")
    );

    await page.goto(`/portal?edificacaoId=${ED_B}`);
    const alerta = alertaApi(page);
    await expect(alerta).toContainText("Não encontrado");
    await expect(alerta).toContainText("Edificação não encontrada.");
  });

  test("(d4) erro 403 na lista de documentos e no download", async ({ page }) => {
    await autenticar(page, "cliente");
    await page.route(`${API}/portal/relatorios`, (route) =>
      problema(route, 403, "Acesso negado", "Sem permissão para listar documentos.")
    );
    await page.goto("/portal/documentos");
    await expect(alertaApi(page)).toContainText("Acesso negado");
    await expect(alertaApi(page)).toContainText("Sem permissão para listar documentos.");

    // download negado (403) com a lista carregada
    await page.unroute(`${API}/portal/relatorios`);
    await page.route(`${API}/portal/relatorios`, (route) => json(route, relatorios));
    await page.route(`${API}/portal/relatorios/${REL_1}/download/pdf`, (route) =>
      problema(route, 403, "Acesso negado", "Relatório de outro contratante.")
    );
    await page.goto("/portal/documentos");
    await page
      .getByRole("row")
      .filter({ hasText: "LTIP" })
      .getByRole("button", { name: "PDF" })
      .click();
    await expect(alertaApi(page)).toContainText("Relatório de outro contratante.");
  });

  test("(e) perfil auditor: o menu global não tem item do portal e a UI não bloqueia /portal (lacuna)", async ({
    page,
  }) => {
    await autenticar(page, "auditor");
    await mockPortal(page);
    await page.route(`${API}/dashboard**`, (route) => json(route, []));
    await page.route(`${API}/edificacoes**`, (route) => json(route, []));

    // menu global (fora de /portal): não há link para o portal para nenhum perfil
    await page.goto("/edificacoes");
    const nav = page.getByRole("navigation", { name: "Navegação principal" });
    await expect(nav.getByRole("link", { name: "Edificações" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Acompanhamento" })).toHaveCount(0);
    await expect(nav.getByRole("link", { name: "Meus documentos" })).toHaveCount(0);

    // Comportamento real: acessando /portal por URL, não há redirecionamento por perfil
    // (nem `useUsuarioAtual` é usado em app/portal ou no AppShell). A proteção é só do backend (403).
    await page.route(`${API}/portal/edificacoes`, (route) =>
      problema(route, 403, "Acesso negado", "Perfil sem acesso ao portal.")
    );
    await page.goto("/portal");
    await expect(page).toHaveURL(/\/portal\/?$/);
    await expect(alertaApi(page)).toContainText("Perfil sem acesso ao portal.");
  });
});
