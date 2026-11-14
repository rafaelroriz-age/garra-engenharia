import { expect, test, type Page, type Route } from "@playwright/test";

import { API_BASE_URL } from "./helpers";

/**
 * Aprovação de legenda por IA restrita ao auditor (DEC-42 itens A e B; SEG-IA-03/04/05).
 *
 * - Só `auditor` vê e usa «Aprovar legenda»; `auxiliar` gera e edita o rascunho.
 * - Editar ou regerar uma legenda aprovada mostra aviso e, após salvar/gerar, o status
 *   passa a `rascunho` conforme a **resposta do backend** (nada é presumido localmente).
 *
 * API **mockada** via `page.route` (mesmo padrão de `legenda-ia.spec.ts`): não precisa de
 * backend, banco nem provedor de LLM; só do frontend em execução (`E2E_BASE_URL`).
 */

const INSPECAO_ID = "00000000-0000-4000-8000-000000000011";
const VISITA_ID = "00000000-0000-4000-8000-000000000012";
const FOTO_ID = "00000000-0000-4000-8000-000000000013";
const USUARIO_ID = "00000000-0000-4000-8000-000000000014";
const PNG_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

const SUGESTAO = "Fissura diagonal no revestimento da fachada norte, próxima à janela do 2º pavimento.";
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
      contrato_id: "00000000-0000-4000-8000-000000000015",
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

async function abrirPainel(page: Page) {
  await page.goto(`/inspecoes/visitas/?id=${INSPECAO_ID}`);
  await page.getByRole("button", { name: "Legenda com IA" }).click();
  await expect(page.getByLabel("Legenda sugerida (editável)")).toBeVisible();
}

test.describe("Aprovação de legenda IA restrita ao auditor (DEC-42)", () => {
  test("auxiliar não vê «Aprovar» e recebe a orientação; pode editar o rascunho", async ({ page }) => {
    await prepararPagina(page, "auxiliar", fotoRascunho);
    await abrirPainel(page);

    await expect(page.getByRole("button", { name: "Aprovar legenda" })).toHaveCount(0);
    await expect(page.getByText("A aprovação é feita pelo auditor responsável.")).toBeVisible();
    // Continua podendo editar o rascunho e gerar nova sugestão.
    await expect(page.getByLabel("Legenda sugerida (editável)")).toBeEnabled();
    await expect(page.getByRole("button", { name: "Gerar nova sugestão com IA" })).toBeEnabled();
  });

  test("auditor vê «Aprovar» e aprova após confirmação", async ({ page }) => {
    await prepararPagina(page, "auditor", fotoRascunho);
    let corpoAprovar: Record<string, unknown> | null = null;
    await page.route(`${API_BASE_URL}/fotos/${FOTO_ID}`, (route) => {
      if (route.request().method() === "PUT") corpoAprovar = route.request().postDataJSON();
      return responder(route, 200, {
        ...fotoRascunho,
        legenda: (corpoAprovar?.legenda as string | undefined) ?? SUGESTAO,
        status_validacao_ia: "aprovada",
        aprovado_por_id: USUARIO_ID,
        aprovado_em: "2026-11-05T12:10:00Z",
      });
    });

    await abrirPainel(page);
    await expect(page.getByText("A aprovação é feita pelo auditor responsável.")).toHaveCount(0);

    await page.getByLabel("Legenda sugerida (editável)").fill(REVISADA);
    await page.getByRole("button", { name: "Aprovar legenda" }).click();
    expect(corpoAprovar).toBeNull(); // confirmação obrigatória
    await page.getByRole("button", { name: "Confirmar aprovação" }).click();

    await expect(page.getByText(/^Aprovada em /)).toBeVisible();
    expect(corpoAprovar).toEqual({ legenda: REVISADA, aprovar_legenda_ia: true });
  });

  test("editar legenda aprovada mostra aviso e, ao salvar, o status volta a rascunho", async ({ page }) => {
    await prepararPagina(page, "auditor", fotoAprovada);
    let corpoPut: Record<string, unknown> | null = null;
    await page.route(`${API_BASE_URL}/fotos/${FOTO_ID}`, (route) => {
      if (route.request().method() === "PUT") corpoPut = route.request().postDataJSON();
      // Resposta do backend: edição sem aprovar_legenda_ia zera a aprovação (DEC-42 B).
      return responder(route, 200, {
        ...fotoAprovada,
        legenda: REVISADA,
        status_validacao_ia: "rascunho",
        aprovado_por_id: null,
        aprovado_em: null,
      });
    });

    await abrirPainel(page);
    await expect(page.getByText("Esta legenda já está aprovada")).toBeVisible();
    await expect(page.getByText(/^Aprovada em /)).toBeVisible();

    await page.getByLabel("Legenda sugerida (editável)").fill(REVISADA);
    await page.getByRole("button", { name: "Salvar edição (desfaz a aprovação)" }).click();

    await expect(page.getByText("Rascunho — aguardando aprovação")).toBeVisible();
    await expect(page.getByText(/^Aprovada em /)).toHaveCount(0);
    await expect(page.getByText("A aprovação foi desfeita")).toBeVisible();
    expect(corpoPut).toEqual({ legenda: REVISADA });
    await expect(page.getByRole("button", { name: "Aprovar legenda" })).toBeVisible();
  });

  test("gerar nova sugestão em legenda aprovada avisa e volta a rascunho pela resposta do backend", async ({
    page,
  }) => {
    await prepararPagina(page, "auxiliar", fotoAprovada);
    await page.route(`${API_BASE_URL}/fotos/${FOTO_ID}/legenda-ia/gerar`, (route) =>
      responder(route, 200, {
        ...fotoAprovada,
        legenda_ia_sugerida: REVISADA,
        status_validacao_ia: "rascunho",
        aprovado_por_id: null,
        aprovado_em: null,
        legenda_ia_gerada_em: "2026-11-05T12:20:00Z",
      })
    );

    await abrirPainel(page);
    await expect(page.getByText("Esta legenda já está aprovada")).toBeVisible();
    await page.getByRole("button", { name: "Gerar nova sugestão com IA" }).click();

    await expect(page.getByLabel("Legenda sugerida (editável)")).toHaveValue(REVISADA);
    await expect(page.getByText("Rascunho — aguardando aprovação")).toBeVisible();
    await expect(page.getByText(/^Aprovada em /)).toHaveCount(0);
    await expect(page.getByText("A aprovação anterior foi desfeita")).toBeVisible();
  });
});
