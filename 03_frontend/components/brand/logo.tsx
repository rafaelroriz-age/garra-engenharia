import Image, { type StaticImageData } from "next/image";

import { cn } from "@/lib/utils";

import logoCompacta from "@/public/brand/logos/logo-compacta-negativa-fundo-ardosia.jpg";
import logoHorizontal from "@/public/brand/logos/logo-horizontal-negativa-fundo-preto.jpg";
import logoPrincipal from "@/public/brand/logos/logo-principal-fundo-claro.jpg";

export type LogoVariant = "principal" | "horizontal" | "compacta";

const LOGO_SOURCES: Record<LogoVariant, StaticImageData> = {
  principal: logoPrincipal,
  horizontal: logoHorizontal,
  compacta: logoCompacta,
};

const LOGO_ALT = "Garra Perícias e Avaliações";

interface LogoProps {
  variant: LogoVariant;
  className?: string;
  priority?: boolean;
}

/**
 * Marca oficial "Garra Perícias e Avaliações" (BL-41).
 *
 * Os 3 arquivos oficiais são JPEGs com fundo próprio (sem transparência), por
 * isso cada variante é sempre renderizada como um "selo" (`rounded-md
 * overflow-hidden`) — nunca solta sobre outra cor de fundo, evitando um
 * recorte retangular acidental. Escolha a variante pelo fundo da superfície:
 * `principal` (clara), `horizontal` (escura, com espaço horizontal) ou
 * `compacta` (escura, espaço reduzido — navegação/shell).
 */
export function Logo({ variant, className, priority }: LogoProps) {
  return (
    <span className={cn("inline-block shrink-0 overflow-hidden rounded-md shadow-sm", className)}>
      <Image
        src={LOGO_SOURCES[variant]}
        alt={LOGO_ALT}
        priority={priority}
        className="block h-full w-auto"
      />
    </span>
  );
}
