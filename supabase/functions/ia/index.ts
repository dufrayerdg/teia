// teia · IA no servidor
// Tarefas: "receita" e "laudo" (leitura de imagens), "pergunta" (assistente) e "resumo" (relatório do mês).
// A chave ANTHROPIC_API_KEY fica só aqui. Limites do plano grátis são conferidos antes de cada chamada.
import { CORS, json, contexto, LIMITE, ehPlus, usoDoMes, mesAtual } from "../_shared/comum.ts";
import { P_RECEITA, P_LAUDO } from "../_shared/prompts.ts";

const MODELO_LEITURA = Deno.env.get("MODELO_LEITURA") ?? "claude-sonnet-5-5";
const MODELO_CONVERSA = Deno.env.get("MODELO_CONVERSA") ?? "claude-haiku-5-5";
const MAX_IMAGENS = 4;
const MAX_BYTES_IMAGEM = 4_500_000;

type Msg = { role: "user" | "assistant"; content: unknown };

async function claude(modelo: string, mensagens: Msg[], sistema: string | undefined, maxTokens: number) {
  const chave = Deno.env.get("ANTHROPIC_API_KEY");
  if (!chave) throw Object.assign(new Error("sem_chave"), { code: "sem_chave" });
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": chave, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: modelo, max_tokens: maxTokens, ...(sistema ? { system: sistema } : {}), messages: mensagens }),
  });
  if (r.status === 429) throw Object.assign(new Error("rate_limited"), { code: "rate_limited" });
  if (!r.ok) throw new Error(`anthropic ${r.status}: ${(await r.text()).slice(0, 300)}`);
  const d = await r.json();
  return (d.content ?? []).filter((b: { type: string }) => b.type === "text").map((b: { text: string }) => b.text).join("");
}

const extrairJSON = (t: string) => { const m = String(t).match(/\{[\s\S]*\}/); if (!m) throw new Error("sem json"); return JSON.parse(m[0]); };

function imagemParaBloco(dataUrl: string) {
  const m = /^data:(image\/(?:jpeg|png|webp|gif));base64,(.+)$/.exec(dataUrl || "");
  if (!m) throw new Error("imagem inválida");
  if (m[2].length * 0.75 > MAX_BYTES_IMAGEM) throw new Error("imagem grande demais");
  return { type: "image", source: { type: "base64", media_type: m[1], data: m[2] } };
}

const DIAS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const HUMOR = ["Difícil", "Ruim", "Ok", "Bom", "Ótimo"];

