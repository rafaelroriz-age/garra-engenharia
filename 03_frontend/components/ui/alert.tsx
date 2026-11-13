import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/** Aviso de prancha: filete com barra lateral de 3px na cor semântica. */
const alertVariants = cva(
  "relative w-full rounded-md border border-l-[3px] px-4 py-3 text-sm [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-[0.85rem] [&>svg]:h-4 [&>svg]:w-4 [&>svg+div]:translate-y-[-3px] [&:has(svg)]:pl-11",
  {
    variants: {
      variant: {
        default: "border-l-primary bg-card text-foreground [&>svg]:text-primary",
        destructive:
          "border-destructive/40 border-l-destructive bg-destructive/[0.07] text-foreground [&>svg]:text-destructive",
        success:
          "border-sev-ok/40 border-l-sev-ok bg-sev-ok/[0.08] text-foreground [&>svg]:text-sev-ok",
        warning:
          "border-sev-atencao/50 border-l-sev-atencao bg-sev-atencao/[0.10] text-foreground [&>svg]:text-sev-atencao",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
))
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h5 ref={ref} className={cn("mb-1 font-semibold leading-tight", className)} {...props} />
  )
)
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("text-sm text-foreground/85 [&_p]:leading-relaxed", className)} {...props} />
  )
)
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription }
