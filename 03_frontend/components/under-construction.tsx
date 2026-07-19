import type { LucideIcon } from "lucide-react";
import { Construction } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface UnderConstructionProps {
  requirement: string;
  children: React.ReactNode;
  icon?: LucideIcon;
}

/**
 * Placeholder padrão para telas ainda não implementadas (BL-03).
 * Formulários e integração com a API entram em tarefas subsequentes do backlog.
 */
export function UnderConstruction({ requirement, children, icon: Icon = Construction }: UnderConstructionProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          Em construção
        </CardTitle>
        <Badge variant="outline">{requirement}</Badge>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">{children}</CardContent>
    </Card>
  );
}
