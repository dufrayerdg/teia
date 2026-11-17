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
  meds: ["medicamentos", m => ({ nome: m.nome, dose: m.dose || "", horarios: m.horarios || [], inicio: nul(m.inicio), fim: nul(m.fim), receita_id: nul(m.receitaId), medico: m.medico || "" }),
         r => ({ id: r.id, nome: r.nome, dose: r.dose, horarios: r.horarios || [], inicio: r.inicio || "", fim: r.fim || "", receitaId: r.receita_id || "", medico: r.medico })],
  trat: ["tratamentos", t => ({ tipo: t.tipo, profissional: t.profissional || "", local: t.local || "", dias: t.dias || [], hora: t.hora || "", meta: t.meta || "", progresso: Number(t.progresso || 0) }),
         r => ({ id: r.id, tipo: r.tipo, profissional: r.profissional, local: r.local, dias: r.dias || [], hora: r.hora, meta: r.meta, progresso: r.progresso })],
  tarefas: ["tarefas", t => ({ titulo: t.titulo, dias: t.dias || [], hora: t.hora || "" }), r => ({ id: r.id, titulo: r.titulo, dias: r.dias || [], hora: r.hora })],
  docs: ["documentos", d => ({ tipo: d.tipo || "outro", titulo: d.titulo || "", data: nul(d.data), profissional: d.profissional || "", registro: d.registro || "", especialidade: d.especialidade || "", origem: d.origem || "", resumo: d.resumo || "", pontos: d.pontos || [], termos: d.termos || [], recomendacoes: d.recomendacoes || [], perguntas: d.perguntas || [], medicamentos: d.medicamentos || [], arquivos: d.assetIds || [], mime: d.mime || "", lido_por_ia: !!d.resumo }),
         r => ({ id: r.id, tipo: r.tipo, titulo: r.titulo, data: r.data || "", profissional: r.profissional, registro: r.registro, especialidade: r.especialidade, origem: r.origem, resumo: r.resumo, pontos: r.pontos, termos: r.termos, recomendacoes: r.recomendacoes, perguntas: r.perguntas, medicamentos: r.medicamentos, assetIds: r.arquivos || [], assetId: (r.arquivos || [])[0] || null, mime: r.mime, criadoEm: r.criado_em })],
  regs: ["registros", x => ({ data: x.data, humor: Number(x.humor || 3), sono: x.sono || "", crise: !!x.crise, tratamento_id: nul(x.tratId), conquista: x.conquista || "", nota: x.nota || "" }),
         r => ({ id: r.id, data: r.data, humor: r.humor, sono: r.sono, crise: r.crise, tratId: r.tratamento_id || "", conquista: r.conquista, nota: r.nota })],
  rede: ["rede", x => ({ nome: x.nome, papel: x.papel || "", contato: x.contato || "", obs: x.obs || "" }), r => ({ id: r.id, nome: r.nome, papel: r.papel, contato: r.contato, obs: r.obs })],
  notas: ["notas_consulta", n => ({ data: n.data, titulo: n.titulo, texto: n.texto, para: n.para || "", feito: !!n.feito, origem: n.origem || "manual", pergunta: n.pergunta || "" }),
          r => ({ id: r.id, data: r.data, titulo: r.titulo, texto: r.texto, para: r.para, feito: r.feito, origem: r.origem, pergunta: r.pergunta })],
};
const SINC = {}; const filas = {};
function linhasDe(nome) {
  if (nome === "checks") { const out = new Map(); for (const [dia, ks] of Object.entries(S.checks.d || {})) for (const [chave, q] of Object.entries(ks || {})) out.set(dia + "|" + chave, { dia, chave, por: (q && q.by) || "", hora: (q && q.at) || "" }); return out; }
  const [, para] = MAPA[nome]; const out = new Map(); for (const it of S[nome].items) { if (!it.id) it.id = uid(); out.set(it.id, { id: it.id, ...para(it) }); } return out;
}
async function sincronizar(nome) {
  if (nome === "plano") return;
  if (nome === "perfil") { if (!S.perfil) return; const p = S.perfil; const { error } = await SB.from("perfis").upsert({ user_id: USER.id, mae: p.mae || "", crianca: p.crianca || "", nascimento: nul(p.nascimento), diagnosticos: p.diagnosticos || "", plano_saude: p.plano || "", consentimento_em: p.consentEm || null }); if (error) throw error; return; }
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
  const p = (filas[nome] || Promise.resolve()).catch(() => {}).then(() => sincronizar(nome)).catch(e => { console.error("salvar", nome, e); toast("Não consegui salvar agora. Confira sua internet."); throw e; });
  filas[nome] = p; return p;
}
async function carregar() {
  const pega = t => SB.from(t).select("*");
  const [perfil, assin, uso, ...cols] = await Promise.all([
    SB.from("perfis").select("*").maybeSingle(), SB.from("assinaturas").select("*").maybeSingle(), SB.from("uso_ia").select("*").eq("mes", mesAtual()).maybeSingle(),
    ...Object.values(MAPA).map(([t]) => pega(t)), SB.from("marcacoes").select("dia,chave,por,hora").gte("dia", iso(addDays(new Date(), -150)))]);
  const err = [perfil, assin, uso, ...cols].find(r => r.error); if (err) throw err.error;
  const r = perfil.data; S.perfil = r ? { mae: r.mae, crianca: r.crianca, nascimento: r.nascimento || "", diagnosticos: r.diagnosticos, plano: r.plano_saude, consent: !!r.consentimento_em, consentEm: r.consentimento_em } : null;
  Object.keys(MAPA).forEach((n, i) => { S[n] = { items: (cols[i].data || []).map(MAPA[n][2]) }; });
  S.checks = { d: {} }; for (const m of cols[cols.length - 1].data || []) { (S.checks.d[m.dia] = S.checks.d[m.dia] || {})[m.chave] = { by: m.por, at: m.hora }; }
  aplicarPlano(assin.data, uso.data);
  for (const n of [...Object.keys(MAPA), "checks"]) SINC[n] = new Map([...linhasDe(n)].map(([k, v]) => [k, JSON.stringify(v)]));
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
  if (error) { const st = error.context && error.context.status; let b = {}; try { b = await error.context.json(); } catch (e) {} const er = new Error(b.erro || "falha"); er.code = st === 402 ? "limite" : st === 429 ? "rate_limited" : (b.erro || "falha"); er.motivo = b.motivo; throw er; }
  return data.resultado;
}
const blobParaDataURL = b => new Promise((ok, erro) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.onerror = erro; fr.readAsDataURL(b); });
let ENTRANDO = false;
async function iniciar() {
  { const lm = document.getElementById("loadmark"); if (lm) lm.innerHTML = simbolo(64); }
  if (!SB) { go(S.perfil ? "inicio" : "boasvindas", {}, true); return; }
  SB.auth.onAuthStateChange((ev, sess) => { if (ev === "SIGNED_IN" && sess && (!USER || USER.id !== sess.user.id)) { USER = sess.user; entrou(); } if (ev === "SIGNED_OUT") { USER = null; go("boasvindas", {}, true); } });
  const { data } = await SB.auth.getSession();
  if (data && data.session) { USER = data.session.user; await entrou(); } else go("boasvindas", {}, true);
}
async function entrou() {
  if (ENTRANDO) return; ENTRANDO = true;
  try { await carregar(); go(S.perfil ? "inicio" : "cadastro", S.perfil ? {} : { step: 1, novo: true }, true); }
  catch (e) { console.error(e); toast("Não consegui carregar seus dados. Tente de novo."); go("boasvindas", {}, true); }
  finally { ENTRANDO = false; }
}
async function sair() { await SB.auth.signOut().catch(() => {}); for (const k of Object.keys(SINC)) delete SINC[k]; S.perfil = null; for (const n of Object.keys(MAPA)) S[n] = { items: [] }; S.checks = { d: {} }; CHAT = []; USER = null; go("boasvindas", {}, true); }

