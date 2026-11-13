import { expect, test, type Page, type Route } from "@playwright/test";

import { API_BASE_URL } from "./helpers";

/**
 * Anotação de foto integrada à legenda por IA (BL-39; RF-15, RN-16, RN-17; DEC-42).
 *
 * - O editor mostra o estado da legenda e permite ajustar o texto, mas não tem ação de aprovar.
 * - Alterar a legenda de foto aprovada: o aviso «voltou a pendente» segue a RESPOSTA do backend.
 *
 * API **mockada** via `page.route` (padrão de `legenda-ia-aprovacao.spec.ts`).
 */

const INSPECAO_ID = "00000000-0000-4000-8000-000000000021";
const VISITA_ID = "00000000-0000-4000-8000-000000000022";
const FOTO_ID = "00000000-0000-4000-8000-000000000023";
const USUARIO_ID = "00000000-0000-4000-8000-000000000024";
const PNG_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

const SUGESTAO = "Fissura diagonal no revestimento da fachada norte.";
const REVISADA = "Fissura diagonal no revestimento da fachada norte (2º pavimento).";

type Role = "auditor" | "auxiliar";
type Estado = Record<string, unknown>;

const fotoRascunho: Estado = {
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
  legenda_ia_sugerida: SUGESTAO,
  nivel_certeza_ia: null,
  status_validacao_ia: "rascunho",
  alertas_ia: null,
  pendencias_ia: null,
  legenda_ia_gerada_em: "2026-11-05T12:05:00Z",
  aprovado_por_id: null,
  aprovado_em: null,
};

const fotoAprovada: Estado = {
  ...fotoRascunho,
  legenda: SUGESTAO,
  status_validacao_ia: "aprovada",
  aprovado_por_id: USUARIO_ID,
  aprovado_em: "2026-11-05T12:10:00Z",
};

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

async function prepararPagina(page: Page, role: Role, foto: Estado) {
  await page.addInitScript(() => window.localStorage.setItem("garra:access_token", "token-e2e"));
  await page.route(`${API_BASE_URL}/**`, (route) =>
    responder(route, 404, { title: "Não mockado", status: 404 }, "application/problem+json")
  );
  await page.route(`${API_BASE_URL}/auth/me`, (route) =>
    responder(route, 200, { id: USUARIO_ID, nome: "Equipe E2E", email: "e2e@exemplo.com", ativo: true, role })
  );
  await page.route(`${API_BASE_URL}/inspecoes/${INSPECAO_ID}`, (route) =>
    responder(route, 200, {
      id: INSPECAO_ID,
      contrato_id: "00000000-0000-4000-8000-000000000025",
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
          fotos: [foto],
        },
      ],
    })
  );
}

async function abrirEditor(page: Page) {
  await page.goto(`/inspecoes/visitas/?id=${INSPECAO_ID}`);
  await page.getByRole("button", { name: "Anotar foto" }).click();
  const dialog = page.getByRole("dialog").filter({ hasText: "Editar e marcar foto" });
  await expect(dialog.locator("canvas").first()).toBeVisible({ timeout: 15_000 });
  return dialog;
}

test.describe("Anotação de foto + legenda IA (BL-39)", () => {
  test("editor mostra o estado da legenda e não oferece ação de aprovar (auxiliar)", async ({ page }) => {
    await prepararPagina(page, "auxiliar", fotoRascunho);
    const dialog = await abrirEditor(page);

    await expect(dialog.getByText("Legenda IA pendente de aprovação")).toBeVisible();
    await expect(dialog.getByText(/aprovação da legenda é feita pelo auditor/)).toBeVisible();
    await expect(dialog.getByRole("button", { name: /Aprovar/ })).toHaveCount(0);
  });

  test("editor não oferece «Aprovar» nem para o auditor (aprovação só no painel)", async ({ page }) => {
    await prepararPagina(page, "auditor", fotoAprovada);
    const dialog = await abrirEditor(page);

    await expect(dialog.getByText("Legenda IA aprovada")).toBeVisible();
    await expect(dialog.getByRole("button", { name: /Aprovar/ })).toHaveCount(0);
    await expect(dialog.getByText(/use o painel «Legenda com IA»/)).toBeVisible();
  });

  test("alterar a legenda aprovada avisa no editor e, pela resposta do backend, volta a pendente", async ({
    page,
  }) => {
    await prepararPagina(page, "auditor", fotoAprovada);
    let corpoPut: Record<string, unknown> | null = null;
    await page.route(`${API_BASE_URL}/fotos/${FOTO_ID}`, (route) => {
      if (route.request().method() === "PUT") corpoPut = route.request().postDataJSON();
      return responder(route, 200, {
        ...fotoAprovada,
        legenda: REVISADA,
        status_validacao_ia: "rascunho",
        aprovado_por_id: null,
        aprovado_em: null,
      });
    });
    await page.route(`${API_BASE_URL}/fotos/upload`, (route) =>
      responder(route, 200, { storage_key: "fotos/anotada.png", url: PNG_DATA_URL })
    );
    await page.route(`${API_BASE_URL}/visitas/${VISITA_ID}/fotos`, (route) =>
      responder(route, 201, {
        ...fotoRascunho,
        id: "00000000-0000-4000-8000-000000000026",
        storage_key: "fotos/anotada.png",
        legenda: REVISADA,
        legenda_ia_sugerida: null,
        status_validacao_ia: null,
        ordem: 1,
      })
    );

    const dialog = await abrirEditor(page);
    await dialog.getByRole("textbox", { name: "Legenda da foto" }).fill(REVISADA);
    await expect(dialog.getByText(/desfaz a aprovação/)).toBeVisible();
    await dialog.getByRole("button", { name: "Salvar marcação" }).click();

    await expect(dialog).toBeHidden();
    await expect(page.getByText(/voltou a pendente/)).toBeVisible();
    await expect(page.getByText("Legenda IA: pendente de aprovação")).toBeVisible();
    expect(corpoPut).toEqual({ legenda: REVISADA });
  });
});
