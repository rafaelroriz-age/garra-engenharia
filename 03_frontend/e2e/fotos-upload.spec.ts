import { test, expect, type Response } from "@playwright/test";

import { pngBuffer } from "./helpers";
import { apagarRecursos, prepararInspecao } from "./inspecao-helpers";

/**
 * Upload de fotos de Visita (RF-05, BL-11) no navegador, contra o backend real e o storage S3/MinIO
 * configurado nele. Revalida a regra da T19: o servidor só aceita `storage_key` que ele mesmo gerou
 * no upload (o front vincula a chave devolvida por `POST /fotos/upload[-clipboard]`).
 *
 * A imagem é o PNG 1x1 de `helpers.ts`, gerado no teste (nada de `01_output-context/`).
 * Fotos criadas são removidas ao final; edificação/contrato/visita não têm DELETE na API.
 */
test("upload manual e colagem da área de transferência aparecem na lista de fotos da visita", async ({
  page,
  request,
}) => {
  const { auth } = await prepararInspecao(page, request, "RFO");

  // `navigator.clipboard.read()` simulado (o Chromium headless não concede leitura real). O init script
  // vale a partir da próxima navegação; o `reload` abaixo o aplica à página atual.
  await page.addInitScript((base64: string) => {
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
    const blob = new Blob([bytes], { type: "image/png" });
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { read: async () => [{ types: ["image/png"], getType: async () => blob }] },
    });
  }, pngBuffer().toString("base64"));
  await page.reload();

  // Visita para vincular as fotos.
  await page.getByRole("button", { name: "Nova visita" }).click();
  const dialogVisita = page.getByRole("dialog");
  await dialogVisita.getByLabel("Data da visita").fill("2026-03-11");
  await dialogVisita.getByLabel("Serviços executados").fill("Visita de fotos E2E");
  await dialogVisita.getByRole("button", { name: "Registrar visita" }).click();
  await expect(dialogVisita).toBeHidden();
  await expect(page.getByText(/Visita #1/)).toBeVisible();

  const secaoFotos = () =>
    page.locator("section", { has: page.getByRole("heading", { name: "Fotos da visita" }) });
  const fotoIds: string[] = [];
  const dialogEditor = page.getByRole("dialog").filter({ hasText: "Editar e marcar foto" });

  const salvarNoEditor = async () => {
    await expect(dialogEditor.locator("canvas").first()).toBeVisible({ timeout: 15_000 });
    const vinculo = page.waitForResponse(
      (r: Response) =>
        /\/visitas\/[0-9a-f-]+\/fotos$/.test(new URL(r.url()).pathname) && r.request().method() === "POST"
    );
    await dialogEditor.getByRole("button", { name: "Salvar marcação" }).click();
    const resposta = await vinculo;
    expect(resposta.status(), `corpo: ${await resposta.text()} | requisição: ${resposta.request().postData()}`).toBe(201);
    fotoIds.push(((await resposta.json()) as { id: string }).id);
    await expect(dialogEditor).toBeHidden();
  };

  try {
    // 1. Upload manual.
    await secaoFotos().getByRole("button", { name: "Enviar arquivo" }).click();
    await secaoFotos().locator('input[type="file"]').setInputFiles({
      name: "upload-manual-e2e.png",
      mimeType: "image/png",
      buffer: pngBuffer(),
    });
    await salvarNoEditor();
    await expect(secaoFotos().getByRole("img")).toHaveCount(1);

    // 2. Colagem (clipboard), vinculada à mesma visita.
    await secaoFotos().getByRole("button", { name: "Colar da área de transferência" }).click();
    await salvarNoEditor();
    await expect(secaoFotos().getByRole("img")).toHaveCount(2);

    // 3. Persistência: após recarregar, as duas fotos continuam listadas.
    await page.reload();
    await expect(page.getByText(/Visita #1/)).toBeVisible();
    await expect(secaoFotos().getByRole("img")).toHaveCount(2);
  } finally {
    await apagarRecursos(
      request,
      auth.token,
      fotoIds.map((id) => `/fotos/${id}`)
    );
  }
});
