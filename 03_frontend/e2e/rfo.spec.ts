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
 * Fluxo 1 — Relatório de Fiscalização de Obra (RFO)
 * `00_docs/estudo-do-contexto.md` Seção 8, `arquitetura.md` Seção 10.6.
 *
 * Cadastra edificação -> cadastra contrato RFO -> cria visita com
 * equipe/serviços/medições -> anexa foto -> valida o estado atual da
 * geração de relatório.
 *
 * A geração de relatório (RF-06) está bloqueada por B-02 (BL-12/BL-13
 * aguardando o `.docx` original do cliente — ver `backlog-tarefas.md`),
 * portanto o teste valida o placeholder "em construção" em vez de simular
 * um job que ainda não existe no backend.
 */
test("Fluxo RFO: edificação, contrato, visita com equipe/medições/foto", async ({ page, request }) => {
  const auth = await registrarUsuario(request);

  const fiscalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Eng. Fiscal"),
    tipo: "fiscal",
    crea: "111111-GO",
  });
  const responsavelLegalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Responsável Legal Executora"),
    tipo: "responsavel_legal",
  });

  await loginPelaUI(page, auth);

  // 1. Cadastra edificação (RF-01, BL-08)
  const nomeEdificacao = nomeUnico("Ed. RFO");
  await page.goto("/edificacoes");
  await page.getByRole("button", { name: "Nova edificação" }).click();
  const dialogEdificacao = page.getByRole("dialog");
  await dialogEdificacao.getByLabel("Nome").fill(nomeEdificacao);
  await dialogEdificacao.getByLabel("Endereço").fill("Rua das Obras, 123");
  await dialogEdificacao.getByRole("button", { name: "Criar edificação" }).click();
  await expect(dialogEdificacao).toBeHidden();
  // Filtra pelo nome único: o banco de dev compartilhado acumula muitas edificações
  // de execuções anteriores, e a nova pode não aparecer na 1ª página sem o filtro.
  await page.getByPlaceholder("Buscar por nome ou endereço...").fill(nomeEdificacao);
  await expect(page.getByRole("link", { name: nomeEdificacao })).toBeVisible();

  // 2. Cadastra contrato RFO (RF-02, RF-12, RN-06, RN-09, BL-09)
  const numeroContrato = `CT-RFO-${Date.now()}`;
  await page.goto("/contratos");
  await page.getByRole("button", { name: "Novo contrato" }).click();
  const dialogContrato = page.getByRole("dialog");
  await dialogContrato.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
  await dialogContrato.getByLabel("Número do contrato").fill(numeroContrato);
  await dialogContrato.getByLabel("Tipo de serviço").selectOption("RFO");
  await dialogContrato.getByLabel("Engenheiro fiscal (ID)").fill(fiscalId);
  await dialogContrato.getByLabel("ART de Fiscalização").fill("ART-FISC-0001");
  await dialogContrato.getByLabel("Razão social").fill("Construtora Exemplo Ltda");
  await dialogContrato.getByLabel("CNPJ").fill(cnpjUnico());
  await dialogContrato.getByLabel("Responsável legal (ID)").fill(responsavelLegalId);
  await dialogContrato.getByLabel("ART de Execução").fill("ART-EXEC-0001");
  await dialogContrato.getByRole("button", { name: "Criar contrato" }).click();
  await expect(dialogContrato).toBeHidden();

  // Filtra pela edificação (única a este teste) para achar o contrato mesmo com
  // muitos contratos pré-existentes no banco de dev compartilhado.
  await page.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
  const linkContrato = page.getByRole("link", { name: numeroContrato });
  await expect(linkContrato).toBeVisible();
  await linkContrato.click();
  await expect(page).toHaveURL(/\/contratos\/detalhe\/\?id=[0-9a-f-]+$/);

  // 3. Navega para a Inspeção (1:1 com o Contrato) recém-criada
  await expect(page.getByText("Inspeção", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Visitas (RF-03)" }).click();
  await expect(page).toHaveURL(/\/inspecoes\/visitas\/\?id=[0-9a-f-]+$/);

  // 4. Cria visita com equipe, serviços e medições (RF-03, RN-01, RN-02, BL-10)
  await page.getByRole("button", { name: "Nova visita" }).click();
  await page.getByLabel("Data da visita").fill("2026-08-05");
  await page.getByLabel("Serviços executados").fill("Concretagem da laje do 2º pavimento.");
  await page.getByRole("button", { name: "Registrar visita" }).click();

  await expect(page.getByText(/Visita #1/)).toBeVisible();

  // Equipe presente (mão de obra)
  const equipeSection = page.locator("section", { has: page.getByRole("heading", { name: "Equipe presente" }) });
  await equipeSection.getByLabel("Função").fill("Pedreiro");
  await equipeSection.getByLabel("Qtd.").fill("4");
  await equipeSection.getByRole("button", { name: "Adicionar" }).click();
  await expect(equipeSection.getByRole("cell", { name: "Pedreiro" })).toBeVisible();

  // Medições parciais
  const medicoesSection = page.locator("section", { has: page.getByRole("heading", { name: "Medições parciais" }) });
  await medicoesSection.getByLabel("Descrição").fill("Concretagem");
  await medicoesSection.getByLabel("Qtd.").fill("35.5");
  await medicoesSection.getByLabel("Unidade").fill("m³");
  await medicoesSection.getByRole("button", { name: "Adicionar" }).click();
  await expect(medicoesSection.getByRole("cell", { name: "Concretagem" })).toBeVisible();

  // 5. Anexa foto à visita (RF-05, RNF-02 parcial, BL-11) via editor de anotação (DEC-19)
  const fotosSection = page.locator("section", { has: page.getByRole("heading", { name: "Fotos da visita" }) });
  await enviarFotoViaEditor(page, fotosSection);
  await expect(fotosSection.getByRole("img").first()).toBeVisible();

  // 6. Dispara geração de relatório — bloqueada por B-02 (BL-12/BL-13): valida
  // que o sistema informa corretamente o estado "em construção" em vez de
  // simular um job de geração que ainda não existe no backend.
  await page.goto(page.url().replace(/\/visitas$/, "/relatorio"));
  await expect(page.getByText(/em construção/i)).toBeVisible();
  await expect(page.getByText(/BL-12\/BL-13/i)).toBeVisible();
});
