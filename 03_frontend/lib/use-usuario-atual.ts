"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api-client";

export type PerfilUsuario = "auditor" | "auxiliar" | "cliente";

export interface UsuarioAtual {
  id: string;
  nome: string;
  email: string;
  ativo: boolean;
  role: PerfilUsuario;
}

/**
 * Perfil do usuário autenticado (`GET /auth/me`), usado apenas para ocultar
 * ações que ele não pode executar (RN-18, DEC-27). A autorização real é sempre
 * do backend — esconder um botão aqui é usabilidade, nunca controle de acesso.
 *
 * Enquanto o perfil carrega, `isAuditor` é `false`: prefere-se esconder uma ação
 * permitida por um instante a piscar uma ação proibida.
 */
export function useUsuarioAtual() {
  const [usuario, setUsuario] = useState<UsuarioAtual | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let ativo = true;
    api
      .get<UsuarioAtual>("/auth/me")
      .then((dados) => {
        if (ativo) setUsuario(dados);
      })
      .catch(() => {
        if (ativo) setUsuario(null);
      })
      .finally(() => {
        if (ativo) setIsLoading(false);
      });
    return () => {
      ativo = false;
    };
  }, []);

  return {
    usuario,
    isLoading,
    isAuditor: usuario?.role === "auditor",
    isAuxiliar: usuario?.role === "auxiliar",
  };
}
