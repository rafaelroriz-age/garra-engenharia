"use client";

import { useSearchParams } from "next/navigation";

/**
 * Lê o `?id=` da URL. Substitui os antigos segmentos dinâmicos `[id]`, que
 * não funcionam no export estático (`output: "export"`) servido pelo GitHub
 * Pages: os IDs vêm do banco e não são conhecidos em build time.
 *
 * Quem usa este hook precisa estar sob um `<Suspense>` (ver os `layout.tsx`
 * de `contratos/detalhe`, `edificacoes/detalhe` e `inspecoes`).
 */
export function useIdParam(): string {
  return useSearchParams().get("id") ?? "";
}
