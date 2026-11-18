// Servidor estático mínimo para `out/` (export estático do Next). `next start` não funciona com
// `output: "export"`, então o config offline (playwright.offline.config.ts) usa este script.
import { existsSync, readFileSync, statSync } from "node:fs";
import { createServer } from "node:http";
import path from "node:path";

const OUT = path.resolve(process.cwd(), "out");
const PORTA = Number(process.env.E2E_OFFLINE_PORTA ?? 3120);
const TIPOS = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon",
  ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8",
};

function achar(rel) {
  const alvo = path.normalize(path.join(OUT, decodeURIComponent(rel)));
  if (!alvo.startsWith(OUT)) return null;
  for (const c of [alvo, path.join(alvo, "index.html"), `${alvo}.html`]) {
    if (existsSync(c) && statSync(c).isFile()) return c;
  }
  return null;
}

createServer((req, res) => {
  const destino = achar(new URL(req.url ?? "/", "http://x").pathname);
  if (!destino) return void res.writeHead(404).end("nao encontrado");
  res.writeHead(200, { "Content-Type": TIPOS[path.extname(destino)] ?? "application/octet-stream", "Cache-Control": "no-store" });
  res.end(readFileSync(destino));
}).listen(PORTA, () => console.log(`out/ em http://localhost:${PORTA}`));
