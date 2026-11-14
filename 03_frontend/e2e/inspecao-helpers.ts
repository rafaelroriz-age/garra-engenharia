import type { APIRequestContext, Page } from "@playwright/test";
import { expect } from "@playwright/test";

import {
  API_BASE_URL,
  cnpjUnico,
  criarResponsavel,
  loginPelaUI,
  nomeUnico,
  type AuthContext,
  registrarUsuario,
} from "./helpers";

/**
 * Apoio dos specs de Visitas, Ocorrências e Fotos (BL-21): cria, pela UI, edificação e contrato
 * do tipo pedido e devolve o id da Inspeção (1:1 com o Contrato). Mesmo padrão de `rfo.spec.ts`
 * e `ltip.spec.ts`, sem alterá-los.
 */
export interface InspecaoE2E {
  auth: AuthContext;
  inspecaoId: string;
}

export async function prepararInspecao(
  page: Page,
  request: APIRequestContext,
  tipo: "RFO" | "LTIP"
): Promise<InspecaoE2E> {
  const auth = await registrarUsuario(request);
  const fiscalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Eng. Fiscal"),
    tipo: "fiscal",
    crea: "333333-GO",
  });
  const responsavelLegalId = await criarResponsavel(request, auth.token, {
    nome: nomeUnico("Responsável Legal"),
    tipo: "responsavel_legal",
  });

  await loginPelaUI(page, auth);

  const nomeEdificacao = nomeUnico(`Ed. ${tipo}`);
  await page.goto("/edificacoes");
  await page.getByRole("button", { name: "Nova edificação" }).click();
  const dialogEdificacao = page.getByRole("dialog");
  await dialogEdificacao.getByLabel("Nome").fill(nomeEdificacao);
  await dialogEdificacao.getByLabel("Endereço").fill("Rua dos Testes, 1");
  await dialogEdificacao.getByRole("button", { name: "Criar edificação" }).click();
  await expect(dialogEdificacao).toBeHidden();

  const numeroContrato = `CT-${tipo}-${Date.now()}`;
  await page.goto("/contratos");
  await page.getByRole("button", { name: "Novo contrato" }).click();
  const dialogContrato = page.getByRole("dialog");
  await dialogContrato.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
  await dialogContrato.getByLabel("Número do contrato").fill(numeroContrato);
  await dialogContrato.getByLabel("Tipo de serviço").selectOption(tipo);
  await dialogContrato.getByLabel("Engenheiro fiscal (ID)").fill(fiscalId);
  await dialogContrato.getByLabel("ART de Fiscalização").fill("ART-FISC-0001");
  await dialogContrato.getByLabel("Razão social").fill("Construtora Exemplo Ltda");
  await dialogContrato.getByLabel("CNPJ").fill(cnpjUnico());
  await dialogContrato.getByLabel("Responsável legal (ID)").fill(responsavelLegalId);
  await dialogContrato.getByLabel("ART de Execução").fill("ART-EXEC-0001");
  await dialogContrato.getByRole("button", { name: "Criar contrato" }).click();
  await expect(dialogContrato).toBeHidden();

  await page.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
  const linkContrato = page.getByRole("link", { name: numeroContrato });
  await expect(linkContrato).toBeVisible();
  await linkContrato.click();
  await expect(page).toHaveURL(/\/contratos\/detalhe\/\\?id=[0-9a-f-]+$/);

  const alvo = tipo === "RFO" ? "visitas" : "ocorrencias";
  await page.getByRole("link", { name: tipo === "RFO" ? "Visitas (RF-03)" : "Ocorrências (RF-04)" }).click();
  await expect(page).toHaveURL(new RegExp(`/inspecoes/${alvo}/\\?id=[0-9a-f-]+$`));
  const inspecaoId = page.url().match(new RegExp(`/inspecoes/${alvo}/\\?id=([0-9a-f-]+)$`))?.[1];
  if (!inspecaoId) throw new Error("Não foi possível extrair o id da inspeção da URL.");
  return { auth, inspecaoId };
}

/** Remove, via API, os recursos que a API permite apagar (fotos e ocorrências). Falhas são ignoradas. */
export async function apagarRecursos(
  request: APIRequestContext,
  token: string,
  caminhos: string[]
): Promise<void> {
  for (const caminho of caminhos) {
    await request
      .delete(`${API_BASE_URL}${caminho}`, { headers: { Authorization: `Bearer ${token}` } })
      .catch(() => undefined);
  }
}
