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
 * Dashboard de saúde por sistema predial (RF-07, BL-16, BL-21).
 *
 * Semeia via API uma edificação nova + contrato (que origina a Inspeção) + 3 ocorrências no
 * mesmo sistema predial e confere que os indicadores exibidos batem com os dados criados.
 * (`app/scripts/seed_demo.py` não existe no repositório; por isso o seed é feito via API,
 * com nomes únicos "E2E" por execução.) As ocorrências criadas são removidas ao final
 * (`DELETE /ocorrencias/{id}`); edificação e contrato não têm DELETE na API.
 */
test("Dashboard: indicadores por sistema predial batem com as ocorrências semeadas", async ({
  page,
  request,
}) => {
  const auth = await registrarUsuario(request);
  const headers = { Authorization: `Bearer ${auth.token}` };

  const fiscalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Eng. Fiscal"),
    tipo: "fiscal",
    crea: "333333-GO",
  });
  const legalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Resp. Legal"),
    tipo: "responsavel_legal",
  });

  // Edificação
  const nomeEdificacao = nomeUnico("Ed. Dashboard");
  const edResp = await request.post(`${API_BASE_URL}/edificacoes`, {
    data: { nome: nomeEdificacao, endereco: "Rua do Dashboard, 300" },
    headers,
  });
  expect(edResp.ok(), await edResp.text()).toBeTruthy();
  const edificacao = (await edResp.json()) as { id: string };

  // Contrato -> Inspeção
  const ctResp = await request.post(`${API_BASE_URL}/contratos`, {
    data: {
      edificacao_id: edificacao.id,
      fiscal_id: fiscalId,
      numero: `CT-DASH-${Date.now()}`,
      tipo_servico: "LTIP",
      art_fiscalizacao: "ART-DASH-E2E",
      executores: [
        {
          responsavel_legal_id: legalId,
          razao_social: nomeUnico("Executora"),
          cnpj: cnpjUnico(),
          art_execucao: "ART-EXEC-E2E",
        },
      ],
      nbrs: [],
    },
    headers,
  });
  expect(ctResp.ok(), await ctResp.text()).toBeTruthy();
  const contrato = (await ctResp.json()) as { inspecao: { id: string } | null };
  expect(contrato.inspecao).not.toBeNull();
  const inspecaoId = contrato.inspecao!.id;

  // Sistema predial + subsistema do gabarito
  const sisResp = await request.get(`${API_BASE_URL}/sistemas-prediais`, {
    headers,
  });
  expect(sisResp.ok()).toBeTruthy();
  const sistemas = (await sisResp.json()) as {
    id: string;
    nome: string;
    subsistemas: { id: string; nome: string }[];
  }[];
  const sistema = sistemas.find((s) => s.subsistemas.length > 0);
  test.skip(
    !sistema,
    "Gabarito de sistemas prediais não carregado (rode app.scripts.seed_gabarito).",
  );
  const subsistema = sistema!.subsistemas[0];

  // 3 ocorrências no mesmo sistema: 1 conforme/mínimo, 1 não conforme/médio, 1 não conforme/crítico
  const base = {
    inspecao_id: inspecaoId,
    sistema_id: sistema!.id,
    subsistema_id: subsistema.id,
  };
  const payloads = [
    {
      ...base,
      situacao: "CONFORME",
      classificacao: "NAO_SE_APLICA",
      grau_risco: "MINIMO",
      gut_gravidade: 1,
    },
    {
      ...base,
      situacao: "NAO_CONFORME",
      classificacao: "ANOMALIA",
      tipo_anomalia: "Fissura E2E",
      grau_risco: "MEDIO",
      gut_gravidade: 3,
    },
    {
      ...base,
      situacao: "NAO_CONFORME",
      classificacao: "FALHA",
      tipo_falha: "Vazamento E2E",
      grau_risco: "CRITICO",
      gut_gravidade: 5,
    },
  ];
  const ocorrenciaIds: string[] = [];
  try {
    for (const data of payloads) {
      const r = await request.post(
        `${API_BASE_URL}/inspecoes/${inspecaoId}/ocorrencias`,
        { data, headers },
      );
      expect(r.status(), await r.text()).toBe(201);
      ocorrenciaIds.push(((await r.json()) as { id: string }).id);
    }

    // O backend é a fonte de verdade dos agregados.
    const apiDash = await request.get(
      `${API_BASE_URL}/edificacoes/${edificacao.id}/dashboard`,
      { headers },
    );
    expect(apiDash.ok()).toBeTruthy();
    const agregado = (await apiDash.json()) as {
      conformidade_por_sistema: {
        sistema_id: string;
        conforme: number;
        nao_conforme: number;
        total: number;
      }[];
    };
    const linha = agregado.conformidade_por_sistema.find(
      (c) => c.sistema_id === sistema!.id,
    );
    expect(linha).toMatchObject({ conforme: 1, nao_conforme: 2, total: 3 });

    // UI
    await loginPelaUI(page, auth);
    await page.goto(`/dashboard?edificacaoId=${edificacao.id}`);
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();

    // Indicadores (`KpiTile`) expõem `role="group"` nomeado pelo título.
    const card = (titulo: string) => page.getByRole("group", { name: titulo, exact: true });

    // Cartões de totais
    await expect(card("Total de ocorrências")).toContainText("3");
    await expect(card("Conforme").first()).toContainText("1");
    await expect(page.getByText("(33%)")).toBeVisible();
    await expect(page.getByText("(67%)")).toBeVisible();
    await expect(card("Ocorrências em Grau Crítico")).toContainText("1");

    // Indicadores por sistema predial
    await expect(
      page.getByText("Conformidade e Grau de Risco por sistema", {
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByText(sistema!.nome, { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText("1 conforme · 2 não conforme")).toBeVisible();
    await expect(page.getByText(/1 mínimo, 1 médio, 1 crítico/)).toBeVisible();
    await expect(page.getByText("1 crítico(s)")).toBeVisible();
    await expect(
      page.getByRole("progressbar", { name: `${sistema!.nome}: 33% conforme` }),
    ).toBeVisible();

    // Gravidade GUT média por subsistema: (1 + 3 + 5) / 3 = 3.0
    await expect(
      page.getByText("Gravidade GUT média por subsistema", { exact: true }),
    ).toBeVisible();
    await expect(page.getByText(subsistema.nome).first()).toBeVisible();
    await expect(page.getByText("3.0", { exact: true })).toBeVisible();
  } finally {
    for (const id of ocorrenciaIds) {
      await request.delete(`${API_BASE_URL}/ocorrencias/${id}`, { headers });
    }
  }
});
