# Gera web/index.html a partir do protótipo, trocando a camada de dados/IA pelo Supabase.
import re, sys
import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, ICONS, OUT = (sys.argv[1:4] if len(sys.argv) > 3 else [os.path.join(RAIZ, 'src', 'app.template.html'), os.path.join(RAIZ, 'src', 'icons.json'), os.path.join(RAIZ, 'web', 'index.html')])
s = open(SRC, encoding='utf-8').read()
def rep(a, b, cnt=1):
    global s
    assert a in s, "MISS: " + a[:90]
    s = s.replace(a, b, cnt)

# head
rep('<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="theme-color" content="#ffffff">\n<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n<script src="config.js"></script>')

# ---------- camada de dados ----------
a = s.index('const CL = (window.claude'); b = s.index('/* ---------- Navegação ---------- */')
s = s[:a] + r'''const CFG = window.TEIA_CONFIG || {};
const SB = (window.supabase && CFG.SUPABASE_URL && CFG.SUPABASE_ANON_KEY) ? window.supabase.createClient(CFG.SUPABASE_URL, CFG.SUPABASE_ANON_KEY, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } }) : null;
let USER = null, MODO_DEMO = !SB, SAMPLE = SB ? {} : null, SAMPLE_IMG = !!SB;
const nul = v => (v === "" || v === undefined ? null : v);
/* coleção do app -> tabela do banco */
const MAPA = {
  meds: ["medicamentos", m => ({ membro_id: nul(m.membroId), nome: m.nome, dose: m.dose || "", horarios: m.horarios || [], inicio: nul(m.inicio), fim: nul(m.fim), receita_id: nul(m.receitaId), medico: m.medico || "" }),
         r => ({ id: r.id, membroId: r.membro_id || "", nome: r.nome, dose: r.dose, horarios: r.horarios || [], inicio: r.inicio || "", fim: r.fim || "", receitaId: r.receita_id || "", medico: r.medico })],
  trat: ["tratamentos", t => ({ membro_id: nul(t.membroId), tipo: t.tipo, profissional: t.profissional || "", local: t.local || "", dias: t.dias || [], hora: t.hora || "", meta: t.meta || "", progresso: Number(t.progresso || 0) }),
         r => ({ id: r.id, membroId: r.membro_id || "", tipo: r.tipo, profissional: r.profissional, local: r.local, dias: r.dias || [], hora: r.hora, meta: r.meta, progresso: r.progresso })],
  tarefas: ["tarefas", t => ({ membro_id: nul(t.membroId), titulo: t.titulo, dias: t.dias || [], hora: t.hora || "" }), r => ({ id: r.id, membroId: r.membro_id || "", titulo: r.titulo, dias: r.dias || [], hora: r.hora })],
  docs: ["documentos", d => ({ membro_id: nul(d.membroId), tipo: d.tipo || "outro", titulo: d.titulo || "", data: nul(d.data), profissional: d.profissional || "", registro: d.registro || "", especialidade: d.especialidade || "", origem: d.origem || "", resumo: d.resumo || "", pontos: d.pontos || [], termos: d.termos || [], recomendacoes: d.recomendacoes || [], perguntas: d.perguntas || [], medicamentos: d.medicamentos || [], arquivos: d.assetIds || [], mime: d.mime || "", lido_por_ia: !!d.resumo }),
         r => ({ id: r.id, membroId: r.membro_id || "", tipo: r.tipo, titulo: r.titulo, data: r.data || "", profissional: r.profissional, registro: r.registro, especialidade: r.especialidade, origem: r.origem, resumo: r.resumo, pontos: r.pontos, termos: r.termos, recomendacoes: r.recomendacoes, perguntas: r.perguntas, medicamentos: r.medicamentos, assetIds: r.arquivos || [], assetId: (r.arquivos || [])[0] || null, mime: r.mime, criadoEm: r.criado_em })],
  regs: ["registros", x => ({ membro_id: nul(x.membroId), data: x.data, humor: Number(x.humor || 3), sono: x.sono || "", crise: !!x.crise, tratamento_id: nul(x.tratId), conquista: x.conquista || "", nota: x.nota || "" }),
         r => ({ id: r.id, membroId: r.membro_id || "", data: r.data, humor: r.humor, sono: r.sono, crise: r.crise, tratId: r.tratamento_id || "", conquista: r.conquista, nota: r.nota })],
  rede: ["rede", x => ({ nome: x.nome, papel: x.papel || "", contato: x.contato || "", obs: x.obs || "" }), r => ({ id: r.id, nome: r.nome, papel: r.papel, contato: r.contato, obs: r.obs })],
  notas: ["notas_consulta", n => ({ membro_id: nul(n.membroId), data: n.data, titulo: n.titulo, texto: n.texto, para: n.para || "", feito: !!n.feito, origem: n.origem || "manual", pergunta: n.pergunta || "" }),
          r => ({ id: r.id, membroId: r.membro_id || "", data: r.data, titulo: r.titulo, texto: r.texto, para: r.para, feito: r.feito, origem: r.origem, pergunta: r.pergunta })],
  consultas: ["consultas", c => ({ membro_id: nul(c.membroId), titulo: c.titulo, data: c.data, hora: c.hora || "", profissional: c.profissional || "", local: c.local || "", obs: c.obs || "" }),
          r => ({ id: r.id, membroId: r.membro_id || "", titulo: r.titulo, data: r.data, hora: r.hora, profissional: r.profissional, local: r.local, obs: r.obs })],
  membros: ["membros", m => ({ nome: m.nome, relacao: m.relacao || "", nascimento: nul(m.nascimento), diagnosticos: m.diagnosticos || "", plano_saude: m.plano || "", foto: m.foto || null }),
          r => ({ id: r.id, nome: r.nome, relacao: r.relacao, nascimento: r.nascimento || "", diagnosticos: r.diagnosticos, plano: r.plano_saude, foto: r.foto || "" })],
};
const SINC = {}; const filas = {};
function linhasDe(nome) {
  if (nome === "checks") { const out = new Map(); for (const [dia, ks] of Object.entries(S.checks.d || {})) for (const [chave, q] of Object.entries(ks || {})) out.set(dia + "|" + chave, { dia, chave, por: (q && q.by) || "", hora: (q && q.at) || "" }); return out; }
  const [, para] = MAPA[nome]; const out = new Map(); for (const it of (POR_MEMBRO.includes(nome) ? ALL[nome] : S[nome].items)) { if (!it.id) it.id = uid(); out.set(it.id, { id: it.id, ...para(it) }); } return out;
}
async function sincronizar(nome) {
  if (nome === "plano") return;
  if (nome === "perfil") { if (!S.perfil) return; const p = S.perfil; const { error } = await SB.from("perfis").upsert({ user_id: USER.id, mae: p.mae || "", papel: p.papel || "", crianca: p.crianca || "", nascimento: nul(p.nascimento), diagnosticos: p.diagnosticos || "", plano_saude: p.plano || "", foto: p.foto || null, consentimento_em: p.consentEm || null }); if (error) throw error; return; }
  const tabela = nome === "checks" ? "marcacoes" : MAPA[nome][0];
  const atual = linhasDe(nome), antes = SINC[nome] || new Map();
  const mudou = [...atual].filter(([k, v]) => antes.get(k) !== JSON.stringify(v)).map(([, v]) => ({ ...v, user_id: USER.id }));
  const sairam = [...antes.keys()].filter(k => !atual.has(k));
  if (mudou.length) { const { error } = await SB.from(tabela).upsert(mudou, nome === "checks" ? { onConflict: "user_id,dia,chave" } : undefined); if (error) throw error; }
  if (sairam.length) {
    if (nome === "checks") { for (const k of sairam) { const [dia, chave] = [k.slice(0, 10), k.slice(11)]; const { error } = await SB.from("marcacoes").delete().match({ dia, chave }); if (error) throw error; } }
    else { const { error } = await SB.from(tabela).delete().in("id", sairam); if (error) throw error; }
  }
  SINC[nome] = new Map([...atual].map(([k, v]) => [k, JSON.stringify(v)]));
}
function salvar(nome) {
  if (!SB || !USER) return Promise.resolve();
  const p = (filas[nome] || Promise.resolve()).catch(() => {}).then(() => sincronizar(nome)).catch(e => { console.error("salvar", nome, e); if (e && /teia_plus_necessario/.test(e.message || "")) { paywall(e.hint || (nome === "rede" ? "rede" : "membro")); } else toast("Não consegui salvar agora. Confira sua internet."); throw e; });
  filas[nome] = p; return p;
}
async function carregar() {
  const pega = t => SB.from(t).select("*");
  const [perfil, assin, uso, ...cols] = await Promise.all([
    SB.from("perfis").select("*").maybeSingle(), SB.from("assinaturas").select("*").maybeSingle(), SB.from("uso_ia").select("*").eq("mes", mesAtual()).maybeSingle(),
    ...Object.values(MAPA).map(([t]) => pega(t)), SB.from("marcacoes").select("dia,chave,por,hora").gte("dia", iso(addDays(new Date(), -150)))]);
  const err = [perfil, assin, uso, ...cols].find(r => r.error); if (err) throw err.error;
  const r = perfil.data; S.perfil = r ? { mae: r.mae, papel: r.papel || "", crianca: r.crianca, nascimento: r.nascimento || "", diagnosticos: r.diagnosticos, plano: r.plano_saude, foto: r.foto || "", consent: !!r.consentimento_em, consentEm: r.consentimento_em } : null;
  Object.keys(MAPA).forEach((n, i) => { S[n] = { items: (cols[i].data || []).map(MAPA[n][2]) }; });
  S.checks = { d: {} }; for (const m of cols[cols.length - 1].data || []) { (S.checks.d[m.dia] = S.checks.d[m.dia] || {})[m.chave] = { by: m.por, at: m.hora }; }
  prepararMembros();
  aplicarPlano(assin.data, uso.data);
  for (const n of [...Object.keys(MAPA), "checks"]) SINC[n] = new Map([...linhasDe(n)].map(([k, v]) => [k, JSON.stringify(v)]));
  if (S.membros.items.length && !(cols[Object.keys(MAPA).indexOf("membros")].data || []).length) { SINC.membros = new Map(); salvar("membros").catch(() => {}); }
  carregarConteudos();
}
function aplicarPlano(a, u) { S.plano = { plus: !!a && a.plano === "plus" && ["ativa", "teste"].includes(a.status), ciclo: a && a.ciclo, desde: a && a.desde, uso: { [mesAtual()]: { leitura: (u && u.leituras) || 0, pergunta: (u && u.perguntas) || 0 } } }; }
async function atualizarPlano() { if (!SB || !USER) return; const [a, u] = await Promise.all([SB.from("assinaturas").select("*").maybeSingle(), SB.from("uso_ia").select("*").eq("mes", mesAtual()).maybeSingle()]); aplicarPlano(a.data, u.data); }
async function carregarConteudos() {
  try { const { data } = await SB.from("conteudos").select("id,categoria,titulo,minutos,autor,corpo,destaque,publicado_em").eq("publicado", true).order("destaque", { ascending: false }).order("publicado_em", { ascending: false });
    if (data && data.length) { CONTEUDOS.splice(0, CONTEUDOS.length, ...data.map(c => ({ id: c.id, cat: c.categoria, titulo: c.titulo, min: c.minutos, autor: c.autor, corpo: (c.corpo || []).map(b => b.p != null ? b.p : b.h != null ? ["h", b.h] : ["ul", b.ul || []]) }))); if (["conteudos", "inicio"].includes(TELA.nome)) render(); } } catch (e) {}
}
/* IA no servidor (Edge Function "ia") */
async function ia(tarefa, dados) {
  const { data, error } = await SB.functions.invoke("ia", { body: { tarefa, ...dados } });
  if (error) { const st = error.context && error.context.status; let b = {}; try { b = await error.context.json(); } catch (e) {} const er = new Error(b.erro || "falha"); er.code = st === 402 ? "limite" : (b.erro === "limite_plus" || b.erro === "limite_dia" || b.erro === "servico_ocupado") ? b.erro : st === 429 ? "rate_limited" : (b.erro || "falha"); er.motivo = b.motivo; throw er; }
  return data.resultado;
}
const MSG_LIMITE = (c, t) => c === "limite_plus" ? (t === "leitura" ? "Você usou as 30 leituras deste mês. Elas voltam no mês que vem." : t === "resumo" ? "Você chegou ao limite de resumos deste mês. Volta no mês que vem." : "Você usou as 300 perguntas deste mês. Elas voltam no mês que vem.")
  : c === "limite_dia" ? (t === "leitura" ? "Você chegou ao limite de leituras de hoje. Volte amanhã." : t === "resumo" ? "Você chegou ao limite de resumos de hoje. Volte amanhã." : "Você chegou ao limite de perguntas de hoje. Volte amanhã.")
  : c === "servico_ocupado" ? "A teIA está muito concorrida agora. Tente de novo daqui a pouco." : "";
const blobParaDataURL = b => new Promise((ok, erro) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.onerror = erro; fr.readAsDataURL(b); });
let ENTRANDO = false;
async function iniciar() {
  { const lm = document.getElementById("loadmark"); if (lm) lm.innerHTML = simbolo(64); }
  if (!SB) { go(S.perfil ? "inicio" : "boasvindas", {}, true); return; }
  SB.auth.onAuthStateChange((ev, sess) => { if (sess && sess.user && ["SIGNED_IN", "USER_UPDATED", "TOKEN_REFRESHED"].includes(ev)) { const novo = !USER || USER.id !== sess.user.id; USER = sess.user; if (novo && ev === "SIGNED_IN") entrou(); else if (ev === "USER_UPDATED" && TELA.nome === "conta") render(); } if (ev === "SIGNED_OUT") { USER = null; go("boasvindas", {}, true); } });
  const { data } = await SB.auth.getSession();
  if (data && data.session) { USER = data.session.user; await entrou(); } else go("boasvindas", {}, true);
}
async function entrou() {
  if (ENTRANDO) return; ENTRANDO = true;
  try { await carregar(); if (!S.perfil) { const m = USER.user_metadata || {}; const nome = m.given_name || String(m.full_name || m.name || "").trim().split(" ")[0]; if (nome && !CAD.mae) CAD.mae = nome; } go(S.perfil ? "inicio" : "cadastro", S.perfil ? {} : { step: 1, novo: true }, true); }
  catch (e) { console.error(e); toast("Não consegui carregar seus dados. Tente de novo."); go("boasvindas", {}, true); }
  finally { ENTRANDO = false; }
}
const LOGIN_EMAIL = true; // desligue (false) para mostrar só o Google
const pendenteConvite = () => { try { return !!localStorage.getItem("teia.convite"); } catch (e) { return false; } };
let RELOGIO_REENVIO = null;
function esperarReenvio() { clearInterval(RELOGIO_REENVIO); let t = 30; const atualiza = () => { const b = document.getElementById("reenviar"); if (!b || TELA.nome !== "entrar") { clearInterval(RELOGIO_REENVIO); return; } b.disabled = t > 0; b.textContent = t > 0 ? `Reenviar código (${t}s)` : "Reenviar código"; t--; }; atualiza(); RELOGIO_REENVIO = setInterval(atualiza, 1000); }
async function sair() { await SB.auth.signOut().catch(() => {}); for (const k of Object.keys(SINC)) delete SINC[k]; S.perfil = null; for (const n of Object.keys(MAPA)) S[n] = { items: [] }; S.checks = { d: {} }; CHAT = []; USER = null; go("boasvindas", {}, true); }

''' + s[b:]

