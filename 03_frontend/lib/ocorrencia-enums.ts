/**
 * Value Objects de classificação de Ocorrência (RN-05, arquitetura.md Seção 9.14:
 * `Situacao`, `Classificacao`, `GrauRisco`). Espelha os Enums Pydantic que o
 * backend adota nos endpoints de Ocorrência (BL-14) — apenas a representação
 * de opções/rótulos para os `<select>` do formulário, sem nenhuma regra de
 * negócio (a validação definitiva é sempre do backend).
 *
 * Assunção a confirmar quando o backend do BL-14 for implementado: valores
 * serializados em `UPPER_SNAKE_CASE`, alinhados ao padrão já usado por
 * `TipoServico`/`StatusContrato` em `lib/types.ts`.
 */

export type Situacao = "CONFORME" | "NAO_CONFORME";

export const SITUACAO_OPTIONS: { value: Situacao; label: string }[] = [
  { value: "CONFORME", label: "Conforme" },
  { value: "NAO_CONFORME", label: "Não Conforme" },
];

export type Classificacao = "ANOMALIA" | "FALHA" | "ANOMALIA_FALHA" | "NAO_SE_APLICA";

export const CLASSIFICACAO_OPTIONS: { value: Classificacao; label: string }[] = [
  { value: "ANOMALIA", label: "Anomalia" },
  { value: "FALHA", label: "Falha" },
  { value: "ANOMALIA_FALHA", label: "Anomalia + Falha" },
  { value: "NAO_SE_APLICA", label: "Não se Aplica" },
];

/** RN-05: tipo de anomalia é exigido quando a classificação envolve Anomalia. */
export function exigeTipoAnomalia(classificacao: string | undefined): boolean {
  return classificacao === "ANOMALIA" || classificacao === "ANOMALIA_FALHA";
}

/** RN-05: tipo de falha é exigido quando a classificação envolve Falha. */
export function exigeTipoFalha(classificacao: string | undefined): boolean {
  return classificacao === "FALHA" || classificacao === "ANOMALIA_FALHA";
}

export type GrauRisco = "MINIMO" | "MEDIO" | "CRITICO";

export const GRAU_RISCO_OPTIONS: { value: GrauRisco; label: string }[] = [
  { value: "MINIMO", label: "Mínimo" },
  { value: "MEDIO", label: "Médio" },
  { value: "CRITICO", label: "Crítico" },
];

/** Variante de `Badge` (`components/ui/badge.tsx`) por Grau de Risco, para leitura visual rápida. */
export function grauRiscoBadgeVariant(grauRisco: string | null | undefined): "destructive" | "secondary" | "outline" {
  switch (grauRisco) {
    case "CRITICO":
      return "destructive";
    case "MEDIO":
      return "secondary";
    default:
      return "outline";
  }
}

export function grauRiscoLabel(grauRisco: string | null | undefined): string {
  return GRAU_RISCO_OPTIONS.find((option) => option.value === grauRisco)?.label ?? "—";
}

export function situacaoLabel(situacao: string | null | undefined): string {
  return SITUACAO_OPTIONS.find((option) => option.value === situacao)?.label ?? "—";
}

export function classificacaoLabel(classificacao: string | null | undefined): string {
  return CLASSIFICACAO_OPTIONS.find((option) => option.value === classificacao)?.label ?? "—";
}
