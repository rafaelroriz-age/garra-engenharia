import { cn } from "@/lib/utils";

export type StampTone = "primary" | "sinal" | "critico" | "atencao" | "ok" | "muted";

const TONES: Record<StampTone, string> = {
  primary: "text-primary",
  sinal: "text-sinal-ink",
  critico: "text-sev-critico",
  atencao: "text-sev-atencao",
  ok: "text-sev-ok",
  muted: "text-muted-foreground",
};

interface StampProps {
  children: React.ReactNode;
  tone?: StampTone;
  /** Inclina o carimbo como se aplicado à mão (desligar em listas densas). */
  tilted?: boolean;
  size?: "sm" | "md";
  className?: string;
}

/**
 * Carimbo de status (RASCUNHO, EMITIDO, APROVADO, CRÍTICO): borda dupla,
 * mono caixa-alta, leve rotação. O texto é real e legível — a cor nunca é
 * o único portador da informação.
 */
export function Stamp({ children, tone = "primary", tilted = true, size = "md", className }: StampProps) {
  return (
    <span
      className={cn(
        "inline-flex select-none items-center justify-center whitespace-nowrap rounded-[2px] border-2 border-current p-[2px] font-mono font-semibold uppercase leading-none",
        size === "md" ? "text-xs tracking-[0.18em]" : "text-[0.625rem] tracking-[0.16em]",
        tilted && "-rotate-[4deg]",
        TONES[tone],
        className
      )}
    >
      <span
        className={cn(
          "block rounded-[1px] border border-current",
          size === "md" ? "px-2.5 py-1.5" : "px-1.5 py-1"
        )}
      >
        {children}
      </span>
    </span>
  );
}
