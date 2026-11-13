import { cn } from "@/lib/utils";

interface SectionTitleProps {
  /** Número da seção ("01", "02"…). Decorativo: não entra no nome do heading. */
  number?: string;
  children: React.ReactNode;
  as?: "h2" | "h3";
  /** Ações alinhadas à direita (botões, filtros). */
  actions?: React.ReactNode;
  className?: string;
  id?: string;
}

/**
 * Título de seção numerado, à maneira de uma prancha: "01 —  Título",
 * apoiado num filete. O número fica fora do heading (aria-hidden) para que o
 * nome acessível do título permaneça exatamente o texto informado.
 */
export function SectionTitle({ number, children, as: Heading = "h2", actions, className, id }: SectionTitleProps) {
  return (
    <div className={cn("flex flex-wrap items-end justify-between gap-3 border-b border-foreground/20 pb-2", className)}>
      <div className="flex min-w-0 items-baseline gap-3">
        {number ? (
          <span aria-hidden="true" className="dado shrink-0 text-xs font-medium text-sinal-ink">
            {number} —
          </span>
        ) : null}
        <Heading id={id} className="display-wide truncate text-base font-semibold tracking-tight text-foreground">
          {children}
        </Heading>
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
