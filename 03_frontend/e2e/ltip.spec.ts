import { test, expect } from "@playwright/test";

import {
  criarResponsavel,
  cnpjUnico,
  enviarFotoViaEditor,
  loginPelaUI,
  nomeUnico,
  registrarUsuario,
} from "./helpers";

/**
 * Fluxo 2 — Laudo Técnico de Inspeção Predial (LTIP)
 * `00_docs/estudo-do-contexto.md` Seção 8, `arquitetura.md` Seção 10.6.
 *
 * Cadastra edificação -> cadastra contrato LTIP -> registra ocorrências em
 * múltiplos sistemas prediais com fotos -> valida o dashboard de saúde
 * (BL-16) -> valida o estado atual da geração de laudo.
 *
 * A geração de laudo (RF-06) está bloqueada por B-02 (BL-17 aguardando o
 * `.docx` original do cliente — ver `backlog-tarefas.md`), portanto o teste
 * valida o placeholder "em construção" em vez de simular um job que ainda
 * não existe no backend.
 */
test("Fluxo LTIP: edificação, contrato, ocorrências em múltiplos sistemas com fotos e dashboard", async ({
  page,
  request,
}) => {
  const auth = await registrarUsuario(request);

  const fiscalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Eng. Fiscal LTIP"),
    tipo: "fiscal",
    crea: "222222-GO",
  });
  const responsavelLegalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Responsável Legal Executora LTIP"),
    tipo: "responsavel_legal",
  });

  await loginPelaUI(page, auth);

  // 1. Cadastra edificação (RF-01, BL-08)
  const nomeEdificacao = nomeUnico("Ed. LTIP");
  await page.goto("/edificacoes");
  await page.getByRole("button", { name: "Nova edificação" }).click();
  const dialogEdificacao = page.getByRole("dialog");
  await dialogEdificacao.getByLabel("Nome").fill(nomeEdificacao);
  await dialogEdificacao.getByLabel("Endereço").fill("Av. da Inspeção, 456");
  await dialogEdificacao.getByRole("button", { name: "Criar edificação" }).click();
  await expect(dialogEdificacao).toBeHidden();
  // Filtra pelo nome único: o banco de dev compartilhado acumula muitas edificações
  // de execuções anteriores, e a nova pode não aparecer na 1ª página sem o filtro.
  await page.getByPlaceholder("Buscar por nome ou endereço...").fill(nomeEdificacao);
  const linkEdificacao = page.getByRole("link", { name: nomeEdificacao });
  await expect(linkEdificacao).toBeVisible();
  await linkEdificacao.click();
  await expect(page).toHaveURL(/\/edificacoes\/detalhe\/\?id=[0-9a-f-]+$/);
  const edificacaoId = page.url().match(/\/edificacoes\/detalhe\/\?id=([0-9a-f-]+)$/)?.[1];
  if (!edificacaoId) throw new Error("Não foi possível extrair o id da edificação da URL.");

  // 2. Cadastra contrato LTIP (RF-02, RN-06, RN-09, BL-09)
  const numeroContrato = `CT-LTIP-${Date.now()}`;
  await page.goto("/contratos");
  await page.getByRole("button", { name: "Novo contrato" }).click();
  const dialogContrato = page.getByRole("dialog");
  await dialogContrato.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
  await dialogContrato.getByLabel("Número do contrato").fill(numeroContrato);
  await dialogContrato.getByLabel("Tipo de serviço").selectOption("LTIP");
  await dialogContrato.getByLabel("Engenheiro fiscal (ID)").fill(fiscalId);
  await dialogContrato.getByLabel("ART de Fiscalização").fill("ART-FISC-LTIP-0001");
  await dialogContrato.getByLabel("Razão social").fill("Vistorias Técnicas Ltda");
  await dialogContrato.getByLabel("CNPJ").fill(cnpjUnico());
  await dialogContrato.getByLabel("Responsável legal (ID)").fill(responsavelLegalId);
  await dialogContrato.getByLabel("ART de Execução").fill("ART-EXEC-LTIP-0001");
  await dialogContrato.getByRole("button", { name: "Criar contrato" }).click();
  await expect(dialogContrato).toBeHidden();

  // Filtra pela edificação (única a este teste) para achar o contrato mesmo com
  // muitos contratos pré-existentes no banco de dev compartilhado.
  await page.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
  const linkContrato = page.getByRole("link", { name: numeroContrato });
  await expect(linkContrato).toBeVisible();
  await linkContrato.click();

  // 3. Navega para Ocorrências da Inspeção (1:1 com o Contrato)
  await page.getByRole("link", { name: "Ocorrências (RF-04)" }).click();
  await expect(page).toHaveURL(/\/inspecoes\/ocorrencias\/\?id=[0-9a-f-]+$/);
  const inspecaoId = page.url().match(/\/inspecoes\/ocorrencias\/\?id=([0-9a-f-]+)$/)?.[1];
  if (!inspecaoId) throw new Error("Não foi possível extrair o id da inspeção da URL.");

  // 4. Registra ocorrências em 2 sistemas prediais diferentes, cada uma com foto (RF-04, RN-03, RN-05, RN-10, BL-14)
  await criarOcorrencia(page, {
    sistemaIndex: 1,
    situacao: "Não Conforme",
    classificacao: "Anomalia",
    tipoEspecificoLabel: "Tipo de Anomalia",
    grauRisco: "Crítico",
    descricao: "Infiltração aparente na fachada.",
  });
  await criarOcorrencia(page, {
    sistemaIndex: 2,
    situacao: "Não Conforme",
    classificacao: "Falha",
    tipoEspecificoLabel: "Tipo de Falha",
    grauRisco: "Médio",
    descricao: "Ausência de manutenção preventiva registrada.",
  });

  await expect(page.getByRole("row")).toHaveCount(3); // 1 cabeçalho + 2 ocorrências

  // 5. Valida o dashboard de saúde da edificação (RF-07, BL-16)
  await page.goto(`/dashboard?edificacaoId=${edificacaoId}`);
  await expect(page.getByText("Total de ocorrências")).toBeVisible();
  // Cada indicador do dashboard é um `KpiTile` com `role="group"` nomeado pelo título —
  // seleção semântica, sem depender de classes utilitárias de estilo.
  const totalCard = page.getByRole("group", { name: "Total de ocorrências", exact: true });
  await expect(totalCard).toHaveCount(1);
  await expect(totalCard.getByText("2", { exact: true })).toBeVisible();
  await expect(page.getByText("Ocorrências em Grau Crítico")).toBeVisible();

  // 6. Dispara geração de laudo — bloqueada por B-02 (BL-17, RN-11): valida
  // que o sistema informa corretamente o estado "em construção" em vez de
  // simular um job de geração que ainda não existe no backend.
  await page.goto(`/inspecoes/relatorio/?id=${inspecaoId}`);
  await expect(page.getByText(/em construção/i)).toBeVisible();
  await expect(page.getByText(/BL-12\/BL-13/i)).toBeVisible();
});