# banner do modo de teste
rep('Modo de teste: os dados não ficam salvos nesta visualização.', 'Modo de demonstração: os dados não estão sendo salvos agora.')

# tela de entrar
rep("const CAD = {};", r'''TELAS.entrar = (p) => `${topo("Entrar com e-mail")}
<div class="wrap stack" style="padding-top:16px;gap:16px">
  <div style="display:flex;justify-content:center;padding:8px 0 4px">${logo(40)}</div>
  ${p.enviado ? `<div class="card stack" style="gap:8px;text-align:center;padding:24px 16px"><span class="ib" style="margin:0 auto">${ic("feito", 20)}</span><p class="b" style="font-size:17px">Confira seu e-mail</p><p class="small muted">Enviamos um código de 6 números para <b>${esc(p.email)}</b>. Digite abaixo. Se não achar, olhe o spam.</p></div>
    <form class="stack" data-f="codigo"><input class="input" name="codigo" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" required placeholder="000000" style="text-align:center;font-size:24px;letter-spacing:8px"><button class="btn full" type="submit">Entrar</button></form>
    <button class="btn sec full" data-a="reenviar" data-v="${esc(p.email)}" id="reenviar" disabled>Reenviar código</button>
    <button class="link" style="align-self:center" data-a="entrar-de-novo">Usar outro e-mail</button>`
  : `<div class="stack" style="gap:4px;text-align:center"><h1 style="font-size:24px">Qual é o seu e-mail?</h1><p class="muted small">Sem senha: enviamos um código para você entrar.</p></div>
  <form class="stack" data-f="entrar"><label class="f">E-mail<input class="input" type="email" name="email" autocomplete="email" inputmode="email" autocapitalize="none" required placeholder="voce@email.com" value="${esc(p.email || "")}"></label><button class="btn full" type="submit">Enviar código</button></form>`}
  <p class="xs muted" style="text-align:center;line-height:1.5">Ao entrar, você concorda em guardar na sua conta os dados de saúde de quem você cuida. Eles ficam privados e você pode apagar quando quiser.</p>
</div>`;

const CAD = {};''')
rep('<button class="btn full" data-a="cad-ir" data-v="1">Começar ${ic("seta-dir", 18)}</button>',
    '${SB ? `${pendenteConvite() ? `<div class="card row" style="gap:12px;margin-bottom:12px"><span class="ib c2">${ic("rede", 20)}</span><p class="small grow">Você recebeu um convite para cuidar junto. Entre para aceitar.</p></div>` : ""}<div class="stack" style="gap:12px"><button class="btn gbtn full" data-a="entrar-google">${GOOGLE_G}Continuar com Google</button>${LOGIN_EMAIL ? `<button class="btn full" data-a="ir" data-v="entrar">Continuar com e-mail</button>` : ""}</div>` : `<button class="btn full" data-a="cad-ir" data-v="1">Começar ${ic("seta-dir", 18)}</button>`}')
