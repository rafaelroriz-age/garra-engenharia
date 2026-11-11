import { expect, test, type Page, type Route } from "@playwright/test";

import { API_BASE_URL } from "./helpers";

/**
 * Painel de legenda por IA (BL-35; RF-15, RN-16, RN-17) com a API **mockada** via `page.route`.
 *
 * Diferente de `rfo.spec.ts`/`ltip.spec.ts`, este teste não precisa de backend, banco nem
 * provedor de LLM: só do frontend em execução (`E2E_BASE_URL`). As respostas seguem o contrato
 * de `00_docs/backlog-auto/legenda-ia-endpoints.md` §2 (`FotoRead`, 503 `legenda-ia-indisponivel`).
 */

const INSPECAO_ID = "00000000-0000-4000-8000-000000000001";
const VISITA_ID = "00000000-0000-4000-8000-000000000002";
const FOTO_ID = "00000000-0000-4000-8000-000000000003";
const USUARIO_ID = "00000000-0000-4000-8000-000000000004";
const PNG_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

const fotoBase = {
  id: FOTO_ID,
  visita_id: VISITA_ID,
  ocorrencia_id: null,
  storage_key: "fotos/teste.png",
  url_publica: PNG_DATA_URL,
  legenda: "",
  origem: "upload_manual",
  ordem: 0,
  created_at: "2026-11-05T12:00:00Z",
  legenda_bruta: null,
  legenda_ia_sugerida: null,
  nivel_certeza_ia: null,
  status_validacao_ia: null,
  alertas_ia: null,
  pendencias_ia: null,
  legenda_ia_gerada_em: null,
  aprovado_por_id: null,
  aprovado_em: null,
};

const SUGESTAO = "Fissura diagonal no revestimento da fachada norte, próxima à janela do 2º pavimento.";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
};

async function responder(route: Route, status: number, body: unknown, contentType = "application/json") {
  if (route.request().method() === "OPTIONS") {
    await route.fulfill({ status: 204, headers: CORS_HEADERS });
    return;
  }
  await route.fulfill({ status, headers: CORS_HEADERS, contentType, body: JSON.stringify(body) });
}

async function prepararPagina(page: Page, role: "auditor" | "auxiliar" | "cliente") {
  await page.addInitScript(() => window.localStorage.setItem("garra:access_token", "token-e2e"));
  // Qualquer rota não mockada explicitamente devolve 404 (nunca toca um backend real).
  await page.route(`${API_BASE_URL}/**`, (route) =>
    responder(route, 404, { title: "Não mockado", status: 404 }, "application/problem+json")
  );
  await page.route(`${API_BASE_URL}/auth/me`, (route) =>
    responder(route, 200, { id: USUARIO_ID, nome: "Equipe E2E", email: "e2e@exemplo.com", ativo: true, role })
  );
  await page.route(`${API_BASE_URL}/inspecoes/${INSPECAO_ID}`, (route) =>
    responder(route, 200, {
      id: INSPECAO_ID,
      contrato_id: "00000000-0000-4000-8000-000000000005",
      tipo: "RFO",
      status: "em_andamento",
      created_at: "2026-11-05T12:00:00Z",
      visitas: [
        {
          id: VISITA_ID,
          inspecao_id: INSPECAO_ID,
          data: "2026-11-05",
          servicos_executados: "Vistoria de fachada",
          observacoes: null,
          seq_numero: 1,
          mao_obra: [],
          medicoes: [],
          fotos: [fotoBase],
        },
      ],
    })
  );
}