''' + s[b:]

# banner do modo de teste
rep('Modo de teste: os dados não ficam salvos nesta visualização.', 'Modo de demonstração: configure o Supabase em config.js para salvar os dados.')

# tela de entrar
rep("const CAD = {};", r'''TELAS.entrar = (p) => `${topo("Entrar")}
<div class="wrap stack" style="padding-top:20px;gap:14px">
  <div style="display:flex;justify-content:center;padding:10px 0 4px">${logo(40)}</div>
  ${p.enviado ? `<div class="card stack" style="gap:8px;text-align:center"><span class="ib" style="margin:0 auto">${ic("feito", 20)}</span><p class="b">Confira seu e-mail</p><p class="small muted">Enviamos um link de acesso para <b>${esc(p.email)}</b>. Abra o e-mail neste celular e toque no link para entrar.</p></div>
    <button class="btn sec full" data-a="entrar-de-novo">Usar outro e-mail</button>`
  : `<p class="muted small" style="text-align:center">Sem senha: enviamos um link de acesso para o seu e-mail.</p>
  <form class="stack" data-f="entrar"><label class="f">Seu e-mail<input class="input" type="email" name="email" autocomplete="email" inputmode="email" required placeholder="voce@email.com"></label><button class="btn full" type="submit">Receber link de acesso</button></form>`}
  <p class="xs muted" style="text-align:center;line-height:1.5">Ao entrar, você concorda em guardar os dados de saúde da criança na sua conta. Eles ficam privados e você pode apagar quando quiser.</p>
</div>`;

