import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Transforma um status em `snake_case` (ex.: `em_andamento`) em rótulo legível ("Em andamento"). */
export function humanizeStatus(status: string): string {
  const texto = status.replace(/_/g, " ").toLowerCase()
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

/**
 * Prefixa um caminho absoluto com o `basePath` do app (ex.: `/garra-engenharia`
 * no GitHub Pages). Necessário só para URLs em string crua (metadata, `<img>`,
 * `<a>`); `next/link` e `useRouter` já aplicam o basePath sozinhos.
 */
export function withBasePath(path: string): string {
  return `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}${path}`
}
