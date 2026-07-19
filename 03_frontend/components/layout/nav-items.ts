import type { LucideIcon } from "lucide-react";
import { Building2, FileText, LayoutDashboard } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

/**
 * Itens de navegação principal do app (Sidebar desktop + menu mobile).
 * As rotas de `inspecoes/[id]/*` não aparecem aqui: são acessadas a partir
 * do contexto de uma edificação/contrato específico, não pela navegação global.
 */
export const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/edificacoes", label: "Edificações", icon: Building2 },
  { href: "/contratos", label: "Contratos", icon: FileText },
];
