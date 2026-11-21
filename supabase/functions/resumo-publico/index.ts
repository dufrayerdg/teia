// Didi · resumo para o profissional (link de leitura com validade). Público: valida o token no servidor.
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const json = (c: unknown, s = 200) => new Response(JSON.stringify(c), { status: s, headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "no-store" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const t = new URL(req.url).searchParams.get("t") || "";
  if (t.length < 24 || t.length > 80) return json({ erro: "link_invalido" }, 404);
  const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const { data: link } = await admin.from("links_profissional").select("*").eq("token", t).maybeSingle();
  if (!link || link.revogado || new Date(link.expira_em) < new Date()) return json({ erro: "link_invalido" }, 404);
  await admin.from("links_profissional").update({ acessos: (link.acessos || 0) + 1 }).eq("token", t);

  const dono = link.user_id; const hoje = new Date().toISOString().slice(0, 10); const desde = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  const [perfil, membros] = await Promise.all([
    admin.from("perfis").select("mae,papel,crianca,nascimento,diagnosticos,plano_saude").eq("user_id", dono).maybeSingle(),
    admin.from("membros").select("id,nome,nascimento,diagnosticos,plano_saude").eq("user_id", dono).order("criado_em"),
  ]);
  const lista = membros.data ?? []; const membro = lista.find((m: any) => m.id === link.membro_id) ?? lista[0] ?? null;
  const primeiro = !membro || (lista[0] && membro.id === lista[0].id);
  const f = (q0: any) => { const q = q0.eq("user_id", dono); return membro ? (primeiro ? q.or(`membro_id.eq.${membro.id},membro_id.is.null`) : q.eq("membro_id", membro.id)) : q; };
  const [meds, trat, regs, docs, cons, marcos, notas] = await Promise.all([
    f(admin.from("medicamentos").select("nome,dose,horarios,inicio,fim,medico")),
    f(admin.from("tratamentos").select("tipo,profissional,dias,hora,meta")),
    f(admin.from("registros").select("data,humor,sono,crise,crise_info")).gte("data", desde),
    f(admin.from("documentos").select("tipo,titulo,data,profissional,resumo")).order("data", { ascending: false }).limit(6),
    f(admin.from("consultas").select("titulo,data,hora,profissional")).gte("data", desde).order("data").limit(10),
    f(admin.from("marcos").select("titulo,data")).order("data", { ascending: false }).limit(5),
    f(admin.from("notas_consulta").select("titulo,texto")).eq("feito", false).limit(10),
  ]);
  const r = regs.data ?? []; const sono: Record<string, number> = { Bom: 0, Regular: 0, Ruim: 0 }; const gat: Record<string, number> = {};
  for (const x of r) { if (sono[x.sono] !== undefined) sono[x.sono]++; if (x.crise) for (const g of (x.crise_info?.gatilhos ?? [])) gat[g] = (gat[g] || 0) + 1; }
  const p = perfil.data ?? {};
  return json({
    gerado: hoje, expira: link.expira_em, quem: p.mae || "", papel: p.papel || "",
    pessoa: membro ? { nome: membro.nome, nascimento: membro.nascimento, diagnosticos: membro.diagnosticos, plano_saude: membro.plano_saude } : { nome: p.crianca, nascimento: p.nascimento, diagnosticos: p.diagnosticos, plano_saude: p.plano_saude },
    remedios: (meds.data ?? []).filter((m: any) => (!m.inicio || m.inicio <= hoje) && (!m.fim || m.fim >= hoje)),
    terapias: trat.data ?? [], documentos: docs.data ?? [], consultas: cons.data ?? [], marcos: marcos.data ?? [], notas: notas.data ?? [],
    ultimos30: { dias: r.length, humor: r.length ? r.reduce((t: number, x: any) => t + (x.humor || 3), 0) / r.length : 0, sono, crises: r.filter((x: any) => x.crise).length, gatilhos: Object.entries(gat).sort((a, b) => b[1] - a[1]).slice(0, 4) },
  });
});
