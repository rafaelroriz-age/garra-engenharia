import { cn } from "@/lib/utils";

import { GarraMark } from "./garra-mark";

export type LogoVariant = "principal" | "horizontal" | "compacta";

const LOGO_ALT = "Garra Perícias e Avaliações";

interface LogoProps {
  variant: LogoVariant;
  className?: string;
}

/**
 * Marca oficial "Garra Perícias e Avaliações" (BL-41/BL-19).
 *
 * Vetorizada em SVG (`GarraMark`, `fill="currentColor"`) + texto real
 * (`font-display`) no lugar dos 4 JPEGs originais com fundo/cores embutidas:
 * escala sem perda em qualquer tamanho e herda a cor certa de cada
 * superfície via classe de texto — navy (`text-primary`) sobre fundo claro,
 * branco (`text-primary-foreground`) sobre o navy da marca (`bg-primary`).
 *
 * `principal` (fundo claro, ex.: login) → ícone empilhado sobre o nome.
 * `horizontal` (fundo navy, ex.: header da landing) → ícone + nome em linha.
 * `compacta` (fundo navy, ex.: sidebar/topbar) → ícone + nome em 2 linhas.
 */
export function Logo({ variant, className }: LogoProps) {
  if (variant === "principal") {
    return (
      <span
        role="img"
        aria-label={LOGO_ALT}
        className={cn("inline-flex flex-col items-center gap-2 text-primary", className)}
      >
        <GarraMark className="h-14 w-14" />
        <span className="text-center font-display text-base font-extrabold leading-tight tracking-tight sm:text-lg">
          Garra Perícias
          <br />e Avaliações
        </span>
      </span>
    );
  }

  if (variant === "horizontal") {
    return (
      <span
        role="img"
        aria-label={LOGO_ALT}
        className={cn("inline-flex items-center gap-3 text-primary-foreground", className)}
      >
        <GarraMark className="h-10 w-10 sm:h-12 sm:w-12" />
        <span className="whitespace-nowrap font-display text-lg font-extrabold leading-tight tracking-tight sm:text-xl">
          Garra Perícias e Avaliações
        </span>
      </span>
    );
  }

  return (
    <span
      role="img"
      aria-label={LOGO_ALT}
      className={cn("inline-flex items-center gap-2 text-primary-foreground", className)}
    >
      <GarraMark className="h-8 w-8" />
      <span className="font-display text-xs font-bold leading-[1.15] tracking-tight">
        Garra Perícias
        <br />e Avaliações
      </span>
    </span>
  );
}
