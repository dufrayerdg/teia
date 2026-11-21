// Didi · assinatura Didi+
// Enquanto o pagamento real (Mercado Pago / Stripe / lojas) não está ligado, esta função só
// simula a assinatura quando PAGAMENTOS_TESTE=true. Em produção, quem ativa o Didi+ é o webhook do gateway.
import { CORS, json, contexto } from "../_shared/comum.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const ctx = await contexto(req);
  if (!ctx) return json({ erro: "nao_autenticado" }, 401);
  if (Deno.env.get("PAGAMENTOS_TESTE") !== "true") return json({ erro: "pagamentos_indisponiveis" }, 503);
  const { user, admin } = ctx;
  const { acao, ciclo } = await req.json().catch(() => ({}));
  const hoje = new Date();
  if (acao === "assinar") {
    if (!["mensal", "anual"].includes(ciclo)) return json({ erro: "ciclo" }, 400);
    const renova = new Date(hoje); ciclo === "anual" ? renova.setDate(renova.getDate() + 7) : renova.setMonth(renova.getMonth() + 1);
    const { error } = await admin.from("assinaturas").upsert({ user_id: user.id, plano: "plus", ciclo, status: ciclo === "anual" ? "teste" : "ativa", desde: hoje.toISOString().slice(0, 10), renova_em: renova.toISOString().slice(0, 10), gateway: "simulado" });
    if (error) return json({ erro: "falha" }, 500);
    return json({ ok: true });
  }
  if (acao === "cancelar") {
    const { error } = await admin.from("assinaturas").update({ plano: "gratis", status: "cancelada" }).eq("user_id", user.id);
    if (error) return json({ erro: "falha" }, 500);
    return json({ ok: true });
  }
  return json({ erro: "acao" }, 400);
});
