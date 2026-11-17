"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Lock } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { verificarServidorAoIniciar } from "@/lib/api-client";
import { cancelarSenha, informarSenha, pedirSenha, useModoLeitura } from "@/lib/modo-leitura";

function formatarData(iso: string | null): string {
  if (!iso) return "data desconhecida";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(d);
}

/**
 * Faixa fixa "Modo leitura — dados de <data>" (DEC-57 P5) e diálogo da senha da
 * equipe para decifrar o snapshot. Também dispara a checagem do `api.json` na
 * abertura do app. Fora do modo leitura não renderiza nada.
 */
export function ModoLeituraBanner() {
  const modo = useModoLeitura();
  const [senha, setSenha] = useState("");

  useEffect(() => {
    void verificarServidorAoIniciar();
  }, []);

  if (!modo.ativo) return null;

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (await informarSenha(senha)) setSenha("");
  }

  return (
    <>
      {/* Espaço reservado para a faixa fixa não cobrir o fim da página. */}
      <div aria-hidden="true" className="h-11" />
      <div
        role="status"
        className="fixed inset-x-0 bottom-0 z-40 flex min-h-11 flex-wrap items-center justify-center gap-x-3 gap-y-1 border-t border-sev-atencao/50 bg-sev-atencao/[0.15] px-4 py-2 text-sm text-foreground backdrop-blur"
      >
        <Lock className="h-4 w-4 shrink-0 text-sev-atencao" aria-hidden="true" />
        <span className="font-medium">
          Modo leitura — dados de <span className="dado">{formatarData(modo.geradoEm)}</span>
        </span>
        <span className="text-muted-foreground">Servidor desligado: gravações indisponíveis.</span>
        {!modo.desbloqueado && !modo.pedindoSenha ? (
          <Button type="button" size="sm" variant="outline" className="h-8" onClick={pedirSenha}>
            Informar senha
          </Button>
        ) : null}
      </div>

      <Dialog
        open={modo.pedindoSenha}
        onOpenChange={(aberto) => {
          if (!aberto) cancelarSenha();
        }}
      >
        <DialogContent className="max-w-sm">
          <form onSubmit={(e) => void enviar(e)} className="space-y-4">
            <DialogHeader>
              <DialogTitle>Modo leitura</DialogTitle>
              <DialogDescription>
                O servidor está desligado. Informe a senha da equipe para ver os dados de{" "}
                {formatarData(modo.geradoEm)} (somente leitura).
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2">
              <Label htmlFor="modo-leitura-senha">Senha da equipe</Label>
              <Input
                id="modo-leitura-senha"
                type="password"
                autoComplete="current-password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                aria-invalid={modo.erro ? true : undefined}
                aria-describedby={modo.erro ? "modo-leitura-erro" : undefined}
                autoFocus
              />
              {modo.erro ? (
                <p id="modo-leitura-erro" role="alert" className="text-sm text-destructive">
                  {modo.erro}
                </p>
              ) : null}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={cancelarSenha}>
                Cancelar
              </Button>
              <Button type="submit" disabled={modo.carregando || senha === ""}>
                {modo.carregando ? "Abrindo..." : "Abrir dados"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
