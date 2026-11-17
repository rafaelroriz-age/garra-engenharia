// Executa com `npm run test:unit` (node:test, sem dependências novas).
// Vetor de teste: 00_docs/backlog-auto/snapshot-cifrado.md §6 (o mesmo de 04_backend/tests/test_snapshot.py).
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  ModoLeituraErro,
  SenhaSnapshotInvalida,
  aguardarRotas,
  cancelarSenha,
  chaveRota,
  configurarModoLeitura,
  decifrarSnapshot,
  entrarModoLeitura,
  informarSenha,
  obterEstadoModoLeitura,
  resolverRota,
  responderModoLeitura,
  sairModoLeitura,
  tentarReconectar,
  type EnvelopeSnapshot,
} from "./modo-leitura.ts";
import { avaliarApiJson, comCacheBuster, raizDaApi } from "./api-descoberta.ts";

const SENHA = "garra-vetor-de-teste-2026";

const VETOR: EnvelopeSnapshot = {
  v: 1,
  kdf: { alg: "PBKDF2-SHA256", iter: 600000, salt: "AAECAwQFBgcICQoLDA0ODw==" },
  cifra: "AES-256-GCM",
  iv: "ZGVmZ2hpamtsbW5v",
  ct: "LS0+PjfaRdi0+WO5lD5DRc89s4wxV+TCZUANmOA1UrzmHO7qjPSmqwGI00eU2I4LxAKVDSu0g7qQuJolJdIMME/Tn09fMmxTMFfPmLfGkKEfK4UHX9UMhYF7P9CYWpH+G6Rk6jMm3mnUj3Hp5TXjORUECdJwyZ7tqpCUxp7gKbLItpUgf0tbxXswcoXkCE80VxlUnde+/aYeJAg/KWcCmOO0uh9Hn5g2kLV+ZObQBr9p5b7EnGq4p30F8P/2X76dmv3ZSjKeP4HXllsuiyODZUnx9ONVSGBx8u7hTDScEnCZUnQ8BM3X0Ot/ug==",
  gerado_em: "2026-11-17T12:00:00+00:00",
};

const ROTAS_ESPERADAS = {
  "/api/v1/auth/me": {
    email: "snapshot.servico@garra-engenharia.com.br",
    nome: "Snapshot de leitura (serviço)",
    role: "auditor",
  },
  "/api/v1/edificacoes?page=1&page_size=10": { items: [], page: 1, page_size: 10, total: 0 },
};

test("decifra o vetor de teste do T81 e resolve as rotas", async () => {
  const snap = await decifrarSnapshot(VETOR, SENHA);
  assert.equal(snap.gerado_em, "2026-11-17T12:00:00+00:00");
  assert.deepEqual(snap.rotas, ROTAS_ESPERADAS);
  // Chave = "/api/v1" + path, exatamente como a tela chama api.get(path).
  const params = new URLSearchParams({ page: "1", page_size: "10" });
  assert.deepEqual(resolverRota(snap.rotas, chaveRota(`/edificacoes?${params}`)), {
    items: [],
    page: 1,
    page_size: 10,
    total: 0,
  });
  assert.equal((resolverRota(snap.rotas, chaveRota("/auth/me")) as { role: string }).role, "auditor");
  assert.equal(resolverRota(snap.rotas, chaveRota("/contratos/1")), undefined);
});

test("senha errada falha com SenhaSnapshotInvalida", async () => {
  await assert.rejects(decifrarSnapshot(VETOR, `${SENHA}x`), SenhaSnapshotInvalida);
});

test("envelope de versão desconhecida é recusado sem tentar decifrar", async () => {
  await assert.rejects(decifrarSnapshot({ ...VETOR, v: 2 }, SENHA), /não suportado/);
  await assert.rejects(decifrarSnapshot({ ...VETOR, cifra: "ChaCha20" }, SENHA), /não suportado/);
});

