import { createClient, type SupabaseClient } from "npm:@supabase/supabase-js@2";

export const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

export const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { ...CORS, "Content-Type": "application/json" } });

/** Cliente com a sessão de quem chamou (respeita RLS) + cliente de serviço. */
export async function contexto(req: Request) {
  const url = Deno.env.get("SUPABASE_URL")!;
  const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const auth = req.headers.get("Authorization") ?? "";
  const usuario: SupabaseClient = createClient(url, anon, { global: { headers: { Authorization: auth } }, auth: { persistSession: false } });
  const admin: SupabaseClient = createClient(url, service, { auth: { persistSession: false } });
  const { data, error } = await usuario.auth.getUser();
  if (error || !data.user) return null;
  return { user: data.user, usuario, admin };
}

/** Conta cujos dados a pessoa usa: a própria ou a de quem a convidou (família). */
export async function donoDe(admin: SupabaseClient, userId: string): Promise<string> {
  const { data } = await admin.from("acessos").select("dono").eq("convidado", userId).order("criado_em").limit(1).maybeSingle();
  return (data && data.dono) || userId;
}

export const fusoHoje = (d = new Date()) => new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
export const fusoHora = (d = new Date()) => new Intl.DateTimeFormat("en-GB", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", hour12: false }).format(d);

// Limites de uso da IA (custo previsível). Preços de referência (USD por 1 milhão de tokens):
// Haiku 5.5 = US$ 0,10 entrada / US$ 0,50 saída (chat) e Sonnet 5.5 = US$ 2 / US$ 10 (leitura de documentos).
// Estimativa (US$ 1 = R$ 5,50): pergunta ≈ R$ 0,004; leitura ≈ R$ 0,10 (até R$ 0,21 com 4 páginas).
// Teto no Didi+: 300 perguntas (≈ R$ 1,20) + 30 leituras (≤ R$ 6,30) por mês por conta.
export const LIMITE = { leitura: 3, pergunta: 5 } as const;                              // plano grátis, por mês
export const LIMITE_PLUS = { leitura: 30, pergunta: 300, resumo: 8 } as const;           // Didi+, por mês
export const LIMITE_DIA = { leitura: 8, pergunta: 30, resumo: 3 } as const;              // qualquer plano, por dia
export const FREIO_GLOBAL_DIA = { leitura: 600, pergunta: 30000 } as const;              // soma de todas as contas, por dia
export const mesAtual = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit" }).format(new Date()).slice(0, 7);

export async function ehPlus(admin: SupabaseClient, userId: string) {
  const { data } = await admin.from("assinaturas").select("plano,status").eq("user_id", userId).maybeSingle();
  return !!data && data.plano === "plus" && ["ativa", "teste"].includes(data.status);
}

export async function usoDoMes(admin: SupabaseClient, userId: string) {
  const { data } = await admin.from("uso_ia").select("leituras,perguntas,resumos").eq("user_id", userId).eq("mes", mesAtual()).maybeSingle();
  return data ?? { leituras: 0, perguntas: 0, resumos: 0 };
}

export async function usoDoDia(admin: SupabaseClient, userId: string) {
  const { data } = await admin.from("uso_ia_dia").select("leituras,perguntas,resumos").eq("user_id", userId).eq("dia", fusoHoje()).maybeSingle();
  return data ?? { leituras: 0, perguntas: 0, resumos: 0 };
}

export async function usoGlobalDoDia(admin: SupabaseClient) {
  const { data } = await admin.rpc("uso_global", { p_dia: fusoHoje() });
  const r = Array.isArray(data) ? data[0] : data;
  return { leituras: Number(r?.leituras ?? 0), perguntas: Number(r?.perguntas ?? 0) };
}
