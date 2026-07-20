import * as React from "react"
import { ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>

/**
 * Wrapper em torno do `<select>` nativo (em vez de um Combobox Radix) —
 * mantém navegação por teclado e leitores de tela nativos sem dependências
 * adicionais, cumprindo o requisito de acessibilidade do modo Frontend.
 */
const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          ref={ref}
          className={cn(
            "flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-1 pr-8 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 aria-[invalid=true]:border-destructive aria-[invalid=true]:ring-destructive",
            className
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
      </div>
    )
  }
)
Select.displayName = "Select"

export { Select }
