import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export type KpiTone = "default" | "critico" | "atencao" | "ok" | "primary";

const TONE_TEXT: Record<KpiTone, string> = {
  default: "text-foreground",
  primary: "text-primary",
  critico: "text-sev-critico",
  atencao: "text-sev-atencao",
  ok: "text-sev-ok",
};

const TONE_BAR: Record<KpiTone, string> = {
  default: "bg-foreground",
  primary: "bg-primary",
  critico: "bg-sev-critico",
  atencao: "bg-sev-atencao",
  ok: "bg-sev-ok",
};

interface KpiTileProps {
  /** Título do indicador — também é o nome acessível do grupo (`role="group"`). */
  label: string;
  value: React.ReactNode;
  /** Complemento ao lado do valor (ex.: "(33%)"). */
  suffix?: React.ReactNode;
  icon?: LucideIcon;
  tone?: KpiTone;
  /** Proporção 0–1 desenhada na régua de escala. Sem valor, a régua mostra só as marcas. */
  ratio?: number;
  /** Destaca o tile (ex.: há ocorrências críticas): filete superior na cor do tom. */
  emphasis?: boolean;
  /** Índice para a revelação escalonada. */
  index?: number;
  className?: string;
}

/**
 * Indicador numérico de prancha: rótulo técnico, valor em mono grande e uma
 * régua de escala (0–100) decorativa. Estrutura: rótulo → cabeçalho → tile
 * (2 níveis), e `role="group"` + `aria-label` para seleção semântica nos e2e.
 */
export function KpiTile({
  label,
  value,
  suffix,
  icon: Icon,
  tone = "default",
  ratio,
  emphasis = false,
  index = 0,
  className,
}: KpiTileProps) {
  const pct = typeof ratio === "number" && Number.isFinite(ratio) ? Math.min(1, Math.max(0, ratio)) : null;
  return (
    <div
      role="group"
      aria-label={label}
      data-slot="kpi-tile"
      className={cn(
        "relative flex flex-col rounded-lg border bg-card px-4 pb-3 pt-3.5 animate-reveal",
        emphasis && "border-t-[3px]",
        emphasis && tone === "critico" && "border-t-sev-critico",
        emphasis && tone === "atencao" && "border-t-sev-atencao",
        emphasis && tone === "ok" && "border-t-sev-ok",
        emphasis && (tone === "default" || tone === "primary") && "border-t-primary",
        className
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex min-h-8 items-start gap-1.5">
        {Icon ? <Icon className={cn("mt-px h-3.5 w-3.5 shrink-0", TONE_TEXT[tone])} aria-hidden="true" /> : null}
        <span className="rotulo">{label}</span>
      </div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span className="dado text-[2rem] font-semibold leading-none tracking-tight text-foreground">{value}</span>
        {suffix ? <span className="dado text-sm text-muted-foreground">{suffix}</span> : null}
      </div>
      {/* Régua de escala: 10 divisões, preenchimento proporcional. */}
      <div aria-hidden="true" className="mt-3">
        <div className="relative h-1.5 w-full bg-foreground/[0.06]">
          {pct !== null ? (
            <div
              className={cn("absolute inset-y-0 left-0 origin-left animate-regua-fill", TONE_BAR[tone])}
              style={{ width: `${pct * 100}%`, animationDelay: `${index * 50 + 80}ms` }}
            />
          ) : null}
        </div>
        <div className="flex h-1.5 justify-between">
          {Array.from({ length: 11 }).map((_, i) => (
            <span key={i} className={cn("w-px bg-foreground/30", i % 5 === 0 ? "h-1.5" : "h-1")} />
          ))}
        </div>
      </div>
    </div>
  );
}
