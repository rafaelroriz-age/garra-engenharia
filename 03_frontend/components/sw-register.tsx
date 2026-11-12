"use client";

import { useEffect } from "react";

/** Evento disparado por `clearAuthToken()` no logout (ver lib/api-client.ts). */
export const SW_CLEAR_EVENT = "garra:clear-sw-cache";

/** Registra o Service Worker de leitura (DEC-26) apenas em produção. */
export function SwRegister() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;

    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Falha de registro não afeta o app: segue online-first sem cache.
    });

    function limpar() {
      navigator.serviceWorker.controller?.postMessage({ type: "CLEAR_DATA_CACHE" });
    }
    window.addEventListener(SW_CLEAR_EVENT, limpar);
    return () => window.removeEventListener(SW_CLEAR_EVENT, limpar);
  }, []);

  return null;
}