test.describe("Legenda por IA (BL-35)", () => {
  test("503 sem provedor de IA mostra mensagem clara e não oferece aprovação", async ({ page }) => {
    await prepararPagina(page, "auditor");
    await page.route(`${API_BASE_URL}/fotos/${FOTO_ID}/legenda-ia/gerar`, (route) =>
      responder(
        route,
        503,
        { type: "https://garra/erros/legenda-ia-indisponivel", title: "Service Unavailable", status: 503 },
        "application/problem+json"
      )
    );

    await page.goto(`/inspecoes/${INSPECAO_ID}/visitas`);
    await page.getByRole("button", { name: "Legenda com IA" }).click();

    await expect(page.getByText("só entra no relatório depois que você revisar o texto e aprovar")).toBeVisible();
    await page.getByRole("button", { name: "Gerar legenda com IA" }).click();

    await expect(page.getByText("Geração de legenda por IA indisponível")).toBeVisible();
    await expect(page.getByText("ainda não tem um provedor de IA configurado")).toBeVisible();
    await expect(page.getByRole("button", { name: "Aprovar legenda" })).toHaveCount(0);
  });

  test("gera rascunho, exige texto e confirmação, e aprova o texto revisado", async ({ page }) => {
    // DEC-42: só o auditor aprova (o auxiliar gera e edita o rascunho; ver legenda-ia-aprovacao.spec.ts).
    await prepararPagina(page, "auditor");
    let corpoGerar: unknown = null;
    let corpoAprovar: Record<string, unknown> | null = null;

    await page.route(`${API_BASE_URL}/fotos/${FOTO_ID}/legenda-ia/gerar`, (route) => {
      if (route.request().method() === "POST") corpoGerar = route.request().postDataJSON();
      return responder(route, 200, {
        ...fotoBase,
        legenda_bruta: "fissura fachada norte",
        legenda_ia_sugerida: SUGESTAO,
        status_validacao_ia: "rascunho",
        alertas_ia: ["Não é possível afirmar a causa só pela imagem."],
        pendencias_ia: ["Confirmar o pavimento no local."],
        legenda_ia_gerada_em: "2026-11-05T12:05:00Z",
      });
    });
    await page.route(`${API_BASE_URL}/fotos/${FOTO_ID}`, (route) => {
      if (route.request().method() === "PUT") corpoAprovar = route.request().postDataJSON();
      const legenda = (corpoAprovar?.legenda as string | undefined) ?? SUGESTAO;
      return responder(route, 200, {
        ...fotoBase,
        legenda,
        legenda_bruta: "fissura fachada norte",
        legenda_ia_sugerida: SUGESTAO,
        status_validacao_ia: "aprovada",
        aprovado_por_id: USUARIO_ID,
        aprovado_em: "2026-11-05T12:10:00Z",
      });
    });

    await page.goto(`/inspecoes/${INSPECAO_ID}/visitas`);
    await page.getByRole("button", { name: "Legenda com IA" }).click();
    await page.getByLabel("Anotação de campo (opcional)").fill("fissura fachada norte");
    await page.getByRole("button", { name: "Gerar legenda com IA" }).click();

    const campo = page.getByLabel("Legenda sugerida (editável)");
    await expect(campo).toHaveValue(SUGESTAO);
    expect(corpoGerar).toEqual({ legenda_bruta: "fissura fachada norte" });
    await expect(page.getByText("Rascunho — aguardando aprovação")).toBeVisible();
    await expect(page.getByText("Não é possível afirmar a causa só pela imagem.")).toBeVisible();
    await expect(page.getByText("Confirmar o pavimento no local.")).toBeVisible();

    const aprovar = page.getByRole("button", { name: "Aprovar legenda" });
    await campo.fill("   ");
    await expect(aprovar).toBeDisabled();

    const revisada = "Fissura diagonal no revestimento da fachada norte (2º pavimento).";
    await campo.fill(revisada);
    await expect(aprovar).toBeEnabled();
    await aprovar.click();

    // Confirmação obrigatória: nada é enviado antes dela.
    await expect(page.getByText("Confirmar aprovação", { exact: true }).first()).toBeVisible();
    expect(corpoAprovar).toBeNull();
    await page.getByRole("button", { name: "Confirmar aprovação" }).click();

    await expect(page.getByText(/^Aprovada em /)).toBeVisible();
    expect(corpoAprovar).toEqual({ legenda: revisada, aprovar_legenda_ia: true });
    await expect(page.getByLabel("Legenda da foto")).toHaveValue(revisada);
  });

  test("perfil cliente não vê o painel de legenda por IA", async ({ page }) => {
    await prepararPagina(page, "cliente");
    await page.goto(`/inspecoes/${INSPECAO_ID}/visitas`);
    await expect(page.getByAltText("Foto vinculada à visita")).toBeVisible();
    await page.waitForLoadState("networkidle"); // garante que `/auth/me` já respondeu
    await expect(page.getByRole("button", { name: "Legenda com IA" })).toHaveCount(0);
  });
});
