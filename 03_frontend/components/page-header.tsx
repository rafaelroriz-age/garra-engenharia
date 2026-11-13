import { cn } from "@/lib/utils";

export interface PageHeaderMeta {
  label: string;
  value: React.ReactNode;
}

interface PageHeaderProps {
  title: string;
  description?: string;
  /** Rótulo acima do título (trilha/seção), em caixa-alta espaçada. */
  eyebrow?: string;
  /**
   * Bloco "carimbo de prancha" com metadados (ex.: Nº, Revisão, Data),
   * exibido à direita no desktop e abaixo no mobile.
   */
  meta?: PageHeaderMeta[];
  className?: string;
}

/**
 * Cabeçalho das telas do app: régua curta em sinal + eyebrow opcional,
 * título em Archivo e descrição. Mantém o `<h1>` com o texto exato do título.
 */
export function PageHeader({ title, description, eyebrow, meta, className }: PageHeaderProps) {
  return (
    <div className={cn("mb-6 flex flex-wrap items-end justify-between gap-x-8 gap-y-4", className)}>
      <div className="min-w-0 max-w-3xl space-y-2">
        <div className="flex items-center gap-2" aria-hidden={eyebrow ? undefined : true}>
          <span className="h-[3px] w-6 bg-sinal" aria-hidden="true" />
          {eyebrow ? <span className="rotulo">{eyebrow}</span> : null}
        </div>
        <h1 className="display-wide text-[1.625rem] font-bold leading-[1.1] tracking-tight text-foreground sm:text-[1.875rem]">
          {title}
        </h1>
        {description ? (
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {meta && meta.length > 0 ? (
        <dl className="grid shrink-0 grid-flow-col border border-foreground/25 bg-card text-left">
          {meta.map((item, i) => (
            <div key={item.label} className={cn("px-3 py-2", i > 0 && "border-l border-foreground/25")}>
              <dt className="rotulo text-[0.625rem]">{item.label}</dt>
              <dd className="dado mt-0.5 text-sm font-medium text-foreground">{item.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}
