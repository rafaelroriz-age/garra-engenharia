import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  ArrowUpRight,
  Building2,
  ClipboardList,
  FileDown,
  FileText,
  LayoutDashboard,
  LogIn,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Logo } from "@/components/brand/logo";
import { RegistroMarks } from "@/components/prancha/registro-marks";

interface HubCard {
  href: string;
  label: string;
  title: string;
  description: string;
  icon: LucideIcon;
}

const hubCards: HubCard[] = [
  {
    href: "/dashboard",
    label: "01 · VISÃO GERAL",
    title: "Dashboard Principal",
    description: "Indicadores, saúde por sistema predial e últimas vistorias.",
    icon: LayoutDashboard,
  },
  {
    href: "/edificacoes",
    label: "02 · CADASTRO",
    title: "Edificações",
    description: "Todas as obras cadastradas, com badge de saúde e última inspeção.",
    icon: Building2,
  },
  {
    href: "/contratos",
    label: "03 · CADASTRO",
    title: "Contratos",
    description: "Empresas executoras, NBRs aplicáveis e vínculo com edificações.",
    icon: FileText,
  },
  {
    href: "/inspecoes/1/visitas",
    label: "04 · CAMPO",
    title: "Visitas de Inspeção",
    description: "Registro de visitas do RFO em campo: equipe, serviços e medições.",
    icon: ClipboardList,
  },
  {
    href: "/inspecoes/1/ocorrencias",
    label: "05 · REGISTRO",
    title: "Ocorrências",
    description: "Classificação por sistema predial, CMM e matriz GUT.",
    icon: AlertTriangle,
  },
  {
    href: "/inspecoes/1/relatorio",
    label: "06 · ENTREGA",
    title: "Relatório",
    description: "Geração e download do relatório em PDF e DOCX editável.",
    icon: FileDown,
  },
];

export default function HomePage() {
  return (
    <div className="min-h-dvh bg-background">
      <a
        href="#hub-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-sm focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Pular para o conteúdo principal
      </a>

      <header className="prancha-grid-tinta relative text-sidebar-foreground">
        <RegistroMarks inset={12} size={14} className="text-sidebar-muted" />
        <div className="mx-auto max-w-6xl px-6 pb-14 pt-8 sm:pb-20">
          <div className="mb-14 flex items-center justify-between gap-3 sm:mb-20">
            <Logo variant="horizontal" />
            <Link
              href="/login"
              className="inline-flex min-h-11 items-center gap-2 rounded-sm border border-sidebar-foreground/30 px-4 text-sm font-semibold text-sidebar-foreground transition-colors hover:border-sinal hover:bg-sinal hover:text-sinal-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar"
            >
              <LogIn className="h-4 w-4" aria-hidden="true" />
              Entrar
            </Link>
          </div>

          <Badge className="mb-5 border-sidebar-foreground/30 text-sidebar-foreground" variant="outline">
            Scaffold Next.js 14 PWA · BL-03
          </Badge>
          <h1 className="display-wide max-w-4xl text-4xl font-bold uppercase leading-[1.02] tracking-tight sm:text-6xl">
            Sistema de Automação de Relatórios Prediais
          </h1>
          <div aria-hidden="true" className="mt-6 h-[3px] w-16 bg-sinal" />
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-sidebar-foreground/80">
            Navegue pelas telas do sistema. Cada card abaixo abre uma rota do
            App Router — do dashboard ao relatório de inspeção.
          </p>
        </div>
      </header>

      <main id="hub-content" className="mx-auto max-w-6xl px-6 py-14">
        <div className="mb-6 flex items-baseline gap-3 border-b border-foreground/25 pb-2">
          <span aria-hidden="true" className="dado text-xs font-medium text-sinal-ink">
            00 —
          </span>
          <h2 className="display-wide text-xl font-bold tracking-tight text-foreground">Rotas do sistema</h2>
        </div>
        <ul className="grid grid-cols-1 border-l border-t border-foreground/20 sm:grid-cols-2 lg:grid-cols-3">
          {hubCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <li
                key={card.href}
                className="border-b border-r border-foreground/20 animate-reveal"
                style={{ animationDelay: `${index * 40}ms` }}
              >
                <Link
                  href={card.href}
                  className="group relative flex h-full flex-col gap-3 bg-card p-5 transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                >
                  <span
                    aria-hidden="true"
                    className="absolute inset-x-0 top-0 h-[3px] origin-left scale-x-0 bg-sinal transition-transform duration-200 group-hover:scale-x-100 group-focus-visible:scale-x-100"
                  />
                  <div className="flex items-start justify-between gap-3">
                    <span className="dado text-[0.6875rem] font-medium tracking-[0.08em] text-sinal-ink">
                      {card.label}
                    </span>
                    <Icon className="h-5 w-5 text-primary" aria-hidden="true" />
                  </div>
                  <span className="display-wide text-lg font-semibold leading-tight text-foreground">
                    {card.title}
                  </span>
                  <span className="text-sm leading-relaxed text-muted-foreground">{card.description}</span>
                  <ArrowUpRight
                    className="mt-auto h-4 w-4 self-end text-muted-foreground transition-colors group-hover:text-foreground"
                    aria-hidden="true"
                  />
                </Link>
              </li>
            );
          })}
        </ul>
      </main>
    </div>
  );
}