async function dadosDaFamilia(usuario: any) {
  const desde = new Date(Date.now() - 60 * 864e5).toISOString().slice(0, 10);
  const [perfil, meds, trat, tar, docs, regs] = await Promise.all([
    usuario.from("perfis").select("mae,crianca,nascimento,diagnosticos,plano_saude").maybeSingle(),
    usuario.from("medicamentos").select("nome,dose,horarios,inicio,fim,medico"),
    usuario.from("tratamentos").select("tipo,profissional,local,dias,hora,meta,progresso"),
    usuario.from("tarefas").select("titulo,dias,hora"),
    usuario.from("documentos").select("tipo,titulo,data,profissional,especialidade,origem,resumo,recomendacoes,medicamentos").order("data", { ascending: false }).limit(25),
    usuario.from("registros").select("data,humor,sono,crise,conquista,nota").gte("data", desde).order("data", { ascending: false }).limit(40),
  ]);
  return {
    hoje: new Date().toISOString().slice(0, 10),
    perfil: perfil.data,
    remedios: meds.data ?? [],
    tratamentos: (trat.data ?? []).map((t: any) => ({ ...t, dias: (t.dias ?? []).map((d: number) => DIAS[d]) })),
    tarefas: (tar.data ?? []).map((t: any) => ({ ...t, dias: (t.dias ?? []).map((d: number) => DIAS[d]) })),
    documentos: docs.data ?? [],
    registros: (regs.data ?? []).map((r: any) => ({ ...r, humor: HUMOR[(r.humor || 3) - 1] })),
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ erro: "metodo" }, 405);
  const ctx = await contexto(req);
  if (!ctx) return json({ erro: "nao_autenticado" }, 401);
  const { user, usuario, admin } = ctx;

  let corpo: any;
  try { corpo = await req.json(); } catch { return json({ erro: "corpo_invalido" }, 400); }
  const tarefa = String(corpo?.tarefa || "");
  const plus = await ehPlus(admin, user.id);
  const uso = await usoDoMes(admin, user.id);

  try {
    if (tarefa === "receita" || tarefa === "laudo") {
      if (!plus && uso.leituras >= LIMITE.leitura) return json({ erro: "limite", motivo: "leitura" }, 402);
      const imagens = (Array.isArray(corpo.imagens) ? corpo.imagens : []).slice(0, MAX_IMAGENS);
      if (!imagens.length) return json({ erro: "sem_imagem" }, 400);
      const blocos = [...imagens.map(imagemParaBloco), { type: "text", text: tarefa === "receita" ? P_RECEITA : P_LAUDO }];
      const texto = await claude(MODELO_LEITURA, [{ role: "user", content: blocos }], undefined, 2500);
      const resultado = extrairJSON(texto);
      await admin.rpc("registrar_uso_ia", { p_user: user.id, p_tipo: "leitura" });
      return json({ resultado });
    }

    if (tarefa === "pergunta") {
      if (!plus && uso.perguntas >= LIMITE.pergunta) return json({ erro: "limite", motivo: "pergunta" }, 402);
      const historico: Msg[] = (Array.isArray(corpo.historico) ? corpo.historico : [])
        .filter((m: any) => (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
        .slice(-10).map((m: any) => ({ role: m.role, content: m.content.slice(0, 2000) }));
      while (historico.length && historico[0].role !== "user") historico.shift();
      if (!historico.length || historico[historico.length - 1].role !== "user") return json({ erro: "sem_pergunta" }, 400);
      const dados = await dadosDaFamilia(usuario);
      const crianca = dados.perfil?.crianca || "a criança";
      const sistema = `Você é o assistente da teia, um app para mães de crianças atípicas, sobre ${crianca}. Regras:
1) Responda em português do Brasil em NO MÁXIMO 2 frases curtas (até 35 palavras), sem listas e sem detalhes desnecessários.
2) Use SOMENTE os dados abaixo. Se a informação não estiver neles, diga isso em uma frase.
3) Nunca diagnostique, nem opine sobre saúde, comportamento ou tratamento, nem recomende remédios ou doses.
4) Se a mãe pedir opinião, conselho ou orientação (por exemplo "devo", "é normal", "o que faço", "o que acha"), NÃO opine. Diga em uma frase que isso é para o profissional avaliar e preencha "anotacao" com uma nota objetiva para levar à consulta: 1 a 3 frases descrevendo o que a criança fez ou está fazendo (só fatos dos dados e da fala da mãe, sem interpretar) e a pergunta a fazer. "para" é a especialidade mais indicada entre os profissionais e terapias dos dados, ou null. Nos demais casos, "anotacao" é null.
Responda APENAS com JSON: {"resposta":string,"anotacao":null|{"titulo":string (até 6 palavras),"texto":string,"para":string|null}}
DADOS: ${JSON.stringify(dados)}`;
      const texto = await claude(MODELO_CONVERSA, historico, sistema, 500);
      let resultado: any; try { resultado = extrairJSON(texto); } catch { resultado = { resposta: texto, anotacao: null }; }
      await admin.rpc("registrar_uso_ia", { p_user: user.id, p_tipo: "pergunta" });
      return json({ resultado });
    }

    if (tarefa === "resumo") {
      if (!plus) return json({ erro: "limite", motivo: "relatorio" }, 402);
      const dados = await dadosDaFamilia(usuario);
      const mes = mesAtual();
      const regs = dados.registros.filter((r: any) => String(r.data).startsWith(mes));
      const { data: notas } = await usuario.from("notas_consulta").select("titulo,texto,para").eq("feito", false).limit(10);
      const prompt = `Escreva em português do Brasil um resumo curto (até 170 palavras) do mês da criança ${dados.perfil?.crianca || ""}, para a mãe levar às terapeutas. Tom acolhedor e objetivo. Organize em: Presença nas terapias; Como foram os dias; Conquistas; Pontos para conversar. Sem diagnósticos nem recomendações clínicas. Use só os dados abaixo.
Tratamentos: ${JSON.stringify(dados.tratamentos)}
Sessões do mês (marcadas): ${JSON.stringify(corpo.sessoes ?? [])}
Registros do mês: ${JSON.stringify(regs)}
Anotações pendentes para a consulta: ${JSON.stringify(notas ?? [])}`;
      const texto = await claude(MODELO_CONVERSA, [{ role: "user", content: prompt }], undefined, 700);
      await admin.rpc("registrar_uso_ia", { p_user: user.id, p_tipo: "resumo" });
      return json({ resultado: { texto } });
    }

    return json({ erro: "tarefa_desconhecida" }, 400);
  } catch (e) {
    const code = (e as any)?.code;
    if (code === "rate_limited") return json({ erro: "rate_limited" }, 429);
    if (code === "sem_chave") return json({ erro: "ia_nao_configurada" }, 503);
    console.error("ia:", tarefa, (e as Error).message);
    return json({ erro: "falha_ia" }, 502);
  }
});
