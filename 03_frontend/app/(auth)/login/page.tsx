"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { api, ApiError, setAuthToken } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Logo } from "@/components/brand/logo";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { RegistroMarks } from "@/components/prancha/registro-marks";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

/** Tela de login (e-mail + senha, JWT — BL-06, RNF-05). Consome `POST /auth/login`. */
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const { access_token } = await api.post<TokenResponse>("/auth/login", { email, senha });
      setAuthToken(access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Erro inesperado ao entrar."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card className="relative w-full max-w-sm border-foreground/25 animate-reveal">
      <RegistroMarks inset={-7} size={10} className="text-foreground/50" />
      <div aria-hidden="true" className="h-[3px] w-full bg-primary" />
      <CardHeader className="space-y-3 pb-5">
        <Logo variant="principal" className="mx-auto mb-2 lg:hidden" />
        <div className="flex items-center justify-between gap-3">
          <span className="rotulo">Folha 00 · Acesso</span>
          <Badge variant="outline" className="w-fit">
            RNF-05 · BL-06
          </Badge>
        </div>
        <CardTitle className="display-wide text-2xl font-bold">Acessar sua conta</CardTitle>
        <CardDescription>Informe suas credenciais para continuar.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-5" onSubmit={handleSubmit} noValidate>
          <ApiErrorAlert error={error} />
          <div className="space-y-2">
            <Label htmlFor="email" required>
              E-mail
            </Label>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={isSubmitting}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="senha" required>
              Senha
            </Label>
            <Input
              id="senha"
              name="senha"
              type="password"
              autoComplete="current-password"
              required
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
              disabled={isSubmitting}
            />
          </div>
          <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Entrando..." : "Entrar"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
