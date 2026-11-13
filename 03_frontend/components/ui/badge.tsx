import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Etiqueta técnica: mono caixa-alta, raio mínimo.
 * Severidade (`critico`/`atencao`/`ok`) usa preenchimento calibrado e deve
 * sempre vir com texto legível — nunca só cor. `carimbo` é o selo de status
 * (RASCUNHO, EMITIDO…); para o carimbo rotacionado use `<Stamp />`.
 */
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-sm border px-2 py-0.5 font-mono text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.06em] transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground",
        secondary:
          "border-border bg-secondary text-secondary-foreground",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground",
        outline: "border-foreground/25 text-foreground",
        sinal: "border-transparent bg-sinal text-sinal-foreground",
        critico: "border-transparent bg-sev-critico text-sev-critico-foreground",
        atencao: "border-transparent bg-sev-atencao text-sev-atencao-foreground",
        ok: "border-transparent bg-sev-ok text-sev-ok-foreground",
        carimbo:
          "border-current bg-transparent font-semibold tracking-[0.14em] text-primary shadow-[inset_0_0_0_2px_hsl(var(--card)),inset_0_0_0_3px_currentColor]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