const CAD = {};''')
rep('<button class="btn full" data-a="cad-ir" data-v="1">Começar ${ic("seta-dir", 18)}</button>',
    '<button class="btn full" data-a="cad-ir" data-v="1">Começar ${ic("seta-dir", 18)}</button>\n  ${SB ? `<button class="link" style="align-self:center;margin-top:6px" data-a="ir" data-v="entrar">Já tenho conta</button>` : ""}')
rep('    case "cad-ir": ', '    case "cad-ir": if (SB && !USER) { go("entrar"); break; } ')
rep('    case "voltar": voltar(); break;', '    case "voltar": voltar(); break;\n    case "entrar-de-novo": TELA.p = {}; render(); break;\n    case "sair": confirmar("Sair da conta?", "Seus dados continuam guardados. Para voltar, é só entrar com o mesmo e-mail.", "Sair", sair); break;\n    case "ver-original": { const w = window.open("", "_blank"); const { data, error } = await SB.storage.from("documentos").createSignedUrl(v, 300); if (error || !data) { if (w) w.close(); toast("Não consegui abrir o arquivo."); } else if (w) w.location = data.signedUrl; else location.href = data.signedUrl; break; }')
rep('const SEM_DOCK = ["teiaplus",', 'const SEM_DOCK = ["entrar","teiaplus",')
rep('    if (tipo === "cad") {', r'''    if (tipo === "entrar") { const email = g("email").toLowerCase(); const { error } = await SB.auth.signInWithOtp({ email, options: { emailRedirectTo: location.origin + location.pathname } }); if (error) { toast(error.status === 429 ? "Muitas tentativas. Espere um minuto." : "Não consegui enviar o link. Confira o e-mail."); return; } TELA.p = { enviado: true, email }; render(); return; }
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
rep('} catch (err) { clearInterval(relogio); toast(err && err.code === "rate_limited"', '} catch (err) { clearInterval(relogio); if (err && err.code === "limite") { SCAN = null; paywall(err.motivo || "leitura", { tipo }); return; } toast(err && err.code === "rate_limited"')
# assistente
rep('const r = await SAMPLE(msgs, { modelTier: "default", cache: false }); contarUso("pergunta");',
    'const r = { text: JSON.stringify(await ia("pergunta", { historico: hist.map(m => ({ role: m.role, content: m.content })) })) }; contarUso("pergunta"); atualizarPlano().catch(() => {});')
