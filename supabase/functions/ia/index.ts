// teia · IA no servidor
// Tarefas: "receita" e "laudo" (leitura de imagens), "pergunta" (assistente) e "resumo" (relatório do mês).
// A chave ANTHROPIC_API_KEY fica só aqui. Limites do plano grátis são conferidos antes de cada chamada.
import { CORS, json, contexto, LIMITE, ehPlus, usoDoMes, mesAtual, donoDe } from "../_shared/comum.ts";
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

/** Dados de UMA pessoa cuidada (membro). Itens antigos sem membro_id pertencem à primeira pessoa. */
async function dadosDaFamilia(usuario: any, dono: string, membroPedido?: string) {
  const desde = new Date(Date.now() - 60 * 864e5).toISOString().slice(0, 10);
  const [perfil, membros] = await Promise.all([
    usuario.from("perfis").select("mae,papel,crianca,nascimento,diagnosticos,plano_saude").eq("user_id", dono).maybeSingle(),
    usuario.from("membros").select("id,nome,relacao,nascimento,diagnosticos,plano_saude").eq("user_id", dono).order("criado_em"),
  ]);
  const lista = membros.data ?? [];
  const membro = lista.find((m: any) => m.id === membroPedido) ?? lista[0] ?? null;
  const primeiro = !membro || (lista[0] && membro.id === lista[0].id);
  const filtro = (q0: any) => { const q = q0.eq("user_id", dono); return membro ? (primeiro ? q.or(`membro_id.eq.${membro.id},membro_id.is.null`) : q.eq("membro_id", membro.id)) : q; };
  const hoje = new Date().toISOString().slice(0, 10);
  const [meds, trat, tar, docs, regs, cons] = await Promise.all([
    filtro(usuario.from("medicamentos").select("nome,dose,horarios,inicio,fim,medico")),
    filtro(usuario.from("tratamentos").select("tipo,profissional,local,dias,hora,meta,progresso")),
    filtro(usuario.from("tarefas").select("titulo,dias,hora")),
    filtro(usuario.from("documentos").select("tipo,titulo,data,profissional,especialidade,origem,resumo,recomendacoes,medicamentos")).order("data", { ascending: false }).limit(25),
    filtro(usuario.from("registros").select("data,humor,sono,crise,conquista,nota")).gte("data", desde).order("data", { ascending: false }).limit(40),
    filtro(usuario.from("consultas").select("titulo,data,hora,profissional,local,obs")).gte("data", desde).order("data").limit(20),
  ]);
  const p = perfil.data ?? {};
  return {
    hoje,
    quem_pergunta: { nome: p.mae || null, papel: p.papel || null },
    pessoa_cuidada: membro ? { nome: membro.nome, relacao: membro.relacao, nascimento: membro.nascimento, diagnosticos: membro.diagnosticos, plano_saude: membro.plano_saude }
                           : { nome: p.crianca, nascimento: p.nascimento, diagnosticos: p.diagnosticos, plano_saude: p.plano_saude },
    consultas: cons.data ?? [],
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
  const dono = await donoDe(admin, user.id);

  let corpo: any;
  try { corpo = await req.json(); } catch { return json({ erro: "corpo_invalido" }, 400); }
  const tarefa = String(corpo?.tarefa || "");
  const plus = await ehPlus(admin, dono);
  const uso = await usoDoMes(admin, dono);

  try {
    if (tarefa === "receita" || tarefa === "laudo") {
      if (!plus && uso.leituras >= LIMITE.leitura) return json({ erro: "limite", motivo: "leitura" }, 402);
      const imagens = (Array.isArray(corpo.imagens) ? corpo.imagens : []).slice(0, MAX_IMAGENS);
      if (!imagens.length) return json({ erro: "sem_imagem" }, 400);
      const blocos = [...imagens.map(imagemParaBloco), { type: "text", text: tarefa === "receita" ? P_RECEITA : P_LAUDO }];
      const texto = await claude(MODELO_LEITURA, [{ role: "user", content: blocos }], undefined, 2500);
      const resultado = extrairJSON(texto);
      await admin.rpc("registrar_uso_ia", { p_user: dono, p_tipo: "leitura" });
      return json({ resultado });
    }

    if (tarefa === "pergunta") {
      if (!plus && uso.perguntas >= LIMITE.pergunta) return json({ erro: "limite", motivo: "pergunta" }, 402);
      const historico: Msg[] = (Array.isArray(corpo.historico) ? corpo.historico : [])
        .filter((m: any) => (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
        .slice(-10).map((m: any) => ({ role: m.role, content: m.content.slice(0, 2000) }));
      while (historico.length && historico[0].role !== "user") historico.shift();
      if (!historico.length || historico[historico.length - 1].role !== "user") return json({ erro: "sem_pergunta" }, 400);
      const dados = await dadosDaFamilia(usuario, dono, String(corpo.membro || ""));
      const pessoa = dados.pessoa_cuidada?.nome || "a pessoa cuidada";
      const quem = dados.quem_pergunta.nome ? `${dados.quem_pergunta.nome}${dados.quem_pergunta.papel ? ` (${dados.quem_pergunta.papel})` : ""}` : "quem cuida";
      const sistema = `Você é a teIA, a assistente da teia, um app de cuidado em família. Você conversa com ${quem} sobre ${pessoa}. Chame as pessoas pelo nome e nunca use termos genéricos como "mãe" ou "mães". Regras:
1) Você é uma presença acolhedora e muito inteligente, como uma amiga de confiança que entende de cuidado em família. Português do Brasil, tom caloroso, simples e natural. Seja BREVE: até 3 frases curtas (até 50 palavras), sem listas e sem títulos.
2) Toda resposta tem três toques, nesta ordem, em frases bem curtas: acolhimento sincero; um elogio verdadeiro e específico ao cuidado de quem pergunta (por exemplo: estar de olho, ter anotado, buscar informação, organizar a rotina de ${pessoa}); e a informação ou o próximo passo, de forma clara. Elogie só o que a pessoa de fato fez ou disse, nunca de forma vazia ou exagerada, e varie as palavras a cada resposta.
3) Use os dados abaixo para fatos sobre ${pessoa} (remédios, horários, consultas, documentos), citando nomes, dias e horários reais. Se um fato não estiver neles, diga com gentileza que ainda não há essa informação no app e como adicionar. Quando fizer sentido, termine com uma oferta curta (por exemplo: "Quer que eu anote isso para a consulta?").
4) Cautela: nunca diagnostique, nem diga se algo é normal ou preocupante no caso de ${pessoa}, nem recomende remédios, doses ou mudanças de tratamento.
5) Se a pessoa pedir opinião, conselho ou orientação, ou contar uma preocupação (por exemplo "devo", "é normal", "o que faço", "o que acha", "estou preocupado(a)"):
 a) Comece acolhendo em poucas palavras, reconhecendo o que a pessoa sente e o cuidado dela (por exemplo: "Faz todo sentido ficar de olho nisso.").
 b) Se ajudar, dê em uma frase uma informação geral e tranquilizadora, sem falar do caso de ${pessoa} e sem dizer o que fazer (por exemplo: mudanças no sono são um tema comum de conversa com profissionais).
 c) Diga com carinho qual profissional pode avaliar isso (de preferência um dos profissionais ou terapias dos dados) e que você anotou para levar à consulta.
 Preencha "anotacao" com uma nota objetiva: 1 a 3 frases com o que ${pessoa} fez ou está fazendo (só fatos dos dados e da fala da pessoa, sem interpretar) e a pergunta a fazer. "para" é a especialidade mais indicada, ou null. Nos demais casos, "anotacao" é null.
6) Se a pessoa demonstrar cansaço, tristeza ou sobrecarga, acolha primeiro, com calor, antes de qualquer informação.
7) Se houver sinal de emergência ou risco à vida de alguém, acolha e oriente com calma a ligar 192 (SAMU); se for sofrimento emocional intenso de quem cuida, lembre que o CVV atende no 188, a qualquer hora.
8) Gênero: ajuste a concordância ao gênero de quem fala com você (veja o papel nos dados e o nome). Mãe, avó, tia, irmã: feminino. Pai, avô, tio, irmão: masculino. Se o papel for "Cuidador(a)", "Outro" ou vazio, só use o gênero do primeiro nome quando for inequívoco; na dúvida, use formas neutras que não flexionam (por exemplo "você cuida com tanto carinho", "foi ótimo ter anotado", "que bom você estar de olho"). Faça o mesmo com ${pessoa} (ele/ela, atento/atenta) usando o relacionamento e o nome, e nunca presuma que quem pergunta é mulher.
9) Varie as aberturas das respostas. Se quiser, use no máximo um 💜, e só de vez em quando.
Responda APENAS com JSON: {"resposta":string,"anotacao":null|{"titulo":string (até 6 palavras),"texto":string,"para":string|null}}
DADOS: ${JSON.stringify(dados)}`;
      const texto = await claude(MODELO_CONVERSA, historico, sistema, 700);
      let resultado: any; try { resultado = extrairJSON(texto); } catch { resultado = { resposta: texto, anotacao: null }; }
      await admin.rpc("registrar_uso_ia", { p_user: dono, p_tipo: "pergunta" });
      return json({ resultado });
    }

    if (tarefa === "resumo") {
      if (!plus) return json({ erro: "limite", motivo: "relatorio" }, 402);
      const dados = await dadosDaFamilia(usuario, dono, String(corpo.membro || ""));
      const mes = mesAtual();
      const regs = dados.registros.filter((r: any) => String(r.data).startsWith(mes));
      const { data: notas } = await usuario.from("notas_consulta").select("titulo,texto,para").eq("user_id", dono).eq("feito", false).limit(10);
      const prompt = `Escreva em português do Brasil um resumo curto (até 170 palavras) do mês de ${dados.pessoa_cuidada?.nome || ""}, para ${dados.quem_pergunta.nome || "a família"} levar aos profissionais. Tom acolhedor e objetivo. Chame as pessoas pelo nome. Organize em: Presença nas terapias; Como foram os dias; Conquistas; Pontos para conversar. Sem diagnósticos nem recomendações clínicas. Use só os dados abaixo.
Tratamentos: ${JSON.stringify(dados.tratamentos)}\nConsultas: ${JSON.stringify(dados.consultas)}
Sessões do mês (marcadas): ${JSON.stringify(corpo.sessoes ?? [])}
Registros do mês: ${JSON.stringify(regs)}
Anotações pendentes para a consulta: ${JSON.stringify(notas ?? [])}`;
      const texto = await claude(MODELO_CONVERSA, [{ role: "user", content: prompt }], undefined, 700);
      await admin.rpc("registrar_uso_ia", { p_user: dono, p_tipo: "resumo" });
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
