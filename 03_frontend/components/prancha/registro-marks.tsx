import { cn } from "@/lib/utils";

interface RegistroMarksProps {
  /** Tamanho de cada marca em px. */
  size?: number;
  /** Afastamento da borda do contêiner em px (negativo = para fora). */
  inset?: number;
  className?: string;
}

/**
 * Marcas de registro (cantos em "L") de prancha técnica. Puramente decorativas:
 * o contêiner pai precisa de `position: relative`.
 */
export function RegistroMarks({ size = 12, inset = 0, className }: RegistroMarksProps) {
  const base = "pointer-events-none absolute border-current";
  const style = { width: size, height: size };
  return (
    <span aria-hidden="true" className={cn("text-foreground/40", className)}>
      <span className={cn(base, "border-l border-t")} style={{ ...style, left: inset, top: inset }} />
      <span className={cn(base, "border-r border-t")} style={{ ...style, right: inset, top: inset }} />
      <span className={cn(base, "border-b border-l")} style={{ ...style, left: inset, bottom: inset }} />
      <span className={cn(base, "border-b border-r")} style={{ ...style, right: inset, bottom: inset }} />
    </span>
  );
}
