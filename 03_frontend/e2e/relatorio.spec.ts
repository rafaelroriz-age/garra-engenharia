import { test, expect, type Page, type Route } from "@playwright/test";

/**
 * Tela de relatório da inspeção (V1-06) e cadastro de responsável com assinatura.
 *
 * API mockada com `page.route` (sem backend): `GET /inspecoes/{id}`,
 * `GET/PUT /inspecoes/{id}/conteudo/{tipo}`, `GET /inspecoes/{id}/relatorios`,
 * `POST /inspecoes/{id}/relatorios/{tipo}` e `GET .../download/{formato}`.
 * Formatos conforme `04_backend/app/schemas/relatorio*.py` e `lib/types.ts`.
 */

const API = "**/api/v1";
const INSPECAO = "22222222-2222-4222-8222-222222222222";
const CONTRATO = "33333333-3333-4333-8333-333333333333";
const REL_V01 = "44444444-4444-4444-8444-444444444444";
const REL_V02 = "55555555-5555-4555-8555-555555555555";

const INTRO_PADRAO = "O presente laudo técnico apresenta a inspeção predial do Edifício Teste.";

const v01 = {
  id: REL_V01,
  tipo: "LTIP",
  versao: "V01",
  status: "emitido",
  emitido_em: "2026-11-01T12:00:00Z",
  tem_pdf: true,
  tem_docx: true,
};
const v02 = { ...v01, id: REL_V02, versao: "V02", emitido_em: "2026-11-11T12:00:00Z" };

