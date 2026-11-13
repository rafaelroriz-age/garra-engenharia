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
 * (`font-display`, Archivo expandida). Identidade "Prancha Técnica":
 *
 * `principal` (sobre papel, ex.: login) → símbolo em cianotipia empilhado sobre o nome em tinta.
 * `horizontal` (sobre superfície tinta, ex.: header da landing) → símbolo em sinal + nome em linha.
 * `compacta` (sobre superfície tinta, ex.: sidebar/topbar) → símbolo em sinal + nome em 2 linhas.
 */
export function Logo({ variant, className }: LogoProps) {
  if (variant === "principal") {
    return (
      <span
        role="img"
        aria-label={LOGO_ALT}
        className={cn("inline-flex flex-col items-center gap-2 text-foreground", className)}
      >
        <GarraMark className="h-14 w-14 text-primary" />
        <span className="display-wide text-center text-base font-bold uppercase leading-tight tracking-[0.06em] sm:text-lg">
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
        className={cn("inline-flex items-center gap-3 text-sidebar-foreground", className)}
      >
        <GarraMark className="h-10 w-10 text-sinal sm:h-11 sm:w-11" />
        <span className="display-wide whitespace-nowrap text-base font-bold uppercase leading-tight tracking-[0.06em] sm:text-lg">
          Garra Perícias e Avaliações
        </span>
      </span>
    );
  }

  return (
    <span
      role="img"
      aria-label={LOGO_ALT}
      className={cn("inline-flex items-center gap-2.5 text-sidebar-foreground", className)}
    >
      <GarraMark className="h-8 w-8 text-sinal" />
      <span className="display-wide text-[0.6875rem] font-bold uppercase leading-[1.2] tracking-[0.08em]">
        Garra Perícias
        <br />e Avaliações
      </span>
    </span>
  );
}