rep('    case "cad-ir": ', '    case "cad-ir": if (SB && !USER) { go("entrar"); break; } ')
rep('    case "voltar": voltar(); break;', '    case "voltar": voltar(); break;\n    case "entrar-de-novo": TELA.p = {}; render(); break;\n    case "entrar-google": { const volta = location.origin + location.pathname; const { error } = USER && USER.is_anonymous ? await SB.auth.linkIdentity({ provider: "google", options: { redirectTo: volta } }) : await SB.auth.signInWithOAuth({ provider: "google", options: { redirectTo: volta, queryParams: { prompt: "select_account" } } }); if (error) toast(/already|exists/i.test(error.message || "") ? "Essa conta Google já tem um cadastro. Saia e entre com ela." : "Não consegui abrir o Google agora. Tente com o e-mail."); break; }\n    case "reenviar": { const email = v; const { error } = TELA.p && TELA.p.converter ? await SB.auth.updateUser({ email }) : await SB.auth.signInWithOtp({ email, options: { emailRedirectTo: location.origin + location.pathname } }); toast(error ? (error.status === 429 ? "Muitas tentativas. Espere um minuto." : "Não consegui reenviar. Tente de novo.") : "Código enviado de novo."); if (!error) esperarReenvio(); break; }\n    case "sair": confirmar("Sair da conta?", "Seus dados continuam guardados. Para voltar, é só entrar com a mesma conta.", "Sair", sair); break;\n    case "ver-original": { const w = window.open("", "_blank"); const { data, error } = await SB.storage.from("documentos").createSignedUrl(v, 300); if (error || !data) { if (w) w.close(); toast("Não consegui abrir o arquivo."); } else if (w) w.location = data.signedUrl; else location.href = data.signedUrl; break; }')
rep('const SEM_DOCK = ["tour","teiaplus",', 'const SEM_DOCK = ["tour","entrar","boasvindas","teiaplus",')
rep('    if (tipo === "cad") {', r'''    if (tipo === "codigo") { const email = TELA.p.email, token = g("codigo").replace(/\D/g, ""); const { error } = await SB.auth.verifyOtp({ email, token, type: TELA.p.converter ? "email_change" : "email" }); if (error) { toast(/expired|invalid/i.test(error.message || "") ? "Código errado ou vencido. Confira ou peça outro." : "Não consegui entrar. Tente de novo."); return; } if (TELA.p.converter) { toast("Conta salva! Seus dados continuam aqui."); await SB.auth.refreshSession(); go("perfil", {}, true); } return; }
    if (tipo === "conta-email" || tipo === "entrar-email") { const email = g("email").toLowerCase(), converter = tipo === "conta-email"; const { error } = converter && USER && USER.is_anonymous ? await SB.auth.updateUser({ email }) : await SB.auth.signInWithOtp({ email, options: { emailRedirectTo: location.origin + location.pathname } }); if (error) { toast(error.status === 429 ? "Muitos e-mails em pouco tempo. Espere um minuto." : "Não consegui enviar o código. Confira o e-mail."); return; } go("entrar", { enviado: true, email, converter: converter && !!(USER && USER.is_anonymous) }); esperarReenvio(); return; }
    if (tipo === "entrar") { const email = g("email").toLowerCase(); const { error } = await SB.auth.signInWithOtp({ email, options: { emailRedirectTo: location.origin + location.pathname } }); if (error) { toast(error.status === 429 ? "Muitos e-mails em pouco tempo. Espere um minuto e tente de novo." : /invalid|valid/i.test(error.message || "") ? "Esse e-mail não parece certo. Confira." : "Não consegui enviar o código. Tente de novo."); return; } TELA.p = { enviado: true, email }; render(); esperarReenvio(); return; }
    if (tipo === "cad") {''')
