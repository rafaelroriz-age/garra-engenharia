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
    <Card className="w-full max-w-sm">
      <CardHeader className="space-y-3 text-center">
        <Logo variant="principal" className="mx-auto" />
        <CardTitle className="font-display text-xl">Acessar sua conta</CardTitle>
        <CardDescription>Informe suas credenciais para continuar.</CardDescription>
        <Badge variant="outline" className="mx-auto w-fit">
          RNF-05 · BL-06
        </Badge>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          <ApiErrorAlert error={error} />
          <div className="space-y-1.5">
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
          <div className="space-y-1.5">
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
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Entrando..." : "Entrar"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
