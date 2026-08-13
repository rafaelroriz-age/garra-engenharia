import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  Building2,
  ClipboardList,
  FileDown,
  FileText,
  LayoutDashboard,
  LogIn,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Logo } from "@/components/brand/logo";

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
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Pular para o conteúdo principal
      </a>

      <header className="bg-primary text-primary-foreground">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="mb-8 flex items-center justify-between gap-3">
            <Logo variant="horizontal" className="h-10 sm:h-12" priority />
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 rounded-md border border-white/20 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-white/10"
            >
              <LogIn className="h-4 w-4" aria-hidden="true" />
              Entrar
            </Link>
          </div>

          <Badge className="mb-3 border-white/15 bg-white/10 text-white" variant="outline">
            Scaffold Next.js 14 PWA · BL-03
          </Badge>
          <h1 className="max-w-3xl font-display text-4xl font-extrabold leading-tight sm:text-5xl">
            Sistema de Automação de Relatórios Prediais
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-primary-foreground/80">
            Navegue pelas telas do sistema. Cada card abaixo abre uma rota do
            App Router — do dashboard ao relatório de inspeção.
          </p>
        </div>
      </header>

      <main id="hub-content" className="mx-auto max-w-6xl px-6 py-14">
        <h2 className="mb-8 font-display text-2xl font-bold text-foreground">
          Rotas do sistema
        </h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {hubCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link key={card.href} href={card.href} className="group focus:outline-none">
                <Card className="h-full transition-all group-hover:-translate-y-1 group-hover:shadow-lg group-focus-visible:ring-2 group-focus-visible:ring-ring">
                  <div className="flex h-32 items-center justify-center rounded-t-xl bg-gradient-to-br from-primary to-brand-navy-deep">
                    <Icon className="h-12 w-12 text-brand-accent" aria-hidden="true" />
                  </div>
                  <CardHeader className="pb-2">
                    <span className="text-xs font-semibold text-brand-accent">{card.label}</span>
                    <CardTitle className="font-display text-lg group-hover:text-brand-accent">
                      {card.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0 text-sm text-muted-foreground">
                    {card.description}
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