# após cadastro, recarrega sincronização base
# arquivos originais -> Storage
rep('async function guardarArquivos(files) { if (!ASSETS) return [];', 'async function guardarArquivos(files) { if (!SB || !USER) return [];')
s = re.sub(r'const a = await ASSETS\.upload\(f\); if \(a && a\.id\) ids\.push\(a\.id\);',
           'const ext = (f.name.match(/\\.[a-z0-9]+$/i) || [""])[0].toLowerCase(); const caminho = `${USER.id}/${uid()}${ext}`; const { error } = await SB.storage.from("documentos").upload(caminho, f, { contentType: f.type || undefined, upsert: false }); if (error) throw error; ids.push(caminho);', s, count=1)
assert 'SB.storage.from("documentos").upload' in s
rep('`<a class="btn sec grow" href="/_blob/${esc(a)}" target="_blank" rel="noopener">${arr.length > 1 ? "Página " + (i + 1) : "Ver original"}</a>`',
    '`<button class="btn sec grow" data-a="ver-original" data-v="${esc(a)}">${arr.length > 1 ? "Página " + (i + 1) : "Ver original"}</button>`')
# leitura com IA
a = s.index('async function lerComIA(tipo, imgs) {'); b = s.index('\n', a)
s = s[:a] + 'async function lerComIA(tipo, imgs) { const imagens = await Promise.all(imgs.slice(0, 4).map(blobParaDataURL)); return await ia(tipo, { imagens }); }' + s[b:]
rep('const r = await lerComIA(tipo, imgs); contarUso("leitura");', 'const r = await lerComIA(tipo, imgs); contarUso("leitura"); atualizarPlano().catch(() => {});')
rep('} catch (err) { clearInterval(relogio); toast(err && err.code === "rate_limited"', '} catch (err) { clearInterval(relogio); if (err && err.code === "limite") { SCAN = null; paywall(err.motivo || "leitura", { tipo }); return; } toast(err && MSG_LIMITE(err.code, "leitura") ? MSG_LIMITE(err.code, "leitura") : err && err.code === "rate_limited"')
# assistente
rep('const r = await SAMPLE(msgs, { modelTier: "default", cache: false }); contarUso("pergunta");',
    'const r = { text: JSON.stringify(await ia("pergunta", { membro: ATIVO, historico: hist.map(m => ({ role: m.role, content: m.content })) })) }; contarUso("pergunta"); atualizarPlano().catch(() => {});')