const json = (route: Route, body: unknown, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

function conteudoLtip(salvo = false, textos?: Record<string, string[]>) {
  return {
    inspecao_id: INSPECAO,
    tipo: "LTIP",
    salvo,
    atualizado_em: salvo ? "2026-11-11T15:30:00Z" : null,
    atualizado_por_id: null,
    dados: {
      textos: textos ?? {
        introducao: [INTRO_PADRAO, "Segundo parágrafo da introdução."],
        objetivo: ["Avaliar o estado de conservação."],
        conclusao: ["Conclusão padrão."],
      },
    },
  };
}

async function autenticar(page: Page, role: "auditor" | "auxiliar") {
  await page.addInitScript(() => window.localStorage.setItem("garra:access_token", "token-fake-e2e"));
  await page.route(`${API}/auth/me`, (route) =>
    json(route, { id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", nome: "Usuário Mock", email: "m@x.com", ativo: true, role })
  );
}

interface MockOpcoes {
  tipo?: string;
  conteudo?: unknown;
  versoes?: unknown[];
}

/** Mocks da tela; devolve as chamadas observadas. Rotas específicas registradas depois do genérico. */
async function mockRelatorio(page: Page, opcoes: MockOpcoes = {}) {
  const tipo = opcoes.tipo ?? "LTIP";
  const chamadas = { put: [] as unknown[], post: [] as string[], download: [] as string[] };
  let versoes = opcoes.versoes ?? [v01];

  await page.route(`${API}/**`, (route) => {
    if (route.request().url().includes("/auth/me")) return route.fallback();
    return json(route, []);
  });
  await page.route(`${API}/inspecoes/${INSPECAO}`, (route) =>
    json(route, { id: INSPECAO, contrato_id: CONTRATO, tipo, status: "em_andamento", created_at: "2026-10-01T00:00:00Z", visitas: [] })
  );
  await page.route(`${API}/inspecoes/${INSPECAO}/conteudo/*`, async (route) => {
    if (route.request().method() === "PUT") {
      const body = route.request().postDataJSON() as { dados: { textos: Record<string, string[]> } };
      chamadas.put.push(body);
      return json(route, { ...conteudoLtip(true, body.dados.textos), dados: body.dados });
    }
    return json(route, opcoes.conteudo ?? conteudoLtip());
  });
  await page.route(`${API}/inspecoes/${INSPECAO}/relatorios`, (route) => json(route, versoes));
  await page.route(`${API}/inspecoes/${INSPECAO}/relatorios/*/download/*`, (route) => {
    chamadas.download.push(new URL(route.request().url()).pathname);
    const formato = route.request().url().split("/").pop();
    return json(route, {
      relatorio_id: REL_V01,
      formato,
      url: `https://storage.exemplo/relatorios/ltip-v01.${formato}?assinatura=x`,
      expira_em_segundos: 300,
    });
  });

  return {
    chamadas,
    /** Substitui a resposta de `POST .../relatorios/{tipo}`. */
    async aoEmitir(handler: (route: Route) => Promise<void> | void) {
      await page.route(`${API}/inspecoes/${INSPECAO}/relatorios/*`, async (route) => {
        if (route.request().method() !== "POST") return route.fallback();
        chamadas.post.push(new URL(route.request().url()).pathname);
        await handler(route);
      });
    },
    setVersoes(lista: unknown[]) {
      versoes = lista;
    },
  };
}

/** Abre o grupo colapsável (<details>) pelo título. */
async function abrirGrupo(page: Page, titulo: string) {
  await page.locator("summary").filter({ hasText: titulo }).first().click();
}

test.describe("Relatório da inspeção (V1-06)", () => {
  test("(1) carrega os textos padrão do tipo da inspeção, agrupados e com rótulos legíveis", async ({ page }) => {
    await autenticar(page, "auditor");
    await mockRelatorio(page);

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);

    await expect(page.getByText("Laudo Técnico de Inspeção Predial (LTIP)", { exact: false })).toBeVisible();
    await expect(page.getByText("Usando os textos padrão (ainda não salvos).")).toBeVisible();
    // grupo fechado por padrão; ao abrir, o textarea traz os parágrafos do padrão
    const intro = page.getByLabel("Introdução", { exact: true });
    await expect(intro).toBeHidden();
    await abrirGrupo(page, "Introdução");
    await expect(intro).toBeVisible();
    await expect(intro).toHaveValue(`${INTRO_PADRAO}\n\nSegundo parágrafo da introdução.`);
    await expect(page.locator("summary")).toHaveCount(3);
    await expect(page.getByLabel("Data de emissão")).toBeVisible();
    await expect(page.getByLabel("Local de emissão")).toBeVisible();
  });

  test("(2) salva os textos com o conteúdo completo e mostra confirmação", async ({ page }) => {
    await autenticar(page, "auditor");
    const { chamadas } = await mockRelatorio(page);

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);
    await abrirGrupo(page, "Objetivo");
    await page.getByLabel("Objetivo", { exact: true }).fill("Primeiro parágrafo.\n\nSegundo parágrafo.");
    await page.getByLabel("Local de emissão").fill("Goiânia-GO");
    await page.getByLabel("Data de emissão").fill("2026-11-10");
    await expect(page.getByText("Há alterações não salvas.")).toBeVisible();

    await page.getByRole("button", { name: "Salvar textos" }).click();

    await expect(page.getByText(/Textos salvos em/)).toBeVisible();
    expect(chamadas.put).toHaveLength(1);
    const body = chamadas.put[0] as { dados: Record<string, unknown> & { textos: Record<string, string[]> } };
    expect(body.dados.textos.objetivo).toEqual(["Primeiro parágrafo.", "Segundo parágrafo."]);
    // PUT substitui: as demais chaves vão junto, sem alteração
    expect(body.dados.textos.introducao).toEqual([INTRO_PADRAO, "Segundo parágrafo da introdução."]);
    expect(body.dados.textos.conclusao).toEqual(["Conclusão padrão."]);
    expect(body.dados.local_emissao).toBe("Goiânia-GO");
    expect(body.dados.data_emissao).toBe("2026-11-10");
    // campos de outros tipos não são enviados
    expect(body.dados).not.toHaveProperty("parecer");
    expect(body.dados).not.toHaveProperty("incluir_resumo");
  });

  test("(3) auditor emite nova versão: vê o carregamento e depois a V02 na tabela", async ({ page }) => {
    await autenticar(page, "auditor");
    const mock = await mockRelatorio(page);
    let liberar: () => void = () => {};
    const emissaoLiberada = new Promise<void>((resolve) => (liberar = resolve));
    await mock.aoEmitir(async (route) => {
      await emissaoLiberada; // simula a geração demorada de PDF + DOCX
      mock.setVersoes([v02, v01]);
      await json(
        route,
        { id: REL_V02, inspecao_id: INSPECAO, tipo: "LTIP", versao: "V02", status: "emitido", tem_pdf: true, tem_docx: true },
        201
      );
    });

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);
    const tabela = page.getByRole("table", { name: "Versões do relatório" });
    await expect(tabela.getByRole("row")).toHaveCount(2); // cabeçalho + V01

    await page.getByRole("button", { name: "Emitir nova versão" }).click();
    await expect(page.getByRole("button", { name: "Emitindo..." })).toBeDisabled();
    await expect(page.getByText(/pode levar algumas dezenas de segundos/)).toBeVisible();

    liberar();
    await expect(page.getByText("Versão V02 emitida.")).toBeVisible();
    await expect(tabela.getByRole("row")).toHaveCount(3);
    await expect(tabela.getByRole("row").nth(1)).toContainText("V02");
    expect(mock.chamadas.post).toEqual([`/api/v1/inspecoes/${INSPECAO}/relatorios/ltip`]);
  });

  test("(4) auxiliar não vê 'Emitir nova versão' nem 'Salvar', mas vê as versões e os textos", async ({ page }) => {
    await autenticar(page, "auxiliar");
    await mockRelatorio(page);

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);

    await expect(page.getByRole("button", { name: "Baixar PDF da versão V01" })).toBeVisible();
    await expect(page.getByText("Somente o auditor pode alterar os textos do relatório.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Emitir nova versão" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Salvar textos" })).toHaveCount(0);
    await abrirGrupo(page, "Introdução");
    await expect(page.getByLabel("Introdução", { exact: true })).toHaveAttribute("readonly", "");
  });

  test("(5) 422 de contexto incompleto lista os campos faltantes", async ({ page }) => {
    await autenticar(page, "auditor");
    const mock = await mockRelatorio(page);
    await mock.aoEmitir((route) =>
      route.fulfill({
        status: 422,
        contentType: "application/problem+json",
        body: JSON.stringify({
          type: "https://garra-engenharia.com.br/errors/ltip-contexto-incompleto",
          title: "Contexto do LTIP incompleto",
          status: 422,
          detail: "Dados obrigatórios do LTIP ausentes: edificacao.endereco, responsavel.crea.",
          errors: [
            { field: "edificacao.endereco", message: "Campo obrigatório para emitir o LTIP." },
            { field: "responsavel.crea", message: "Campo obrigatório para emitir o LTIP." },
          ],
        }),
      })
    );

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);
    await page.getByRole("button", { name: "Emitir nova versão" }).click();

    await expect(page.getByText("Contexto do LTIP incompleto")).toBeVisible();
    const lista = page.getByRole("list", { name: "Campos faltantes" });
    await expect(lista.getByRole("listitem")).toHaveCount(2);
    await expect(lista).toContainText("edificacao.endereco");
    await expect(lista).toContainText("responsavel.crea");
    // a tabela continua só com a V01 e o botão volta a ficar disponível
    await expect(page.getByRole("button", { name: "Emitir nova versão" })).toBeEnabled();
  });

  test("(6) download chama a rota da inspeção com o formato e abre a URL pré-assinada", async ({ page }) => {
    await autenticar(page, "auxiliar");
    await page.addInitScript(() => {
      (window as unknown as { __abertas: string[] }).__abertas = [];
      window.open = ((url?: string | URL) => {
        (window as unknown as { __abertas: string[] }).__abertas.push(String(url));
        return null;
      }) as typeof window.open;
    });
    const { chamadas } = await mockRelatorio(page);

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);
    await page.getByRole("button", { name: "Baixar DOCX da versão V01" }).click();
    await expect.poll(() => chamadas.download.length).toBe(1);
    await page.getByRole("button", { name: "Baixar PDF da versão V01" }).click();
    await expect.poll(() => chamadas.download.length).toBe(2);

    expect(chamadas.download).toEqual([
      `/api/v1/inspecoes/${INSPECAO}/relatorios/${REL_V01}/download/docx`,
      `/api/v1/inspecoes/${INSPECAO}/relatorios/${REL_V01}/download/pdf`,
    ]);
    await expect
      .poll(() => page.evaluate(() => (window as unknown as { __abertas: string[] }).__abertas))
      .toEqual([
        "https://storage.exemplo/relatorios/ltip-v01.docx?assinatura=x",
        "https://storage.exemplo/relatorios/ltip-v01.pdf?assinatura=x",
      ]);
  });

  test("(7) vistoria cautelar em tela de 5,5\": campos do tipo e nenhuma rolagem horizontal", async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 640 });
    await autenticar(page, "auditor");
    await mockRelatorio(page, {
      tipo: "VISTORIA_CAUTELAR",
      versoes: [{ ...v02, tipo: "VISTORIA_CAUTELAR" }, { ...v01, tipo: "VISTORIA_CAUTELAR" }],
      conteudo: {
        inspecao_id: INSPECAO,
        tipo: "VISTORIA_CAUTELAR",
        salvo: true,
        dados: {
          textos: {
            introducao: [],
            correlacao_tecnica_entre_origem_provavel_repercussao_funcional_e_responsabilidade: [
              "Texto longo ".repeat(40),
            ],
            parecer_tecnico: ["Parecer padrão."],
          },
          parecer: "Recebimento com ressalvas.",
          datas_vistorias: ["2026-10-01", "2026-10-15"],
          metodologia_corretiva: { "66666666-6666-4666-8666-666666666666": "Refazer rejunte." },
        },
      },
    });

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);
    await expect(page.getByLabel(/Parecer técnico \(complemento/)).toHaveValue("Recebimento com ressalvas.");
    await expect(page.getByLabel("Data da vistoria 2", { exact: true })).toHaveValue("2026-10-15");
    await expect(page.getByLabel("Unidade vistoriada")).toHaveCount(0);
    await abrirGrupo(page, "9. Análise e considerações técnicas");
    await expect(page.getByLabel(/9\.8 Correlação técnica/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Baixar DOCX da versão V02" })).toBeVisible();

    const larguras = await page.evaluate(() => ({
      scroll: document.documentElement.scrollWidth,
      client: document.documentElement.clientWidth,
    }));
    expect(larguras.scroll).toBeLessThanOrEqual(larguras.client);
    // as tabelas também cabem sem rolagem interna
    const tabelaCabe = await page
      .getByRole("table", { name: "Versões do relatório" })
      .evaluate((tabela) => tabela.parentElement!.scrollWidth <= tabela.parentElement!.clientWidth);
    expect(tabelaCabe).toBe(true);
  });

  test("(8) salvar preserva campos que a tela não edita (PUT substitui)", async ({ page }) => {
    await autenticar(page, "auditor");
    const { chamadas } = await mockRelatorio(page, {
      tipo: "VISTORIA_RESIDENCIAL",
      conteudo: {
        inspecao_id: INSPECAO,
        tipo: "VISTORIA_RESIDENCIAL",
        salvo: false,
        dados: {
          textos: { s1: ["Introdução residencial."], s4_2_4_1: ["Região."] },
          fundamentacao_tecnica: { "77777777-7777-4777-8777-777777777777": ["Fundamentação."] },
        },
      },
    });

    await page.goto(`/inspecoes/${INSPECAO}/relatorio`);
    await page.getByLabel("Unidade vistoriada").fill("Apartamento 101");
    await page.getByRole("button", { name: "Adicionar data" }).click();
    await page.getByLabel("Data da vistoria 1", { exact: true }).fill("2026-09-30");
    await page.getByRole("button", { name: "Salvar textos" }).click();
    await expect(page.getByText(/Textos salvos em/)).toBeVisible();

    const body = chamadas.put[0] as { dados: Record<string, unknown> };
    expect(body.dados.unidade).toBe("Apartamento 101");
    expect(body.dados.datas_vistorias).toEqual(["2026-09-30"]);
    expect(body.dados.fundamentacao_tecnica).toEqual({
      "77777777-7777-4777-8777-777777777777": ["Fundamentação."],
    });
    expect(body.dados.textos).toEqual({ s1: ["Introdução residencial."], s4_2_4_1: ["Região."] });
  });
});

