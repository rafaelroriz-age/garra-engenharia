import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Botão "Prancha Técnica": cantos retos (raio 2px), sem sombra, filete 1px.
 * Alvo de toque >= 44px no mobile (h-11), 40px a partir de `sm`.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md border border-transparent text-sm font-semibold tracking-[0.01em] transition-[color,background-color,border-color,transform] duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background active:translate-y-px disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Ação primária: cianotipia.
        default:
          "bg-primary text-primary-foreground hover:bg-primary/90",
        // Único destaque quente da tela.
        sinal:
          "bg-sinal text-sinal-foreground hover:bg-sinal/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border-input bg-card text-foreground hover:border-foreground/60 hover:bg-accent",
        secondary:
          "border-border bg-secondary text-secondary-foreground hover:bg-secondary/70",
        ghost: "text-foreground hover:bg-accent hover:text-accent-foreground",
        link: "h-auto px-0 text-primary underline decoration-primary/40 underline-offset-4 hover:decoration-primary",
      },
      size: {
        default: "h-11 px-4 sm:h-10",
        sm: "h-9 px-3 text-xs sm:h-8",
        lg: "h-12 px-6 text-[0.9375rem]",
        icon: "h-11 w-11 sm:h-10 sm:w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