rep('} catch (e) { ult().content = e && e.code === "rate_limited"', '} catch (e) { if (e && e.code === "limite") { CHAT.splice(-2, 2); paywall(e.motivo || "pergunta"); return; } ult().content = e && MSG_LIMITE(e.code, "pergunta") ? MSG_LIMITE(e.code, "pergunta") : e && e.code === "rate_limited"')
# resumo
rep('try { const r = await SAMPLE(prompt, { modelTier: "default", onText: ({ text }) => { const el = document.getElementById("reltxt"); if (el) el.textContent = text; } }); const el = document.getElementById("reltxt"); if (el && r.text) el.textContent = r.text; }',
    'try { const r = await ia("resumo", { membro: ATIVO, sessoes: sess }); const el = document.getElementById("reltxt"); if (el && r && r.texto) el.textContent = r.texto; }')
rep('catch (err) { out.innerHTML = `<p class="banner">${err && err.code === "rate_limited"', 'catch (err) { if (err && err.code === "limite") { paywall("relatorio"); return; } out.innerHTML = `<p class="banner">${err && MSG_LIMITE(err.code, "resumo") ? MSG_LIMITE(err.code, "resumo") : err && err.code === "rate_limited"')
# teia+ via servidor
rep('    case "plus-assinar": S.plano = { ...S.plano, plus: true, ciclo: v, desde: iso(new Date()) }; await salvar("plano").catch(() => {}); voltar(); toast("Boas-vindas ao teia+!"); break;',
    '    case "plus-assinar": if (SB) { const { error } = await SB.functions.invoke("assinatura", { body: { acao: "assinar", ciclo: v } }); if (error) { toast("O pagamento ainda não está disponível."); break; } await atualizarPlano(); } else S.plano = { ...S.plano, plus: true, ciclo: v, desde: iso(new Date()) }; voltar(); toast("Boas-vindas ao teia+!"); break;')
