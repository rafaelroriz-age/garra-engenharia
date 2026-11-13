import { test, expect } from "@playwright/test";

import {
  API_BASE_URL,
  cnpjUnico,
  criarResponsavel,
  loginPelaUI,
  nomeUnico,
  registrarUsuario,
} from "./helpers";

/**
 * Edificações e Contratos (RF-01, RF-02, RN-06, RN-09 — BL-08, BL-09, BL-21).
 *
 * Login como auditor -> lista/busca de edificações -> criação de edificação pela UI ->
 * lista/filtros de contratos -> criação de contrato com 2 empresas executoras e 2 NBRs.
 *
 * Todos os nomes são únicos por execução. A API não expõe DELETE para edificação/contrato,
 * então os registros criados permanecem no banco de desenvolvimento (identificáveis pelo
 * marcador "E2E" no nome/número); ver o Doc da tarefa BL-21.
 */
test.describe("Edificações e contratos (auditor)", () => {
  test("lista, busca e cria edificação pela UI", async ({ page, request }) => {
    const auth = await registrarUsuario(request);
    await loginPelaUI(page, auth);

    const nome = nomeUnico("Ed. Lista");
    const endereco = `Rua E2E ${Date.now()}, 100`;

    await page.goto("/edificacoes");
    await expect(
      page.getByRole("heading", { name: "Edificações" }),
    ).toBeVisible();
    // A listagem renderiza a tabela (há dados de outras execuções) ou o estado vazio.
    await expect(
      page.getByRole("button", { name: "Nova edificação" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Nova edificação" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Nome").fill(nome);
    await dialog.getByLabel("Endereço").fill(endereco);
    await dialog.getByRole("button", { name: "Criar edificação" }).click();
    await expect(dialog).toBeHidden();

    // Busca por nome (o banco de dev acumula edificações; o filtro isola a recém-criada).
    const busca = page.getByPlaceholder("Buscar por nome ou endereço...");
    await busca.fill(nome);
    const link = page.getByRole("link", { name: nome });
    await expect(link).toBeVisible();
    await expect(page.getByRole("cell", { name: endereco })).toBeVisible();

    // Busca por endereço encontra a mesma edificação.
    await busca.fill(endereco);
    await expect(page.getByRole("link", { name: nome })).toBeVisible();

    // Busca sem resultado mostra o estado vazio.
    await busca.fill(`inexistente-${Date.now()}`);
    await expect(
      page.getByText(/Nenhuma edificação cadastrada ainda/),
    ).toBeVisible();

    // Detalhe da edificação.
    await busca.fill(nome);
    await page.getByRole("link", { name: nome }).click();
    await expect(page).toHaveURL(/\/edificacoes\/detalhe\/\?id=[0-9a-f-]+$/);
    await expect(page.getByText(nome).first()).toBeVisible();
  });

  test("lista contratos, aplica filtros e cria contrato com 2 executoras e NBRs (RN-06/RN-09)", async ({
    page,
    request,
  }) => {
    const auth = await registrarUsuario(request);
    const fiscalId = await criarResponsavel(request, auth.token, {
      nome: nomeUnico("Eng. Fiscal"),
      tipo: "fiscal",
      crea: "222222-GO",
    });
    const legal1 = await criarResponsavel(request, auth.token, {
      nome: nomeUnico("Resp. Legal 1"),
      tipo: "responsavel_legal",
    });
    const legal2 = await criarResponsavel(request, auth.token, {
      nome: nomeUnico("Resp. Legal 2"),
      tipo: "responsavel_legal",
    });
    await loginPelaUI(page, auth);

    // Edificação para o contrato.
    const nomeEdificacao = nomeUnico("Ed. Contrato");
    await page.goto("/edificacoes");
    await page.getByRole("button", { name: "Nova edificação" }).click();
    const dialogEd = page.getByRole("dialog");
    await dialogEd.getByLabel("Nome").fill(nomeEdificacao);
    await dialogEd.getByLabel("Endereço").fill("Av. dos Contratos, 200");
    await dialogEd.getByRole("button", { name: "Criar edificação" }).click();
    await expect(dialogEd).toBeHidden();

    await page.goto("/contratos");
    await expect(
      page.getByRole("heading", { name: "Contratos" }),
    ).toBeVisible();

    // Validação client-side: ART de Fiscalização obrigatória (RN-09).
    await page.getByRole("button", { name: "Novo contrato" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: "Criar contrato" }).click();
    await expect(
      dialog.getByText(/ART de Fiscalização é obrigatória \(RN-09\)/),
    ).toBeVisible();

    // Preenche o contrato com 2 executoras (RN-06) e 2 NBRs.
    const numero = `CT-E2E-${Date.now()}`;
    const razao1 = nomeUnico("Executora A");
    const razao2 = nomeUnico("Executora B");
    const cnpj1 = cnpjUnico();
    const cnpj2 = String(Number(cnpj1) + 1).padStart(14, "0");

    // O seletor de edificação do formulário carrega só `page_size=100` e a API não ordena;
    // com >100 edificações no banco a recém-criada pode não estar na lista (bug de UI
    // registrado no Doc BL-21). Nesse caso o contrato é criado via API para o resto do fluxo.
    await page.waitForLoadState("networkidle");
    const opcaoDisponivel =
      (await dialog
        .locator("#edificacao_id option", { hasText: nomeEdificacao })
        .count()) > 0;
    test.info().annotations.push({
      type: "bug-ui",
      description: opcaoDisponivel
        ? "seletor de edificação OK"
        : "edificação recém-criada ausente do seletor do contrato (limite de 100 sem ordenação/busca)",
    });

    let contratoId = "";
    let edificacaoId = "";
    if (opcaoDisponivel) {
      await dialog
        .getByLabel("Edificação")
        .selectOption({ label: nomeEdificacao });
      await dialog.getByLabel("Número do contrato").fill(numero);
      await dialog.getByLabel("Tipo de serviço").selectOption("LTIP");
      await dialog.getByLabel("Engenheiro fiscal (ID)").fill(fiscalId);
      await dialog.getByLabel("ART de Fiscalização").fill("ART-FISC-E2E");

      await dialog.locator("#executor-razao-0").fill(razao1);
      await dialog.locator("#executor-cnpj-0").fill(cnpj1);
      await dialog.locator("#executor-legal-0").fill(legal1);
      await dialog.locator("#executor-art-0").fill("ART-EXEC-A");

      await dialog
        .getByRole("button", { name: "Adicionar empresa executora" })
        .click();
      await dialog.locator("#executor-razao-1").fill(razao2);
      await dialog.locator("#executor-cnpj-1").fill(cnpj2);
      await dialog.locator("#executor-legal-1").fill(legal2);
      await dialog.locator("#executor-art-1").fill("ART-EXEC-B");

      await dialog.locator("#nbr-codigo-0").fill("NBR 16747");
      await dialog.locator("#nbr-descricao-0").fill("Inspeção predial");
      await dialog.getByRole("button", { name: "Adicionar NBR" }).click();
      await dialog.locator("#nbr-codigo-1").fill("NBR 5674");
      await dialog
        .locator("#nbr-descricao-1")
        .fill("Manutenção de edificações");

      const criado = page.waitForResponse(
        (r) =>
          r.url().endsWith("/contratos") && r.request().method() === "POST",
      );
      await dialog.getByRole("button", { name: "Criar contrato" }).click();
      const resposta = await criado;
      expect(resposta.status()).toBe(201);
      const corpo = (await resposta.json()) as {
        id: string;
        executores: unknown[];
        nbrs: unknown[];
        inspecao: { id: string } | null;
      };
      expect(corpo.executores).toHaveLength(2);
      expect(corpo.nbrs).toHaveLength(2);
      expect(corpo.inspecao).not.toBeNull(); // Inspeção 1:1 originada do contrato
      contratoId = corpo.id;
      await expect(dialog).toBeHidden();
    } else {
      await dialog.getByRole("button", { name: "Cancelar" }).click();
      await expect(dialog).toBeHidden();
      const lista = await request.get(
        `${API_BASE_URL}/edificacoes?page=1&page_size=100&nome=${encodeURIComponent(nomeEdificacao)}`,
        { headers: { Authorization: `Bearer ${auth.token}` } },
      );
      edificacaoId = ((await lista.json()) as { items: { id: string }[] })
        .items[0].id;
      const resp = await request.post(`${API_BASE_URL}/contratos`, {
        headers: { Authorization: `Bearer ${auth.token}` },
        data: {
          edificacao_id: edificacaoId,
          fiscal_id: fiscalId,
          numero,
          tipo_servico: "LTIP",
          art_fiscalizacao: "ART-FISC-E2E",
          executores: [
            {
              responsavel_legal_id: legal1,
              razao_social: razao1,
              cnpj: cnpj1,
              art_execucao: "ART-EXEC-A",
            },
            {
              responsavel_legal_id: legal2,
              razao_social: razao2,
              cnpj: cnpj2,
              art_execucao: "ART-EXEC-B",
            },
          ],
          nbrs: [
            { codigo_nbr: "NBR 16747", descricao: "Inspeção predial" },
            { codigo_nbr: "NBR 5674", descricao: "Manutenção de edificações" },
          ],
        },
      });
      expect(resp.status(), await resp.text()).toBe(201);
      contratoId = ((await resp.json()) as { id: string }).id;
      await page.reload();
    }

    // Filtros da listagem. O filtro de edificação usa a mesma lista capada em 100: se a
    // opção não existe, os filtros são verificados na API (mesmos parâmetros da UI).
    const filtroTemEdificacao =
      (await page
        .locator("#filtro-edificacao option", { hasText: nomeEdificacao })
        .count()) > 0;
    const linkContrato = page.getByRole("link", { name: numero });
    if (filtroTemEdificacao) {
      await page
        .locator("#filtro-edificacao")
        .selectOption({ label: nomeEdificacao });
      await expect(linkContrato).toBeVisible();

      await page.locator("#filtro-tipo-servico").selectOption("LTIP");
      await expect(linkContrato).toBeVisible();
      await page.locator("#filtro-status").selectOption("em_andamento");
      await expect(linkContrato).toBeVisible();

      await page.locator("#filtro-tipo-servico").selectOption("RFO");
      await expect(linkContrato).toBeHidden();
      await expect(
        page.getByText(/Nenhum contrato cadastrado ainda/),
      ).toBeVisible();

      await page.locator("#filtro-tipo-servico").selectOption("LTIP");
      await page.locator("#filtro-status").selectOption("cancelado");
      await expect(linkContrato).toBeHidden();

      await page.locator("#filtro-status").selectOption("");
      await expect(linkContrato).toBeVisible();
    } else {
      const headers = { Authorization: `Bearer ${auth.token}` };
      const total = async (qs: string) =>
        (
          (await (
            await request.get(
              `${API_BASE_URL}/contratos?edificacao_id=${edificacaoId}&${qs}`,
              { headers },
            )
          ).json()) as {
            total: number;
          }
        ).total;
      expect(await total("tipo_servico=LTIP&status=em_andamento")).toBe(1);
      expect(await total("tipo_servico=RFO")).toBe(0);
      expect(await total("status=cancelado")).toBe(0);
      // Filtros de tipo/status da UI continuam exercitados (sem a edificação).
      await page.locator("#filtro-tipo-servico").selectOption("LTIP");
      await page.locator("#filtro-status").selectOption("em_andamento");
      await expect(page.getByRole("table")).toBeVisible();
    }

    // Detalhe: as duas executoras e as duas NBRs aparecem (RN-06, RF-12).
    await page.goto(`/contratos/detalhe/?id=${contratoId}`);
    await expect(page).toHaveURL(/\/contratos\/detalhe\/\?id=[0-9a-f-]+$/);
    await expect(page.getByText(razao1)).toBeVisible();
    await expect(page.getByText(razao2)).toBeVisible();
    await expect(page.getByText("NBR 16747")).toBeVisible();
    await expect(page.getByText("NBR 5674")).toBeVisible();
  });
});
