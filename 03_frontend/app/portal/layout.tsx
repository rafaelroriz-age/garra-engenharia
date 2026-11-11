"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { Skeleton } from "@/components/ui/skeleton";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";

/** Home interna para quem não é cliente (perfis auditor/auxiliar). */
const HOME_INTERNA = "/dashboard";

/**
 * Guarda do Portal do Cliente (BL-32, RN-14).
 *
 * Só o perfil `cliente` vê o conteúdo de `/portal/*`. Os demais perfis são
 * levados à home interna sem que nenhum dado do portal seja renderizado.
 * Sem sessão, o `AppShell` já redireciona ao login (mesma regra das demais rotas).
 *
 * Isto é usabilidade: a autorização real continua no backend (`/portal/*`, 403).
 */
export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { usuario, isLoading } = useUsuarioAtual();
  const isCliente = usuario?.role === "cliente";

  useEffect(() => {
    if (isLoading) return;
    if (!usuario) {
      // Sem perfil confirmado (sessão inválida ou falha em /auth/me): volta ao login.
      router.replace("/login");
      return;
    }
    if (!isCliente) {
      router.replace(HOME_INTERNA);
    }
  }, [isLoading, usuario, isCliente, router]);

  if (isLoading || !isCliente) {
    // Enquanto o perfil carrega ou não é `cliente`, nada do portal é exibido.
    return (
      <div aria-busy="true" aria-label="Verificando acesso ao portal" role="status">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }

  return <>{children}</>;
}
