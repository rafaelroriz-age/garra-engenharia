"use client";

import { useEffect, useState } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { cn } from "@/lib/utils";

const OPCOES = [
  { value: "light", label: "Tema claro", icon: Sun },
  { value: "dark", label: "Tema escuro", icon: Moon },
  { value: "system", label: "Tema do sistema", icon: Monitor },
] as const;

interface ThemeToggleProps {
  /**
   * `segmented`: três botões (claro/escuro/sistema) lado a lado — topbar desktop.
   * `cycle`: um único botão que alterna entre os três — topbar mobile (alvo 44px).
   */
  variant?: "segmented" | "cycle";
  /** `inverse` para uso sobre superfícies tinta (sidebar/topbar escura). */
  tone?: "default" | "inverse";
  className?: string;
}

/** Alternador de tema claro/escuro/sistema (next-themes, classe `.dark`). */
export function ThemeToggle({ variant = "segmented", tone = "default", className }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  // O tema só é conhecido no cliente: até montar, nenhum botão aparece pressionado
  // (evita divergência de hidratação).
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const atual = mounted ? (theme ?? "system") : null;

  const inverse = tone === "inverse";

  if (variant === "cycle") {
    const indice = Math.max(
      0,
      OPCOES.findIndex((opcao) => opcao.value === atual)
    );
    const opcao = atual ? OPCOES[indice] : OPCOES[2];
    const proxima = OPCOES[(indice + 1) % OPCOES.length];
    const Icon = opcao.icon;
    return (
      <button
        type="button"
        onClick={() => setTheme(proxima.value)}
        aria-label={`${opcao.label} ativo. Alternar para ${proxima.label.toLowerCase()}`}
        className={cn(
          "inline-flex h-11 w-11 items-center justify-center rounded-sm border transition-colors",
          inverse
            ? "border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent"
            : "border-border text-foreground hover:bg-accent",
          className
        )}
      >
        <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
      </button>
    );
  }

  return (
    <div
      role="group"
      aria-label="Tema"
      className={cn(
        "inline-flex items-center rounded-sm border p-0.5",
        inverse ? "border-sidebar-border" : "border-border bg-card",
        className
      )}
    >
      {OPCOES.map((opcao) => {
        const Icon = opcao.icon;
        const ativo = atual === opcao.value;
        return (
          <button
            key={opcao.value}
            type="button"
            onClick={() => setTheme(opcao.value)}
            aria-pressed={ativo}
            aria-label={opcao.label}
            title={opcao.label}
            className={cn(
              "inline-flex h-8 w-8 items-center justify-center rounded-[1px] transition-colors",
              inverse
                ? "text-sidebar-muted hover:text-sidebar-foreground"
                : "text-muted-foreground hover:text-foreground",
              ativo &&
                (inverse
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "bg-foreground text-background hover:text-background")
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}
