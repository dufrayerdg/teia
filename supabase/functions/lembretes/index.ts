// Didi · lembretes no celular (web push). Chamado a cada 5 minutos pelo agendador do banco (pg_cron).
import { createClient } from "npm:@supabase/supabase-js@2";
import webpush from "npm:web-push@3.6.7";
import { fusoHoje, fusoHora } from "../_shared/comum.ts";

const JANELA = 5; // minutos
const aMin = (h: string) => { const [a, b] = (h || "").split(":").map(Number); return Number.isFinite(a) && Number.isFinite(b) ? a * 60 + b : -1; };
const naJanela = (h: string, agora: number) => { const m = aMin(h); return m >= 0 && m <= agora && m > agora - JANELA; };
const addDia = (iso: string, n: number) => { const d = new Date(iso + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };

Deno.serve(async (req) => {
  const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const { data: seg } = await admin.rpc("segredos_lembretes");
  if (!seg || req.headers.get("x-teia-cron") !== seg.cron) return new Response("não autorizado", { status: 401 });
  webpush.setVapidDetails("mailto:contato@minhateia.app", seg.vapid_publica, seg.vapid_privada);

  const hoje = fusoHoje(), amanha = addDia(hoje, 1), agora = aMin(fusoHora()), dow = new Date(hoje + "T12:00:00Z").getUTCDay();
  const { data: subs } = await admin.from("push_inscricoes").select("endpoint,p256dh,auth,dono");
  const porDono = new Map<string, any[]>(); for (const s of subs ?? []) porDono.set(s.dono, [...(porDono.get(s.dono) ?? []), s]);
  let enviados = 0;

  for (const [dono, inscricoes] of porDono) {
    const [perfil, membros, meds, cons, trat, marc] = await Promise.all([
      admin.from("perfis").select("lembretes").eq("user_id", dono).maybeSingle(),
      admin.from("membros").select("id,nome").eq("user_id", dono).order("criado_em"),
      admin.from("medicamentos").select("id,membro_id,nome,dose,horarios,inicio,fim,estoque,por_tomada").eq("user_id", dono),
      admin.from("consultas").select("id,membro_id,titulo,data,hora,local").eq("user_id", dono).in("data", [hoje, amanha]),
      admin.from("tratamentos").select("id,membro_id,tipo,dias,hora").eq("user_id", dono),
      admin.from("marcacoes").select("chave").eq("user_id", dono).eq("dia", hoje),
    ]);
    const pref = perfil.data?.lembretes ?? {}; const on = (k: string) => pref[k] !== false;
    const lista = membros.data ?? []; const nomeDe = (id: string | null) => (lista.find((m: any) => m.id === id) ?? lista[0] ?? { nome: "" }).nome;
    const feitos = new Set((marc.data ?? []).map((m: any) => m.chave));
    const msgs: { chave: string; titulo: string; corpo: string; tag: string }[] = [];
    const ativo = (m: any) => (!m.inicio || m.inicio <= hoje) && (!m.fim || m.fim >= hoje);

    if (on("remedio")) for (const m of meds.data ?? []) if (ativo(m)) for (const h of m.horarios ?? []) {
      if (naJanela(h, agora) && !feitos.has(`med:${m.id}:${h}`)) msgs.push({ chave: `${dono}|rem|${m.id}|${hoje}|${h}`, titulo: `Hora do remédio de ${nomeDe(m.membro_id)}`, corpo: `${m.nome}${m.dose ? " " + m.dose : ""} · ${h}`, tag: `rem-${m.id}` });
    }
    if (on("consulta")) for (const c of cons.data ?? []) {
      if (c.data === amanha && naJanela("19:00", agora)) msgs.push({ chave: `${dono}|cons1d|${c.id}`, titulo: `Amanhã: ${c.titulo}`, corpo: `Consulta de ${nomeDe(c.membro_id)}${c.hora ? " às " + c.hora : ""}${c.local ? " · " + c.local : ""}`, tag: `cons-${c.id}` });
      if (c.data === hoje && c.hora && naJanela(fmt(aMin(c.hora) - 60), agora)) msgs.push({ chave: `${dono}|cons1h|${c.id}`, titulo: `Daqui a 1 hora: ${c.titulo}`, corpo: `Consulta de ${nomeDe(c.membro_id)} às ${c.hora}${c.local ? " · " + c.local : ""}`, tag: `cons-${c.id}` });
    }
    if (on("receita") && naJanela("09:00", agora)) for (const m of meds.data ?? []) if (ativo(m)) {
      if (m.fim && m.fim <= addDia(hoje, 3)) msgs.push({ chave: `${dono}|fim|${m.id}|${hoje}`, titulo: `A receita de ${m.nome} está acabando`, corpo: `Termina em ${m.fim.split("-").reverse().join("/")}. Fale com o médico para renovar.`, tag: `fim-${m.id}` });
      const porDia = (Number(m.por_tomada) || 1) * Math.max(1, (m.horarios ?? []).length);
      if (m.estoque != null && Math.floor(Number(m.estoque) / porDia) <= 3) msgs.push({ chave: `${dono}|est|${m.id}|${hoje}`, titulo: `${m.nome} está acabando`, corpo: `Restam ${Math.floor(Number(m.estoque) / porDia)} dia(s) de estoque em casa.`, tag: `est-${m.id}` });
    }
    if (on("manha") && naJanela("07:30", agora)) {
      const partes: string[] = [];
      for (const pessoa of lista.length ? lista : [{ id: null, nome: "" }]) {
        const deles = (x: any) => !lista.length || (x.membro_id || lista[0].id) === pessoa.id;
        const nMeds = (meds.data ?? []).filter((m: any) => ativo(m) && deles(m)).reduce((t: number, m: any) => t + (m.horarios ?? []).length, 0);
        const sess = (trat.data ?? []).filter((t: any) => deles(t) && (t.dias ?? []).includes(dow)).map((t: any) => `${String(t.tipo).split(" (")[0]}${t.hora ? " " + t.hora : ""}`);
        const cs = (cons.data ?? []).filter((c: any) => deles(c) && c.data === hoje).map((c: any) => `${c.titulo}${c.hora ? " " + c.hora : ""}`);
        const itens = [nMeds ? `${nMeds} dose(s) de remédio` : "", ...sess, ...cs].filter(Boolean);
        if (itens.length) partes.push(`${pessoa.nome ? pessoa.nome + ": " : ""}${itens.join(", ")}`);
      }
      if (partes.length) msgs.push({ chave: `${dono}|manha|${hoje}`, titulo: "Hoje no Didi", corpo: partes.join(" · "), tag: "manha" });
    }

    for (const m of msgs) {
      const { error } = await admin.from("lembretes_enviados").insert({ chave: m.chave });
      if (error) continue; // já enviado
      for (const s of inscricoes) {
        try { await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify({ titulo: m.titulo, corpo: m.corpo, tag: m.tag, url: "/" }), { TTL: 3600 }); enviados++; }
        catch (e) { const st = (e as any)?.statusCode; if (st === 404 || st === 410) await admin.from("push_inscricoes").delete().eq("endpoint", s.endpoint); else console.error("push", st, (e as Error).message); }
      }
    }
  }
  await admin.from("lembretes_enviados").delete().lt("enviado_em", new Date(Date.now() - 3 * 864e5).toISOString());
  return new Response(JSON.stringify({ ok: true, enviados }), { headers: { "Content-Type": "application/json" } });
});

function fmt(min: number) { const m = ((min % 1440) + 1440) % 1440; return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`; }