rep('    case "plus-cancelar": S.plano = { ...S.plano, plus: false }; await salvar("plano").catch(() => {}); render(); toast("Assinatura cancelada (teste)."); break;',
    '    case "plus-cancelar": if (SB) { const { error } = await SB.functions.invoke("assinatura", { body: { acao: "cancelar" } }); if (error) { toast("Não consegui cancelar agora."); break; } await atualizarPlano(); } else S.plano = { ...S.plano, plus: false }; render(); toast("Assinatura cancelada."); break;')
# apagar tudo
a = s.index('    case "apagar-tudo":'); b = s.index('\n', a)
s = s[:a] + r'''    case "apagar-tudo": confirmar("Apagar todos os dados?", "Perfil, rotina, tratamentos, documentos, arquivos e registros serão apagados. Não dá para desfazer.", "Apagar tudo", async () => {
      if (SB && USER) { try { const { data: arqs } = await SB.storage.from("documentos").list(USER.id, { limit: 1000 }); if (arqs && arqs.length) await SB.storage.from("documentos").remove(arqs.map(f => `${USER.id}/${f.name}`));
        for (const t of ["marcacoes", ...Object.values(MAPA).map(m => m[0]).filter(t => t !== "membros"), "membros", "perfis"]) { const { error } = await SB.from(t).delete().eq("user_id", USER.id); if (error) throw error; } } catch (e) { toast("Não consegui apagar tudo. Tente de novo."); return; } }
      for (const k of Object.keys(SINC)) delete SINC[k]; S.perfil = null; for (const n of Object.keys(MAPA)) S[n] = { items: [] }; S.checks = { d: {} }; CHAT = []; go(SB ? "cadastro" : "boasvindas", SB ? { step: 1, novo: true } : {}, true); toast("Tudo apagado."); }); break;''' + s[b:]
