interface PageHeaderProps {
  title: string;
  description?: string;
}

/** Cabeçalho padrão das telas do app (título + descrição curta). */
export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-6 space-y-1">
      <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
        {title}
      </h1>
      {description ? (
        <p className="max-w-2xl text-sm text-muted-foreground">{description}</p>
      ) : null}
    </div>
  );
}