test("filtros ausentes no snapshot são resolvidos localmente a partir da lista sem filtro", () => {
  const rotas = {
    "/api/v1/edificacoes?page=1&page_size=10": {
      items: [
        { id: 1, nome: "Edifício Ébano", endereco: "Rua A" },
        { id: 2, nome: "Torre Sul", endereco: "Av. Brasil" },
      ],
      total: 3,
      page: 1,
      page_size: 10,
    },
    "/api/v1/edificacoes?page=1&page_size=100": {
      items: [{ id: 3, nome: "Casa Norte", endereco: "Rua Ebano" }],
      total: 3,
      page: 1,
      page_size: 100,
    },
    "/api/v1/contratos?page=1&page_size=10": {
      items: [
        { id: 10, status: "ativo", tipo_servico: "rfo", edificacao_id: 1 },
        { id: 11, status: "ativo", tipo_servico: "ltip", edificacao_id: 1 },
        { id: 12, status: "encerrado", tipo_servico: "rfo", edificacao_id: 2 },
      ],
      total: 3,
      page: 1,
      page_size: 10,
    },
    "/api/v1/inspecoes/5/ocorrencias": [
      { id: "a", sistema_id: 1, grau_risco: "alto" },
      { id: "b", sistema_id: 2, grau_risco: "alto" },
    ],
  };
  // Busca livre: nome OU endereço, sem acento/caixa.
  const busca = new URLSearchParams({ page: "1", page_size: "10", nome: "ebano", endereco: "ebano" });
  const r1 = resolverRota(rotas, chaveRota(`/edificacoes?${busca}`)) as { items: { id: number }[]; total: number };
  assert.deepEqual(
    r1.items.map((i) => i.id),
    [1, 3],
  );
  assert.equal(r1.total, 2);
  // Filtros combinados de contratos.
  const comb = new URLSearchParams({ page: "1", page_size: "10", tipo_servico: "rfo", status: "ativo" });
  const r2 = resolverRota(rotas, chaveRota(`/contratos?${comb}`)) as { items: { id: number }[] };
  assert.deepEqual(
    r2.items.map((i) => i.id),
    [10],
  );
  // Página além do fim: lista vazia com o total.
  const r3 = resolverRota(rotas, chaveRota("/contratos?page=2&page_size=10")) as { items: unknown[]; total: number };
  assert.deepEqual(r3.items, []);
  assert.equal(r3.total, 3);
  // Lista em array: filtro sem combinação no snapshot ⇒ filtra localmente.
  assert.deepEqual(resolverRota(rotas, chaveRota("/inspecoes/5/ocorrencias?sistema_id=3&grau_risco=alto")), []);
  assert.deepEqual(
    (resolverRota(rotas, chaveRota("/inspecoes/5/ocorrencias?sistema_id=2")) as { id: string }[]).map((o) => o.id),
    ["b"],
  );
  // Caminho que não existe ⇒ undefined.
  assert.equal(resolverRota(rotas, chaveRota("/responsaveis")), undefined);
});

test("store: entra, pede senha, responde GET, recusa escrita e sai quando o servidor volta", async () => {
  let voltou = false;
  configurarModoLeitura({ baixarEnvelope: async () => VETOR, servidorVoltou: async () => voltou });

  await entrarModoLeitura("servidor desligado");
  let e = obterEstadoModoLeitura();
  assert.equal(e.ativo, true);
  assert.equal(e.pedindoSenha, true);
  assert.equal(e.geradoEm, "2026-11-17T12:00:00+00:00");

  // GET pendente aguarda a senha; senha errada mantém o diálogo aberto.
  const pendente = responderModoLeitura("/auth/me", "GET");
  assert.equal(await informarSenha("errada"), false);
  assert.equal(obterEstadoModoLeitura().erro, "Senha incorreta.");
  assert.equal(await informarSenha(SENHA), true);
  assert.equal(((await pendente) as { role: string }).role, "auditor");

  await assert.rejects(responderModoLeitura("/edificacoes", "POST"), (err: unknown) => {
    assert.ok(err instanceof ModoLeituraErro);
    assert.equal(err.motivo, "escrita");
    assert.match(err.message, /Servidor desligado — modo leitura/);
    return true;
  });
  await assert.rejects(responderModoLeitura("/contratos/9", "GET"), (err: unknown) => {
    return err instanceof ModoLeituraErro && err.motivo === "sem-dados";
  });

  assert.equal(await tentarReconectar(), false);
  voltou = true;
  assert.equal(await tentarReconectar(), true);
  e = obterEstadoModoLeitura();
  assert.equal(e.ativo, false);
  assert.equal(e.desbloqueado, false);
});

test("store: cancelar o diálogo rejeita as leituras pendentes", async () => {
  configurarModoLeitura({ baixarEnvelope: async () => VETOR, servidorVoltou: async () => false });
  await entrarModoLeitura("teste");
  const pendente = aguardarRotas();
  cancelarSenha();
  await assert.rejects(pendente, (err: unknown) => err instanceof ModoLeituraErro && err.motivo === "bloqueado");
  sairModoLeitura();
});

test("descoberta: online, desligado, heartbeat velho e sem URL", () => {
  const agora = Date.parse("2026-11-17T12:30:00Z");
  const ok = avaliarApiJson(
    { url: "https://x.trycloudflare.com", online: true, heartbeat: "2026-11-17T12:25:00Z" },
    agora,
  );
  assert.equal(ok.online, true);
  assert.equal(ok.apiBase, "https://x.trycloudflare.com/api/v1");
  assert.equal(ok.raiz, "https://x.trycloudflare.com");
  const comBase = avaliarApiJson(
    { api_base: "https://y.trycloudflare.com/api/v1/", online: true, heartbeat: "2026-11-17T12:25:00Z" },
    agora,
  );
  assert.equal(comBase.apiBase, "https://y.trycloudflare.com/api/v1");
  assert.equal(comBase.raiz, "https://y.trycloudflare.com");
  assert.equal(avaliarApiJson({ url: "https://x", online: false, heartbeat: "2026-11-17T12:25:00Z" }, agora).online, false);
  assert.equal(avaliarApiJson({ url: "https://x", online: true, heartbeat: "2026-11-17T12:05:00Z" }, agora).online, false);
  assert.equal(avaliarApiJson({ online: true, heartbeat: "2026-11-17T12:25:00Z" }, agora).online, false);
  assert.equal(avaliarApiJson(null, agora).online, false);
  assert.equal(comCacheBuster("https://raw/api.json", 5), "https://raw/api.json?t=5");
  assert.equal(raizDaApi("http://localhost:8000/api/v1"), "http://localhost:8000");
});
