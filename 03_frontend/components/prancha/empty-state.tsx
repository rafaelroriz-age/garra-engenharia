import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

import { RegistroMarks } from "./registro-marks";

interface EmptyStateProps {
  /** Ícone opcional; sem ele, usa a ilustração em linha de prancha vazia. */
  icon?: LucideIcon;
  title?: React.ReactNode;
  children?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

/** Ilustração em linha: folha com cota e um ponto de registro. Decorativa. */
function PranchaVazia({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 96 64" aria-hidden="true" focusable="false" className={className} fill="none">
      <rect x="10" y="8" width="60" height="44" stroke="currentColor" strokeWidth="1.25" />
      <path d="M10 44h60" stroke="currentColor" strokeWidth="1" strokeDasharray="2 2" />
      <path d="M52 44v8M52 48h18" stroke="currentColor" strokeWidth="1" />
      <path d="M18 18h28M18 24h20M18 30h24" stroke="currentColor" strokeWidth="1" opacity=".55" />
      <path d="M10 58h60M10 56v4M70 56v4" stroke="currentColor" strokeWidth="1" />
      <circle cx="82" cy="20" r="6" className="stroke-sinal" strokeWidth="1.25" />
      <path d="M82 10v20M72 20h20" className="stroke-sinal" strokeWidth="1" />
    </svg>
  );
}

/**
 * Estado vazio de prancha: malha milimetrada, marcas de registro e o texto
 * existente da tela. Nada de enchimento — o conteúdo vem de quem chama.
 */
export function EmptyState({ icon: Icon, title, children, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "prancha-grid relative flex flex-col items-center gap-3 rounded-lg border border-dashed border-foreground/25 px-6 py-10 text-center",
        className
      )}
    >
      <RegistroMarks inset={6} size={10} />
      {Icon ? (
        <Icon className="h-7 w-7 text-muted-foreground" aria-hidden="true" />
      ) : (
        <PranchaVazia className="h-14 w-20 text-muted-foreground" />
      )}
      {title ? <p className="display-wide text-sm font-semibold text-foreground">{title}</p> : null}
      {children ? <div className="max-w-md text-sm text-muted-foreground">{children}</div> : null}
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}
