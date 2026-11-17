# Teste do app com um Supabase simulado em memória (sem rede).
import sys, json, os
from playwright.sync_api import sync_playwright
WEB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "index.html"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
MOCK = r"""
window.TEIA_CONFIG_FORCE = true;
(() => {
 const salvo = sessionStorage.getItem("__db"); const db = window.__db = salvo ? JSON.parse(salvo) : { perfis: [], medicamentos: [], tratamentos: [], tarefas: [], marcacoes: [], documentos: [], registros: [], rede: [], notas_consulta: [], assinaturas: [{ user_id: "u1", plano: "gratis", status: "ativa" }], uso_ia: [], conteudos: [{ id: "c1", categoria: "artigo", titulo: "Artigo do banco", minutos: 2, autor: "Equipe teia", corpo: [{ p: "Texto" }, { h: "Título" }, { ul: ["a", "b"] }], destaque: true, publicado: true }] };
 const files = window.__files = JSON.parse(sessionStorage.getItem("__files") || "[]");
 const persist = () => { sessionStorage.setItem("__db", JSON.stringify(db)); sessionStorage.setItem("__files", JSON.stringify(files)); };
 const user = { id: "u1", email: "camila@exemplo.com" };
 let logged = !!sessionStorage.getItem("logado");
 function q(t) {
  let rows = () => db[t], filtros = [], op = "select", payload = null, single = false;
  const api = {
   select() { return api; }, eq(k, v) { filtros.push(r => r[k] === v); return api; }, gte(k, v) { filtros.push(r => String(r[k]) >= v); return api; },
   in(k, vs) { filtros.push(r => vs.includes(r[k])); return api; }, match(o) { filtros.push(r => Object.entries(o).every(([k, v]) => r[k] === v)); return api; },
   order() { return api; }, limit() { return api; }, maybeSingle() { single = true; return api; },
   upsert(p, o) { op = "upsert"; payload = Array.isArray(p) ? p : [p]; return api; }, delete() { op = "delete"; return api; },
   then(ok, ko) { try {
     const pass = r => filtros.every(f => f(r)) && (!r.user_id || r.user_id === "u1" || t === "conteudos");
     if (op === "select") { const d = db[t].filter(pass).map(r => JSON.parse(JSON.stringify(r))); return Promise.resolve({ data: single ? (d[0] || null) : d, error: null }).then(ok, ko); }
     if (op === "upsert") { for (const r of payload) { const key = t === "marcacoes" ? (x => x.dia === r.dia && x.chave === r.chave) : t === "perfis" ? (x => x.user_id === r.user_id) : (x => x.id === r.id); const i = db[t].findIndex(key); if (i >= 0) db[t][i] = { ...db[t][i], ...r }; else db[t].push({ ...r }); } window.__ops = (window.__ops || 0) + payload.length; persist(); return Promise.resolve({ data: null, error: null }).then(ok, ko); }
     if (op === "delete") { db[t] = db[t].filter(r => !pass(r)); persist(); return Promise.resolve({ data: null, error: null }).then(ok, ko); }
   } catch (e) { return Promise.reject(e).then(ok, ko); } }
  }; return api;
 }
 const cbs = [];
 window.supabase = { createClient: () => ({
  auth: {
   onAuthStateChange(cb) { cbs.push(cb); return { data: { subscription: { unsubscribe() {} } } }; },
   async getSession() { return { data: { session: logged ? { user } : null } }; },
   async signInWithOtp({ email }) { window.__otp = email; return { error: null }; },
   async signOut() { logged = false; sessionStorage.removeItem("logado"); cbs.forEach(c => c("SIGNED_OUT", null)); return { error: null }; },
  },
  from: q,
  functions: { async invoke(nome, { body }) {
    window.__inv = (window.__inv || []).concat([[nome, body.tarefa || body.acao]]);
    if (nome === "assinatura") { db.assinaturas[0] = { user_id: "u1", plano: body.acao === "assinar" ? "plus" : "gratis", status: body.acao === "assinar" ? "teste" : "cancelada", ciclo: body.ciclo }; persist(); return { data: { ok: true }, error: null }; }
    const u = db.uso_ia[0] || (db.uso_ia[0] = { user_id: "u1", mes: new Date().toISOString().slice(0, 7), leituras: 0, perguntas: 0 });
    const plus = db.assinaturas[0].plano === "plus";
    const lim = (k, n, m) => { if (!plus && u[k] >= n) return { data: null, error: { context: { status: 402, json: async () => ({ erro: "limite", motivo: m }) } } }; };
    if (body.tarefa === "laudo" || body.tarefa === "receita") { const l = lim("leituras", 3, "leitura"); if (l) return l; u.leituras++; persist(); window.__imgs = body.imagens.length; window.__dataurl = String(body.imagens[0]).slice(0, 22);
      return { data: { resultado: body.tarefa === "laudo" ? { tipo: "laudo", titulo: "Avaliação", data: "2026-10-28", profissional: "Dra. Ana", resumo_simples: "Resumo.", pontos_principais: ["p"], termos: [], recomendacoes: [], perguntas_para_consulta: [] } : { medico: "Dr. Paulo", data: "2026-11-10", medicamentos: [{ nome: "Risperidona", dose: "0,5 mg", horarios: ["08:00"] }] } }, error: null }; }
    if (body.tarefa === "pergunta") { const l = lim("perguntas", 5, "pergunta"); if (l) return l; u.perguntas++; persist(); return { data: { resultado: { resposta: "Isso o profissional avalia. Anotei.", anotacao: { titulo: "Sono", texto: "Acorda à noite.", para: "Neuro" } } }, error: null }; }
    if (body.tarefa === "resumo") { if (!plus) return lim("x", -1, "relatorio"); return { data: { resultado: { texto: "Resumo do mês." } }, error: null }; }
  } },
  storage: { from: () => ({
   async upload(path, f) { files.push(path); persist(); return { data: { path }, error: null }; },
   async list(pref) { return { data: files.filter(f => f.startsWith(pref + "/")).map(f => ({ name: f.split("/")[1] })), error: null }; },
   async remove(ps) { ps.forEach(p => files.splice(files.indexOf(p), 1)); persist(); return { error: null }; },
   async createSignedUrl(p) { return { data: { signedUrl: "about:blank#" + p }, error: null }; } }) },
 }) };
 window.__login = () => { logged = true; sessionStorage.setItem("logado", "1"); cbs.forEach(c => c("SIGNED_IN", { user })); };
})();
"""
erros = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    ctx.route("https://cdn.jsdelivr.net/npm/@supabase/**", lambda r: r.fulfill(body="", content_type="text/javascript"))
    ctx.route("**/config.js", lambda r: r.fulfill(body='window.TEIA_CONFIG={SUPABASE_URL:"https://x.supabase.co",SUPABASE_ANON_KEY:"k"}', content_type="text/javascript"))
    ctx.add_init_script(MOCK)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("console", lambda m: m.type == "error" and erros.append("console: " + m.text))
    pg.goto("file://" + WEB); pg.wait_for_timeout(800)
    assert pg.evaluate("TELA.nome") == "boasvindas"
    pg.click("text=Começar"); pg.wait_for_timeout(300); assert pg.evaluate("TELA.nome") == "entrar"
    pg.fill('input[name="email"]', "camila@exemplo.com"); pg.click('form[data-f="entrar"] button'); pg.wait_for_timeout(300)
    assert pg.evaluate("window.__otp") == "camila@exemplo.com"; pg.screenshot(path=f"{OUT}/s_entrar.png")
    pg.evaluate("__login()"); pg.wait_for_timeout(800); assert pg.evaluate("TELA.nome") == "cadastro", pg.evaluate("TELA.nome")
    pg.fill('input[name="mae"]', "Camila"); pg.click('form button[type="submit"]')
    pg.fill('input[name="crianca"]', "Theo"); pg.fill('input[name="nascimento"]', "2023-03-10"); pg.click('form button[type="submit"]')
    pg.click('label.opt:has(input[value="TEA"]) span'); pg.check('input[name="consent"]'); pg.click('form button[type="submit"]'); pg.wait_for_timeout(600)
    assert pg.evaluate("__db.perfis.length") == 1 and pg.evaluate("__db.perfis[0].crianca") == "Theo"
    pg.click("text=Adicionar terapia")
    for d in ["1", "3"]: pg.click(f'label.opt:has(input[name="dias"][value="{d}"]) span')
    pg.fill('input[name="hora"]', "10:00"); pg.click('form button[type="submit"]'); pg.wait_for_timeout(500)
    assert pg.evaluate("__db.tratamentos.length") == 1 and pg.evaluate("__db.tratamentos[0].dias") == [1, 3]
    pg.evaluate("go('rotina',{data:'2026-11-16'},true)"); pg.wait_for_timeout(400)
    pg.click('button.check'); pg.wait_for_timeout(400); assert pg.evaluate("__db.marcacoes.length") == 1, pg.evaluate("__db.marcacoes")
    pg.click('button.check'); pg.wait_for_timeout(400); assert pg.evaluate("__db.marcacoes.length") == 0
    # nota e chat
    pg.evaluate("go('assistente',{},true)"); pg.wait_for_timeout(300)
    pg.fill("#pergunta", "Devo me preocupar?"); pg.press("#pergunta", "Enter"); pg.wait_for_timeout(800)
    assert pg.evaluate("__db.notas_consulta.length") == 1
    # leitura de laudo (imagem)
    pg.evaluate("go('inicio',{},true)"); pg.wait_for_timeout(400)
    img = "/tmp/laudo_teste.png"
    from PIL import Image; Image.new("RGB", (800, 1000), "white").save(img)
    pg.click('button.bn[data-v="laudo"]'); pg.wait_for_timeout(500)
    with pg.expect_file_chooser() as fc: pg.click('button[data-v="laudo|galeria"]')
    fc.value.set_files(img); pg.wait_for_timeout(9000)
    assert pg.evaluate("TELA.nome") == "conflaudo", pg.evaluate("TELA.nome")
    assert pg.evaluate("window.__dataurl").startswith("data:image/"), pg.evaluate("window.__dataurl")
    pg.click('form[data-f="laudo"] button[type="submit"]'); pg.wait_for_timeout(800)
    assert pg.evaluate("__db.documentos.length") == 1 and pg.evaluate("__db.documentos[0].arquivos[0]").startswith("u1/")
    assert pg.evaluate("__files.length") == 1
    # recarregar: os dados vêm do banco
    pg.reload(); pg.wait_for_timeout(1200)
    assert pg.evaluate("TELA.nome") == "inicio", pg.evaluate("TELA.nome")
    assert pg.evaluate("S.trat.items.length") == 1 and pg.evaluate("S.docs.items.length") == 1 and pg.evaluate("S.notas.items.length") == 1
    assert pg.evaluate("CONTEUDOS[0].titulo") == "Artigo do banco"
    ops0 = pg.evaluate("window.__ops || 0"); pg.evaluate("salvar('trat')"); pg.wait_for_timeout(300)
    assert pg.evaluate("window.__ops || 0") == ops0, "salvou sem mudança"
    # limite de leituras -> paywall
    pg.evaluate("__db.uso_ia[0].leituras = 3; sessionStorage.setItem('__db', JSON.stringify(__db))"); pg.evaluate("atualizarPlano().then(()=>go('inicio',{},true))"); pg.wait_for_timeout(500)
    pg.click('button.bn[data-v="laudo"]'); pg.wait_for_timeout(500); assert pg.evaluate("TELA.nome") == "teiaplus"
    pg.click('button[data-a="plus-assinar"]'); pg.wait_for_timeout(600); assert pg.evaluate("S.plano.plus") is True
    pg.evaluate("go('perfil',{},true)"); pg.wait_for_timeout(500); pg.screenshot(path=f"{OUT}/s_perfil.png", full_page=True)
    # apagar tudo
    pg.click('button[data-a="apagar-tudo"]'); pg.wait_for_timeout(400); pg.click('button[data-a="confirmar-ok"]'); pg.wait_for_timeout(800)
    assert pg.evaluate("__db.documentos.length + __db.tratamentos.length + __db.perfis.length + __files.length") == 0
    # sair
    pg.evaluate("go('perfil',{},true)"); pg.wait_for_timeout(300)
    b.close()
print("ERROS:", erros or "nenhum")