test.describe("Responsáveis: dados de assinatura (V1-06)", () => {
  test("(9) cadastra responsável com título, qualificações e imagem da assinatura", async ({ page }) => {
    await autenticar(page, "auditor");
    const criados: unknown[] = [];
    const uploads: string[] = [];
    await page.route(`${API}/**`, (route) => {
      if (route.request().url().includes("/auth/me")) return route.fallback();
      return json(route, []);
    });
    await page.route(`${API}/responsaveis`, (route) => {
      if (route.request().method() === "POST") {
        const body = route.request().postDataJSON();
        criados.push(body);
        return json(route, { id: "88888888-8888-4888-8888-888888888888", ...body }, 201);
      }
      return json(route, criados.map((c, i) => ({ id: `id-${i}`, ...(c as object) })));
    });
    await page.route(`${API}/fotos/upload`, (route) => {
      uploads.push(route.request().headers()["content-type"] ?? "");
      return json(route, { storage_key: "fotos/assinatura-abc.png", url: "data:image/png;base64,iVBORw0KGgo=" }, 201);
    });

    await page.setViewportSize({ width: 360, height: 640 });
    await page.goto("/responsaveis");
    await page.getByRole("button", { name: "Novo responsável" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Nome *").fill("Eng. Fulano de Tal");
    await dialog.getByLabel("CREA").fill("12345/D-GO");
    await dialog.getByLabel("Título profissional").fill("Engenheiro Civil");
    await dialog.getByRole("button", { name: "Adicionar qualificação" }).click();
    await dialog.getByLabel("Qualificação 1", { exact: true }).fill("Especialista em Patologia das Construções");
    await dialog.getByRole("button", { name: "Adicionar qualificação" }).click();
    await dialog.getByLabel("Qualificação 2", { exact: true }).fill("Perito judicial");
    await dialog.getByLabel(/Imagem da assinatura/).setInputFiles({
      name: "assinatura.png",
      mimeType: "image/png",
      buffer: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
        "base64"
      ),
    });
    await expect(dialog.getByText("Assinatura enviada.")).toBeVisible();
    await dialog.getByRole("button", { name: "Cadastrar responsável" }).click();

    await expect(dialog).toBeHidden();
    expect(uploads[0]).toContain("multipart/form-data");
    expect(criados[0]).toMatchObject({
      nome: "Eng. Fulano de Tal",
      tipo: "fiscal",
      crea: "12345/D-GO",
      titulo_profissional: "Engenheiro Civil",
      qualificacoes: ["Especialista em Patologia das Construções", "Perito judicial"],
      assinatura_storage_key: "fotos/assinatura-abc.png",
    });
    await expect(page.getByText("Engenheiro Civil")).toBeVisible();
    await expect(page.getByText("Assinatura cadastrada")).toBeVisible();
  });
});
