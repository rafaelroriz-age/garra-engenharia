import Link from "next/link";
import { Building2, ClipboardList } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Placeholder do Dashboard (RF-07, BL-16). Os indicadores por edificação e
 * sistema predial virão da API — os blocos abaixo apenas reservam o layout.
 */
export default function DashboardPage() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Indicadores de saúde por edificação e sistema predial (RF-07). Os dados serão carregados da API na tarefa BL-16."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} aria-hidden="true">
            <CardHeader className="space-y-2 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-7 w-16" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Últimas vistorias</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Saúde por sistema predial</CardTitle>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-40 w-full" />
          </CardContent>
        </Card>
      </div>

      <p className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Building2 className="h-4 w-4" aria-hidden="true" /> Ver{" "}
          <Link href="/edificacoes" className="font-medium text-primary underline-offset-4 hover:underline">
            edificações
          </Link>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <ClipboardList className="h-4 w-4" aria-hidden="true" /> Ver exemplo de{" "}
          <Link
            href="/inspecoes/1/visitas"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            visitas de inspeção
          </Link>
        </span>
      </p>
    </div>
  );
}