# sair no perfil
rep('  <button class="btn danger full" data-a="apagar-tudo">', '  ${SB && USER ? `<button class="btn sec full" data-a="sair">Sair da conta</button><p class="xs muted" style="text-align:center;margin-top:-4px">${esc(USER.email || "")}</p>` : ""}\n  <button class="btn danger full" data-a="apagar-tudo">')
rep('<p class="xs muted">versão de teste</p>', '<p class="xs muted">${SB ? "versão beta" : "demonstração"}</p>')
# contarUso: o servidor é a fonte, só atualiza a tela
rep('salvar("plano").catch(() => {}); }', '}')
# remove protótipo leftovers
s = s.replace('<p class="xs muted" style="text-align:center;line-height:1.5">${pl === "anual" ? "Depois dos 7 dias, R$ 149,00 por ano. Cancele antes e não paga nada." : "Renova todo mês. Cancele quando quiser."}<br>Protótipo: nenhuma cobrança é feita.</p>',
              '<p class="xs muted" style="text-align:center;line-height:1.5">${pl === "anual" ? "Depois dos 7 dias, R$ 149,00 por ano. Cancele antes e não paga nada." : "Renova todo mês. Cancele quando quiser."}<br>Versão beta: nenhuma cobrança é feita ainda.</p>')

