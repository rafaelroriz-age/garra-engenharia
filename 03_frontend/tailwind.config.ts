import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        // Acento quente único ("sinal"): ação de destaque e alertas.
        sinal: {
          DEFAULT: "hsl(var(--sinal))",
          foreground: "hsl(var(--sinal-foreground))",
          ink: "hsl(var(--sinal-ink))",
        },
        // Severidade de patologia — sempre com texto/ícone redundante.
        sev: {
          critico: "hsl(var(--sev-critico))",
          "critico-foreground": "hsl(var(--sev-critico-foreground))",
          atencao: "hsl(var(--sev-atencao))",
          "atencao-foreground": "hsl(var(--sev-atencao-foreground))",
          ok: "hsl(var(--sev-ok))",
          "ok-foreground": "hsl(var(--sev-ok-foreground))",
        },
        "grid-line": "hsl(var(--grid-line))",
        chart: {
          "1": "hsl(var(--chart-1))",
          "2": "hsl(var(--chart-2))",
          "3": "hsl(var(--chart-3))",
          "4": "hsl(var(--chart-4))",
          "5": "hsl(var(--chart-5))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
          muted: "hsl(var(--sidebar-muted))",
        },
        // Aliases de marca (DEC-06), mapeados para a paleta "Prancha Técnica".
        brand: {
          navy: "hsl(var(--brand-navy))",
          "navy-deep": "hsl(var(--brand-navy-deep))",
          accent: "hsl(var(--brand-accent))",
        },
      },
      // Cantos de prancha: retos ou raio mínimo. `xl`/`2xl` também são
      // reduzidos para que telas legadas herdem a linguagem sem edição.
      borderRadius: {
        "2xl": "calc(var(--radius) + 4px)",
        xl: "calc(var(--radius) + 2px)",
        lg: "var(--radius)",
        md: "var(--radius)",
        sm: "calc(var(--radius) / 2)",
      },
      letterSpacing: {
        rotulo: "0.14em",
      },
      keyframes: {
        reveal: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "regua-fill": {
          from: { transform: "scaleX(0)" },
          to: { transform: "scaleX(1)" },
        },
      },
      animation: {
        reveal: "reveal 220ms cubic-bezier(0.2, 0.7, 0.2, 1) both",
        "regua-fill": "regua-fill 420ms cubic-bezier(0.2, 0.7, 0.2, 1) both",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