interface OcorrenciaInputTeste {
  sistemaIndex: number;
  situacao: "Conforme" | "Não Conforme";
  classificacao: "Anomalia" | "Falha";
  tipoEspecificoLabel: "Tipo de Anomalia" | "Tipo de Falha";
  grauRisco: "Mínimo" | "Médio" | "Crítico";
  descricao: string;
}

/** Cria 1 ocorrência completa (classificação RN-05) e anexa 1 foto, dentro do dialog da Ocorrência. */
async function criarOcorrencia(page: import("@playwright/test").Page, input: OcorrenciaInputTeste) {
  await page.getByRole("button", { name: "Nova ocorrência" }).click();
  const dialog = page.getByRole("dialog");

  await dialog.getByLabel("Sistema predial").selectOption({ index: input.sistemaIndex });
  await dialog.getByLabel("Situação").selectOption({ label: input.situacao });
  await dialog.getByLabel("Classificação").selectOption({ label: input.classificacao });
  await dialog.getByLabel(input.tipoEspecificoLabel).selectOption({ index: 1 });
  await dialog.getByLabel("Grau de Risco (CMM)").selectOption({ label: input.grauRisco });
  await dialog.getByLabel("Descrição").fill(input.descricao);

  const criarResponse = page.waitForResponse(
    (response) => /\/ocorrencias$/.test(new URL(response.url()).pathname) && response.request().method() === "POST"
  );
  await dialog.getByRole("button", { name: "Criar ocorrência" }).click();
  await criarResponse;

  await enviarFotoViaEditor(page, dialog);
  await expect(dialog.getByRole("img").first()).toBeVisible();

  await dialog.getByRole("button", { name: "Concluir" }).click();
  await expect(dialog).toBeHidden();
}