# ---------- conta: pessoa sem conta (acesso antigo) e banner ----------
def rep2(a, b):
    global s
    assert a in s, "MISS2: " + a[:90]
    s = s.replace(a, b, 1)
rep2('${SB && USER ? `<button class="btn sec full" data-a="sair">Sair da conta</button>', '${SB && USER && !USER.is_anonymous ? `<button class="btn sec full" data-a="sair">Sair da conta</button>')
rep2('<p class="xs muted" style="text-align:center;margin-top:-4px">${esc(USER.email || "")}</p>` : ""}', '<p class="xs muted" style="text-align:center;margin-top:-4px">${esc(USER.email || "")}</p>` : ""}${SB && USER && USER.is_anonymous ? `<button class="card row" data-a="ir" data-v="conta" style="border:none;width:100%;text-align:left;gap:12px;font-family:inherit;color:var(--ink)"><span class="ib c2">${ic("privacidade", 20)}</span><span class="grow"><b style="display:block;font-size:14px">Salve sua conta</b><span class="xs muted">Hoje seus dados estão só neste aparelho. Entre com Google ou e-mail para não perder nada.</span></span>${ic("seta", 16)}</button>` : ""}')

exec(open(os.path.join(RAIZ, 'scripts', 'nuvem_patch.py'), encoding='utf-8').read())
s = s.replace('/*__ICONS__*/', open(ICONS, encoding='utf-8').read())
for bad in ["DB.doc", "ASSETS.", "CL.use", "SAMPLE(", "SAMPLE.json", "/_blob/"]:
    assert bad not in s, "sobrou: " + bad
open(OUT, 'w', encoding='utf-8').write(s)
print("ok", len(s))
