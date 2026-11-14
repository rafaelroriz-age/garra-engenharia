import { Suspense } from "react";

/**
 * Limite de Suspense exigido pelo `useSearchParams()` (via `useIdParam`) no
 * export estático do Next.js — as páginas abaixo leem o `?id=` da URL.
 */
export default function Layout({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={null}>{children}</Suspense>;
}