rep('} catch (e) { ult().content = e && e.code === "rate_limited"', '} catch (e) { if (e && e.code === "limite") { CHAT.splice(-2, 2); paywall(e.motivo || "pergunta"); return; } ult().content = e && e.code === "rate_limited"')
# resumo
rep('try { const r = await SAMPLE(prompt, { modelTier: "default", onText: ({ text }) => { const el = document.getElementById("reltxt"); if (el) el.textContent = text; } }); const el = document.getElementById("reltxt"); if (el && r.text) el.textContent = r.text; }',
    'try { const r = await ia("resumo", { sessoes: sess }); const el = document.getElementById("reltxt"); if (el && r && r.texto) el.textContent = r.texto; }')
rep('catch (err) { out.innerHTML = `<p class="banner">${err && err.code === "rate_limited"', 'catch (err) { if (err && err.code === "limite") { paywall("relatorio"); return; } out.innerHTML = `<p class="banner">${err && err.code === "rate_limited"')
# teia+ via servidor
rep('    case "plus-assinar": S.plano = { ...S.plano, plus: true, ciclo: v, desde: iso(new Date()) }; await salvar("plano").catch(() => {}); voltar(); toast("Bem-vinda ao teia+!"); break;',
    '    case "plus-assinar": if (SB) { const { error } = await SB.functions.invoke("assinatura", { body: { acao: "assinar", ciclo: v } }); if (error) { toast("O pagamento ainda não está disponível."); break; } await atualizarPlano(); } else S.plano = { ...S.plano, plus: true, ciclo: v, desde: iso(new Date()) }; voltar(); toast("Bem-vinda ao teia+!"); break;')
rep('    case "plus-cancelar": S.plano = { ...S.plano, plus: false }; await salvar("plano").catch(() => {}); render(); toast("Assinatura cancelada (teste)."); break;',
    '    case "plus-cancelar": if (SB) { const { error } = await SB.functions.invoke("assinatura", { body: { acao: "cancelar" } }); if (error) { toast("Não consegui cancelar agora."); break; } await atualizarPlano(); } else S.plano = { ...S.plano, plus: false }; render(); toast("Assinatura cancelada."); break;')
# apagar tudo
a = s.index('    case "apagar-tudo":'); b = s.index('\n', a)
s = s[:a] + r'''    case "apagar-tudo": confirmar("Apagar todos os dados?", "Perfil, rotina, tratamentos, documentos, arquivos e registros serão apagados. Não dá para desfazer.", "Apagar tudo", async () => {
      if (SB && USER) { try { const { data: arqs } = await SB.storage.from("documentos").list(USER.id, { limit: 1000 }); if (arqs && arqs.length) await SB.storage.from("documentos").remove(arqs.map(f => `${USER.id}/${f.name}`));
        for (const t of ["marcacoes", ...Object.values(MAPA).map(m => m[0]), "perfis"]) { const { error } = await SB.from(t).delete().eq("user_id", USER.id); if (error) throw error; } } catch (e) { toast("Não consegui apagar tudo. Tente de novo."); return; } }
      for (const k of Object.keys(SINC)) delete SINC[k]; S.perfil = null; for (const n of Object.keys(MAPA)) S[n] = { items: [] }; S.checks = { d: {} }; CHAT = []; go(SB ? "cadastro" : "boasvindas", SB ? { step: 1, novo: true } : {}, true); toast("Tudo apagado."); }); break;''' + s[b:]
