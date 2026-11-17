import { cn, withBasePath } from "@/lib/utils";

export type LogoVariant = "principal" | "horizontal" | "compacta";

const LOGO_ALT = "Garra Perícias e Avaliações";

interface LogoProps {
  variant: LogoVariant;
  className?: string;
}

/**
 * Marca oficial "Garra Perícias e Avaliações": SVGs vetorizados em `public/brand/`
 * (gerados da marca oficial). Proporção 814×737 (símbolo + nome).
 *
 * `principal` (sobre fundo claro, ex.: login mobile) → `logo-garra.svg`.
 * `horizontal` (sobre superfície escura, ex.: painel do login e header da landing) e
 * `compacta` (sidebar) → `logo-garra-negativa.svg`, versão branca.
 */
export function Logo({ variant, className }: LogoProps) {
  const negativa = variant !== "principal";
  const tamanho = variant === "principal" ? "h-24" : variant === "horizontal" ? "h-20 sm:h-24" : "h-16";
  return (
    // eslint-disable-next-line @next/next/no-img-element -- export estático (unoptimized)
    <img
      src={withBasePath(negativa ? "/brand/logo-garra-negativa.svg" : "/brand/logo-garra.svg")}
      alt={LOGO_ALT}
      width={814}
      height={737}
      className={cn("w-auto select-none", tamanho, className)}
    />
  );
}
