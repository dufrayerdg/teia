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

export const LIMITE = { leitura: 3, pergunta: 5 } as const;
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
