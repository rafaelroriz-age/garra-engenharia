"use client";

import { useEffect } from "react";

import { AUTH_TOKEN_STORAGE_KEY } from "@/lib/api-client";
import { isLogoutStorageEvent } from "@/lib/sw-cache";
import { withBasePath } from "@/lib/utils";

/** Evento disparado por `clearAuthToken()` no logout (ver lib/api-client.ts). */
export const SW_CLEAR_EVENT = "garra:clear-sw-cache";

/** Registra o Service Worker de leitura (DEC-26) apenas em produção. */
export function SwRegister() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;

    // basePath do Pages (/garra-engenharia): script e scope sob o prefixo (R-22).
    navigator.serviceWorker.register(withBasePath("/sw.js"), { scope: withBasePath("/") }).catch(() => {
      // Falha de registro não afeta o app: segue online-first sem cache.
    });

    function limpar() {
      navigator.serviceWorker.controller?.postMessage({ type: "CLEAR_DATA_CACHE" });
    }
    // Logout em outra aba: o `storage` só dispara nas DEMAIS abas do mesmo origin
    // (a aba que fez o logout usa SW_CLEAR_EVENT). Reaproveita `limpar` (DEC-56).
    function aoMudarStorage(ev: StorageEvent) {
      if (isLogoutStorageEvent(ev, AUTH_TOKEN_STORAGE_KEY)) limpar();
    }
    window.addEventListener(SW_CLEAR_EVENT, limpar);
    window.addEventListener("storage", aoMudarStorage);
    return () => {
      window.removeEventListener(SW_CLEAR_EVENT, limpar);
      window.removeEventListener("storage", aoMudarStorage);
    };
  }, []);

  return null;
}
