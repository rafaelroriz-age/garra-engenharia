"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Menu } from "lucide-react";

import { navItems, portalNavItems } from "./nav-items";
import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { clearAuthToken, isAuthenticated } from "@/lib/api-client";

/** Rotas públicas que não usam o shell autenticado (sidebar/topbar). */
const PUBLIC_ROUTES = ["/", "/login"];

/** Rótulos legíveis dos segmentos de rota, para a trilha da topbar. */
const SEGMENT_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  edificacoes: "Edificações",
  contratos: "Contratos",
  responsaveis: "Responsáveis",
  inspecoes: "Inspeções",
  visitas: "Visitas",
  ocorrencias: "Ocorrências",
  relatorio: "Relatório",
  portal: "Portal do cliente",
  documentos: "Documentos",
  novo: "Novo",
  nova: "Nova",
  editar: "Editar",
};

function trilhaDe(pathname: string): { label: string; isId: boolean }[] {
  return pathname
    .split("/")
    .filter(Boolean)
    .map((segmento) => {
      const conhecido = SEGMENT_LABELS[segmento];
      if (conhecido) return { label: conhecido, isId: false };
      // IDs (numéricos ou UUID) aparecem abreviados, em mono, como nº de folha.
      const curto = segmento.length > 8 ? segmento.slice(0, 8) : segmento;
      return { label: curto, isId: true };
    });
}

function BrandMark() {
  return (
    <Link
      href="/"
      aria-label="Garra Perícias e Avaliações — início"
      className="inline-flex min-h-11 items-center rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar"
    >
      <Logo variant="compacta" />
    </Link>
  );
}

function NavLinks({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const items = pathname.startsWith("/portal") ? portalNavItems : navItems;
  return (
    <nav aria-label="Navegação principal" className="flex flex-col">
      {items.map((item) => {
        // Itens-raiz (ex.: `/portal`) só ficam ativos em match exato — senão ficariam
        // ativos junto com todos os seus filhos (`/portal/documentos`).
        const isRoot = items.some((outro) => outro !== item && outro.href.startsWith(`${item.href}/`));
        const isActive = isRoot
          ? pathname === item.href
          : pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "group relative flex min-h-11 items-center gap-3 border-b border-sidebar-border px-3 text-sm font-medium text-sidebar-foreground/75 transition-colors first:border-t hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-sidebar-ring",
              isActive && "bg-sidebar-accent text-sidebar-accent-foreground"
            )}
          >
            <span
              aria-hidden="true"
              className={cn(
                "absolute inset-y-0 left-0 w-[3px] bg-sidebar-primary transition-opacity",
                isActive ? "opacity-100" : "opacity-0"
              )}
            />
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function Trilha({ pathname }: { pathname: string }) {
  const partes = trilhaDe(pathname);
  return (
    <ol aria-label="Trilha" className="flex min-w-0 items-center gap-2 text-sm">
      <li className="rotulo shrink-0 text-muted-foreground">Garra</li>
      {partes.map((parte, i) => {
        const ultimo = i === partes.length - 1;
        return (
          <li key={`${parte.label}-${i}`} className="flex min-w-0 items-center gap-2">
            <span aria-hidden="true" className="text-foreground/30">
              /
            </span>
            <span
              className={cn(
                "truncate",
                parte.isId ? "dado text-xs" : "font-medium",
                ultimo ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {parte.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function DataDeHoje() {
  // Data só no cliente (evita divergência de hidratação por fuso).
  const [hoje, setHoje] = useState<string | null>(null);
  useEffect(() => {
    setHoje(
      new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date())
    );
  }, []);
  if (!hoje) return null;
  return (
    <span className="hidden items-center gap-2 xl:inline-flex">
      <span className="rotulo">Data</span>
      <span className="dado text-xs text-foreground">{hoje}</span>
    </span>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname.replace(/(.)\/+$/, "$1"));

  // Guarda de rota (RNF-05, BL-06): sem token salvo, redireciona ao login.
  useEffect(() => {
    if (!isPublicRoute && !isAuthenticated()) {
      router.replace("/login");
    }
  }, [isPublicRoute, pathname, router]);

  function handleLogout() {
    clearAuthToken();
    router.push("/login");
  }

  if (isPublicRoute) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-dvh bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-sm focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Pular para o conteúdo principal
      </a>

      {/* Sidebar desktop — "índice de prancha" */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
        <div className="px-5 pb-6 pt-5">
          <BrandMark />
        </div>
        <p className="rotulo px-5 pb-2 text-sidebar-muted">Menu</p>
        <NavLinks pathname={pathname} />
        <div className="mt-auto border-t border-sidebar-border p-3">
          <Button
            variant="ghost"
            onClick={handleLogout}
            className="w-full justify-start gap-3 text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-sidebar-ring focus-visible:ring-offset-sidebar"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sair
          </Button>
        </div>
      </aside>

      {/* Topbar desktop: trilha + data + tema */}
      <header className="sticky top-0 z-20 hidden h-14 items-center justify-between gap-6 border-b border-foreground/15 bg-background/95 px-8 backdrop-blur-[2px] lg:ml-64 lg:flex">
        <Trilha pathname={pathname} />
        <div className="flex shrink-0 items-center gap-5">
          <DataDeHoje />
          <ThemeToggle />
        </div>
      </header>

      {/* Topbar mobile */}
      <header className="sticky top-0 z-20 flex items-center justify-between gap-2 border-b border-sidebar-border bg-sidebar px-3 py-1.5 text-sidebar-foreground lg:hidden">
        <BrandMark />
        <div className="flex items-center gap-1.5">
          <ThemeToggle variant="cycle" tone="inverse" />
          <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-11 w-11 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-sidebar-ring focus-visible:ring-offset-sidebar sm:h-11 sm:w-11"
                aria-label="Abrir menu de navegação"
              >
                <Menu className="h-5 w-5" aria-hidden="true" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="left"
              className="flex w-72 flex-col gap-0 border-sidebar-border bg-sidebar p-0 text-sidebar-foreground"
            >
              <SheetHeader className="px-5 pb-4 pt-5 text-left">
                <SheetTitle className="rotulo text-sidebar-muted">Menu</SheetTitle>
              </SheetHeader>
              <NavLinks pathname={pathname} onNavigate={() => setMobileNavOpen(false)} />
              <div className="mt-auto border-t border-sidebar-border p-3">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setMobileNavOpen(false);
                    handleLogout();
                  }}
                  className="w-full justify-start gap-3 text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                >
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  Sair
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      <main id="main-content" className="px-4 py-6 sm:px-6 lg:ml-64 lg:px-8 lg:py-8">
        {children}
      </main>
    </div>
  );
}