# sair no perfil
rep('  <button class="btn danger full" data-a="apagar-tudo">', '  ${SB && USER ? `<button class="btn sec full" data-a="sair">Sair da conta</button><p class="xs muted" style="text-align:center;margin-top:-4px">${esc(USER.email || "")}</p>` : ""}\n  <button class="btn danger full" data-a="apagar-tudo">')
rep('<p class="xs muted">versão de teste</p>', '<p class="xs muted">${SB ? "versão beta" : "demonstração"}</p>')
# contarUso: o servidor é a fonte, só atualiza a tela
rep('salvar("plano").catch(() => {}); }', '}')
# remove protótipo leftovers
s = s.replace('<p class="xs muted" style="text-align:center;line-height:1.5">${pl === "anual" ? "Depois dos 7 dias, R$ 149,00 por ano. Cancele antes e não paga nada." : "Renova todo mês. Cancele quando quiser."}<br>Protótipo: nenhuma cobrança é feita.</p>',
              '<p class="xs muted" style="text-align:center;line-height:1.5">${pl === "anual" ? "Depois dos 7 dias, R$ 149,00 por ano. Cancele antes e não paga nada." : "Renova todo mês. Cancele quando quiser."}<br>Versão beta: nenhuma cobrança é feita ainda.</p>')

# ---------- acesso livre (provisório): conta anônima, sem tela de login ----------
def rep2(a, b):
    global s
    assert a in s, "MISS2: " + a[:90]
    s = s.replace(a, b, 1)
rep2("""  const { data } = await SB.auth.getSession();
  if (data && data.session) { USER = data.session.user; await entrou(); } else go("boasvindas", {}, true);
}""", """  const { data } = await SB.auth.getSession();
  if (data && data.session) { USER = data.session.user; await entrou(); return; }
  /* acesso livre (provisório): conta anônima ligada a este aparelho */
  const { data: an, error } = await SB.auth.signInAnonymously();
  if (error || !an || !an.user) { console.error("login anônimo", error); MODO_DEMO = true; SAMPLE = null; SAMPLE_IMG = false; go("boasvindas", {}, true); return; }
  USER = an.user; await entrou();
}""")
rep2('go(S.perfil ? "inicio" : "cadastro", S.perfil ? {} : { step: 1, novo: true }, true);', 'go(S.perfil ? "inicio" : "boasvindas", {}, true);')
rep2('    case "cad-ir": if (SB && !USER) { go("entrar"); break; } ', '    case "cad-ir": ')
rep2('\n  ${SB ? `<button class="link" style="align-self:center;margin-top:6px" data-a="ir" data-v="entrar">Já tenho conta</button>` : ""}', '')
rep2('${SB && USER ? `<button class="btn sec full" data-a="sair">Sair da conta</button>', '${SB && USER && !USER.is_anonymous ? `<button class="btn sec full" data-a="sair">Sair da conta</button>')
rep2('<p class="xs muted" style="text-align:center;margin-top:-4px">${esc(USER.email || "")}</p>` : ""}', '<p class="xs muted" style="text-align:center;margin-top:-4px">${esc(USER.email || "")}</p>` : ""}${SB && USER && USER.is_anonymous ? `<p class="xs muted" style="text-align:center;line-height:1.5">Acesso livre: seus dados ficam guardados e ligados a este aparelho. Em breve você vai poder criar uma conta para entrar de outros lugares.</p>` : ""}')
rep2('go(SB ? "cadastro" : "boasvindas", SB ? { step: 1, novo: true } : {}, true); toast("Tudo apagado.");', 'go("boasvindas", {}, true); toast("Tudo apagado.");')
rep2('Modo de demonstração: configure o Supabase em config.js para salvar os dados.', 'Modo de demonstração: os dados não estão sendo salvos agora.')

s = s.replace('/*__ICONS__*/', open(ICONS, encoding='utf-8').read())
for bad in ["DB.doc", "ASSETS.", "CL.use", "SAMPLE(", "SAMPLE.json", "/_blob/"]:
    assert bad not in s, "sobrou: " + bad
open(OUT, 'w', encoding='utf-8').write(s)
print("ok", len(s))
