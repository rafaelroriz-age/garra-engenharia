import { test, expect } from "@playwright/test";

import { pngBuffer } from "./helpers";

/**
 * Regressão BL-31 — valor de `origem` enviado ao vincular foto.
 *
 * O backend (`04_backend/app/schemas/foto.py`, `FotoVincularPayload.origem`) não restringe
 * o valor, mas o contrato de origem do frontend é `OrigemFoto` (`lib/types.ts`):
 * upload manual deve vincular com `upload_manual`, nunca com o rótulo interno `upload`.
 *
 * Diferente dos fluxos RFO/LTIP, este spec NÃO usa o backend real: toda a API é mockada
 * com `page.route`, então roda sem `docker compose up`.
 */

const API_PATTERN = "**/api/v1/**";
const INSPECAO_ID = "11111111-1111-4111-8111-111111111111";
const VISITA_ID = "22222222-2222-4222-8222-222222222222";
const STORAGE_KEY = "fotos/foto-origem-e2e.png";
const UPLOAD_URL = "https://storage.test/fotos/foto-origem-e2e.png";

test.describe("Origem da foto no vínculo (BL-31)", () => {
  test("upload manual vincula a foto com origem 'upload_manual'", async ({ page }) => {
    const origensRecebidas: unknown[] = [];

    // Sessão já autenticada (token lido de `localStorage` pelo api-client).
    await page.addInitScript(() => {
      window.localStorage.setItem("garra:access_token", "token-e2e-mock");
    });

    await page.route(API_PATTERN, async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      const path = url.pathname;
      const method = request.method();

      // A página de visitas lê `inspecao.visitas` de `GET /inspecoes/{id}`.
      if (method === "GET" && path.endsWith(`/inspecoes/${INSPECAO_ID}`)) {
        return route.fulfill({
          json: {
            id: INSPECAO_ID,
            visitas: [
              {
                id: VISITA_ID,
                inspecao_id: INSPECAO_ID,
                seq_numero: 1,
                data: "2026-01-10",
                fotos: [],
                maos_obra: [],
                medicoes: [],
                servicos: [],
              },
            ],
          },
        });
      }

      // Upload bruto (multipart) — devolve a chave e a URL pré-assinada (`FotoUploadResponse`).
      if (method === "POST" && path.endsWith("/fotos/upload")) {
        return route.fulfill({ status: 201, json: { storage_key: STORAGE_KEY, url: UPLOAD_URL } });
      }

      // Vínculo — é aqui que a origem é verificada.
      if (method === "POST" && path.endsWith(`/visitas/${VISITA_ID}/fotos`)) {
        const body = request.postDataJSON() as { origem?: unknown };
        origensRecebidas.push(body.origem);
        return route.fulfill({
          status: 201,
          json: {
            id: "33333333-3333-4333-8333-333333333333",
            visita_id: VISITA_ID,
            storage_key: STORAGE_KEY,
            url_publica: UPLOAD_URL,
            legenda: "",
            origem: body.origem,
            ordem: 0,
            created_at: new Date().toISOString(),
          },
        });
      }

      // Demais rotas (ex.: `/auth/me`) não são exercitadas aqui.
      return route.fulfill({ status: 200, json: {} });
    });

    await page.goto(`/inspecoes/${INSPECAO_ID}/visitas`);

    // Uma única visita no mock: o botão "Enviar arquivo" e o input de arquivo são únicos na página.
    await page.getByRole("button", { name: "Enviar arquivo" }).click();
    await page.locator('input[type="file"]').setInputFiles({
      name: "foto-origem-e2e.png",
      mimeType: "image/png",
      buffer: pngBuffer(),
    });

    const dialog = page.getByRole("dialog").filter({ hasText: "Editar e marcar foto" });
    await expect(dialog.locator("canvas").first()).toBeVisible({ timeout: 15_000 });

    const vinculo = page.waitForResponse(
      (response) =>
        response.url().includes(`/visitas/${VISITA_ID}/fotos`) && response.request().method() === "POST"
    );
    await dialog.getByRole("button", { name: "Salvar marcação" }).click();
    await vinculo;

    expect(origensRecebidas).toEqual(["upload_manual"]);
    expect(origensRecebidas).not.toContain("upload");
  });
});
