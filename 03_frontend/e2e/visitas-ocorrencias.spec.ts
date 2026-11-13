import { test, expect } from "@playwright/test";

import { API_BASE_URL } from "./helpers";
import { apagarRecursos, prepararInspecao } from "./inspecao-helpers";

/**
 * Visitas (RF-03, BL-10) e Ocorrências (RF-04, BL-14) — revalida no navegador as regras que mudaram
 * nas tarefas T21 (visitas: data futura e 2ª visita no mesmo dia rejeitadas, RN-01/RN-02, DEC-38) e
 * T08 (ocorrências: enums de Situação/Classificação, RN-05, DEC-34).
 *
 * Nomes únicos por execução. A API não expõe DELETE para edificação, contrato, inspeção nem visita:
 * esses registros ficam no banco de dev (marcador "E2E"); as ocorrências criadas são removidas.
 */
test.describe("Visitas (RFO)", () => {
  test("cria visita; rejeita data futura e segunda visita no mesmo dia; edita", async ({ page, request }) => {
    const { inspecaoId } = await prepararInspecao(page, request, "RFO");
    await expect(page).toHaveURL(new RegExp(`/inspecoes/visitas/\\?id=${inspecaoId}$`));

    const servicos = `Concretagem E2E ${Date.now()}`;
    const abrirNovaVisita = async () => {
      await page.getByRole("button", { name: "Nova visita" }).click();
      return page.getByRole("dialog");
    };

    // 1. Cria a visita pela UI (data passada fixa: a inspeção é nova, então não colide).
    let dialog = await abrirNovaVisita();
    await dialog.getByLabel("Data da visita").fill("2026-03-10");
    await dialog.getByLabel("Serviços executados").fill(servicos);
    await dialog.getByRole("button", { name: "Registrar visita" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.getByText(/Visita #1/)).toBeVisible();
    await expect(page.getByText(servicos)).toBeVisible();

    // 2. Data futura: o servidor recusa (DEC-38 B) e a mensagem aparece no diálogo.
    dialog = await abrirNovaVisita();
    await dialog.getByLabel("Data da visita").fill("2099-01-01");
    await dialog.getByLabel("Serviços executados").fill("Visita futura");
    await dialog.getByRole("button", { name: "Registrar visita" }).click();
    await expect(dialog.getByRole("alert")).toContainText(/não pode ser futura/i);
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Cancelar" }).click();
    await expect(dialog).toBeHidden();

    // 3. Segunda visita no mesmo dia (RN-01): 409 com a mensagem do servidor.
    dialog = await abrirNovaVisita();
    await dialog.getByLabel("Data da visita").fill("2026-03-10");
    await dialog.getByLabel("Serviços executados").fill("Outra visita no mesmo dia");
    await dialog.getByRole("button", { name: "Registrar visita" }).click();
    await expect(dialog.getByRole("alert")).toContainText(/Já existe uma visita nesta inspeção na data 2026-03-10/);
    await dialog.getByRole("button", { name: "Cancelar" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.getByText(/Visita #\d+/)).toHaveCount(1);

    // 4. Edita a visita e confirma na tela.
    await page.getByRole("button", { name: "Editar visita" }).click();
    const edicao = page.getByRole("dialog");
    const novoTexto = `${servicos} (editado)`;
    await edicao.getByLabel("Serviços executados").fill(novoTexto);
    await edicao.getByLabel("Observações").fill("Observação E2E");
    await edicao.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(edicao).toBeHidden();
    await expect(page.getByText(novoTexto)).toBeVisible();
    await expect(page.getByText("Obs.: Observação E2E")).toBeVisible();

    // 5. A edição persiste (recarrega do servidor).
    await page.reload();
    await expect(page.getByText(novoTexto)).toBeVisible();
  });
});

interface OcorrenciaApi {
  id: string;
  situacao: string;
  classificacao: string;
  grau_risco: string;
}

test.describe("Ocorrências (LTIP)", () => {
  test("cria ocorrência com sistema, subsistema, localização e classificação; edita e confirma", async ({
    page,
    request,
  }) => {
    const { auth, inspecaoId } = await prepararInspecao(page, request, "LTIP");
    const localizacao = `Fachada norte E2E ${Date.now()}`;

    await page.getByRole("button", { name: "Nova ocorrência" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Sistema predial").selectOption({ index: 1 });
    // O subsistema depende do sistema escolhido; escolhe a primeira opção real, se houver.
    const subsistema = dialog.getByLabel("Subsistema");
    if ((await subsistema.locator("option").count()) > 1) {
      await subsistema.selectOption({ index: 1 });
    }
    await dialog.getByLabel("Localização").fill(localizacao);
    await dialog.getByLabel("Situação").selectOption({ label: "Não Conforme" });
    await dialog.getByLabel("Classificação").selectOption({ label: "Anomalia" });
    await dialog.getByLabel("Tipo de Anomalia").selectOption({ index: 1 });
    await dialog.getByLabel("Grau de Risco (CMM)").selectOption({ label: "Médio" });
    await dialog.getByLabel("Descrição").fill("Fissura E2E.");

    const criada = page.waitForResponse(
      (r) => /\/ocorrencias$/.test(new URL(r.url()).pathname) && r.request().method() === "POST"
    );
    await dialog.getByRole("button", { name: "Criar ocorrência" }).click();
    const resposta = await criada;
    expect(resposta.status()).toBe(201);
    const ocorrenciaId = ((await resposta.json()) as { id: string }).id;

    try {
      // O diálogo segue aberto em modo edição: troca a classificação para Falha e confirma.
      await dialog.getByLabel("Classificação").selectOption({ label: "Falha" });
      await dialog.getByLabel("Tipo de Falha").selectOption({ index: 1 });
      await dialog.getByLabel("Grau de Risco (CMM)").selectOption({ label: "Crítico" });
      const atualizada = page.waitForResponse(
        (r) => r.url().includes(`/ocorrencias/${ocorrenciaId}`) && r.request().method() === "PUT"
      );
      await dialog.getByRole("button", { name: "Salvar alterações" }).click();
      expect((await atualizada).status()).toBe(200);
      await dialog.getByRole("button", { name: "Concluir" }).click();
      await expect(dialog).toBeHidden();

      // A lista mostra a ocorrência com os valores editados (enums em rótulo legível).
      const linha = page.getByRole("row").filter({ hasText: localizacao });
      await expect(linha).toHaveCount(1);
      await expect(linha).toContainText("Não Conforme");
      await expect(linha).toContainText("Falha");
      await expect(linha).toContainText("Crítico");

      // Persistência: o servidor devolve os mesmos valores (enums canônicos).
      const lida = await request.get(`${API_BASE_URL}/inspecoes/${inspecaoId}/ocorrencias`, {
        headers: { Authorization: `Bearer ${auth.token}` },
      });
      expect(lida.ok()).toBeTruthy();
      const corpo = (await lida.json()) as OcorrenciaApi[] | { items: OcorrenciaApi[] };
      const itens = Array.isArray(corpo) ? corpo : corpo.items;
      expect(itens.find((o) => o.id === ocorrenciaId)).toMatchObject({
        situacao: "NAO_CONFORME",
        classificacao: "FALHA",
        grau_risco: "CRITICO",
      });
    } finally {
      await apagarRecursos(request, auth.token, [`/ocorrencias/${ocorrenciaId}`]);
    }
  });
});
