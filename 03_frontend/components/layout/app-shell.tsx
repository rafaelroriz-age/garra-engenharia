"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Menu } from "lucide-react";

import { navItems, portalNavItems } from "./nav-items";
import { Logo } from "@/components/brand/logo";
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

function BrandMark() {
  return (
    <Link href="/" aria-label="Garra Perícias e Avaliações — início">
      <Logo variant="compacta" />
    </Link>
  );
}

function NavLinks({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const items = pathname.startsWith("/portal") ? portalNavItems : navItems;
  return (
    <nav aria-label="Navegação principal" className="flex flex-col gap-1">
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
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-white/80 transition-colors hover:bg-white/10 hover:text-white",
              isActive && "bg-white/10 text-white"
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

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
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Pular para o conteúdo principal
      </a>

      {/* Sidebar desktop */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col gap-6 bg-primary px-4 py-6 lg:flex">
        <BrandMark />
        <NavLinks pathname={pathname} />
        <Button
          variant="ghost"
          onClick={handleLogout}
          className="mt-auto justify-start gap-3 text-white/80 hover:bg-white/10 hover:text-white"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
          Sair
        </Button>
      </aside>

      {/* Topbar mobile */}
      <header className="flex items-center justify-between border-b bg-primary px-4 py-3 lg:hidden">
        <BrandMark />
        <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10 hover:text-white"
              aria-label="Abrir menu de navegação"
            >
              <Menu className="h-5 w-5" aria-hidden="true" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 bg-primary p-4">
            <SheetHeader>
              <SheetTitle className="text-white">Menu</SheetTitle>
            </SheetHeader>
            <div className="mt-6">
              <NavLinks pathname={pathname} onNavigate={() => setMobileNavOpen(false)} />
            </div>
            <Button
              variant="ghost"
              onClick={() => {
                setMobileNavOpen(false);
                handleLogout();
              }}
              className="mt-6 w-full justify-start gap-3"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              Sair
            </Button>
          </SheetContent>
        </Sheet>
      </header>

      <main id="main-content" className="px-4 py-6 sm:px-6 lg:ml-64 lg:px-8 lg:py-8">
        {children}
      </main>
    </div>
  );
}
