import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata = {
  title: "Entrar · Garra Engenharia",
};

/**
 * Placeholder da tela de login. O formulário de autenticação (JWT + bcrypt)
 * é implementado em BL-06 (`19-autenticacao-jwt.prompt.md`) — ver RNF-05.
 */
export default function LoginPage() {
  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="space-y-2 text-center">
        <span className="mx-auto grid h-10 w-10 place-items-center rounded-lg bg-brand-accent font-display text-lg font-extrabold text-white">
          G
        </span>
        <CardTitle className="font-display text-xl">Garra Engenharia</CardTitle>
        <Badge variant="outline" className="mx-auto w-fit">
          RNF-05 · BL-06
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-center text-sm text-muted-foreground">
        <p>
          O formulário de login (e-mail, senha, autenticação JWT) será implementado na
          tarefa BL-06 do backlog.
        </p>
        <Link href="/" className="inline-block font-medium text-primary underline-offset-4 hover:underline">
          Voltar ao início
        </Link>
      </CardContent>
    </Card>
  );
}
