import { cn } from "@/lib/utils";

/**
 * Símbolo vetorial oficial "Garra Perícias e Avaliações": skyline estilizado
 * (torres + telhados), mesmo traço já validado em `public/icon.svg` (BL-41),
 * reaproveitado como marca vetorial em `<Logo />` (BL-19).
 *
 * `fill="currentColor"` permite recolorir a marca via classe de texto
 * (`text-primary`, `text-primary-foreground`) conforme o fundo em que é
 * aplicada — sem fundo embutido, sem perda de nitidez em nenhum tamanho.
 */
export function GarraMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 512 512" role="img" aria-hidden="true" className={cn("shrink-0", className)}>
      <path d="M88 344 L176 240 L232 292 L256 176 L280 292 L336 240 L424 344 Z" fill="currentColor" />
    </svg>
  );
}
