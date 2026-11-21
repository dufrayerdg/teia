# Teste do app com um Supabase simulado em memória (sem rede).
import sys, json, os
from playwright.sync_api import sync_playwright
WEB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "index.html"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
MOCK = r"""
window.TEIA_CONFIG_FORCE = true;
(() => {
 const salvo = sessionStorage.getItem("__db"); const db = window.__db = salvo ? JSON.parse(salvo) : { perfis: [], medicamentos: [], tratamentos: [], tarefas: [], marcacoes: [], documentos: [], registros: [], rede: [], notas_consulta: [], membros: [], consultas: [], marcos: [], acessos: [], convites: [], links_profissional: [], push_inscricoes: [], assinaturas: [{ user_id: "u1", plano: "gratis", status: "ativa" }], uso_ia: [], conteudos: [{ id: "c1", categoria: "artigo", titulo: "Artigo do banco", minutos: 2, autor: "Equipe teia", corpo: [{ p: "Texto" }, { h: "Título" }, { ul: ["a", "b"] }], destaque: true, publicado: true }] };
 const files = window.__files = JSON.parse(sessionStorage.getItem("__files") || "[]");
 const persist = () => { sessionStorage.setItem("__db", JSON.stringify(db)); sessionStorage.setItem("__files", JSON.stringify(files)); };
 const user = { id: "u1", email: "camila@exemplo.com", is_anonymous: false, user_metadata: { full_name: "Camila Souza" }, app_metadata: { provider: "google" } };
 let logged = !!sessionStorage.getItem("logado");
 function q(t) {
  let rows = () => db[t], filtros = [], op = "select", payload = null, single = false;
  const api = {
   select() { return api; }, eq(k, v) { filtros.push(r => r[k] === v); return api; }, gte(k, v) { filtros.push(r => String(r[k]) >= v); return api; },
   in(k, vs) { filtros.push(r => vs.includes(r[k])); return api; }, is(k, v) { filtros.push(r => (r[k] ?? null) === v); return api; }, gt(k, v) { filtros.push(r => String(r[k]) > v); return api; },
   insert(p) { op = "upsert"; payload = Array.isArray(p) ? p : [p]; return api; }, match(o) { filtros.push(r => Object.entries(o).every(([k, v]) => r[k] === v)); return api; },
   order() { return api; }, limit() { return api; }, maybeSingle() { single = true; return api; },
   upsert(p, o) { op = "upsert"; payload = Array.isArray(p) ? p : [p]; return api; }, delete() { op = "delete"; return api; },
   then(ok, ko) { try {
     const pass = r => filtros.every(f => f(r)) && (!r.user_id || r.user_id === "u1" || t === "conteudos" || t === "convites" || t === "acessos");
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
   async signInWithOtp({ email }) { window.__otp = (window.__otp_n = (window.__otp_n || 0) + 1, email); return { error: null }; },
   async verifyOtp(a) { window.__verify = a; if (a.token !== '123456') return { error: { message: 'invalid' } }; window.__login(); return { error: null }; },
   async signInWithOAuth(a) { window.__oauth = a; return { error: null }; },
   async linkIdentity(a) { window.__link = a; return { error: null }; },
   async signInAnonymously() { window.__anon = (window.__anon || 0) + 1; logged = true; sessionStorage.setItem("logado", "1"); return { data: { user, session: { user } }, error: null }; },
   async signOut() { logged = false; sessionStorage.removeItem("logado"); cbs.forEach(c => c("SIGNED_OUT", null)); return { error: null }; },
  },
  from: q,
  async rpc(nome, args) { window.__rpc = [nome, args]; return { data: null, error: { message: "convite_invalido" } }; },
  functions: { async invoke(nome, { body }) {
    window.__inv = (window.__inv || []).concat([[nome, body.tarefa || body.acao]]);
    if (nome === "assinatura") { db.assinaturas[0] = { user_id: "u1", plano: body.acao === "assinar" ? "plus" : "gratis", status: body.acao === "assinar" ? "teste" : "cancelada", ciclo: body.ciclo }; persist(); return { data: { ok: true }, error: null }; }
    if (window.__forcaErro) return { data: null, error: { context: { status: window.__forcaErro === "servico_ocupado" ? 503 : 429, json: async () => ({ erro: window.__forcaErro, motivo: "pergunta" }) } } };
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
import threading, http.server, functools, socketserver
_srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(type("H", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}), directory=os.path.dirname(WEB)))
threading.Thread(target=_srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{_srv.server_address[1]}/index.html"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    ctx.route("https://cdn.jsdelivr.net/npm/@supabase/**", lambda r: r.fulfill(body="", content_type="text/javascript"))
    ctx.route("**/config.js", lambda r: r.fulfill(body='window.TEIA_CONFIG={SUPABASE_URL:"https://x.supabase.co",SUPABASE_ANON_KEY:"k"}', content_type="text/javascript"))
    ctx.add_init_script(MOCK)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("console", lambda m: m.type == "error" and erros.append("console: " + m.text + " " + str([a.json_value() for a in m.args][:2])))
    pg.goto(URL); pg.wait_for_timeout(800)
    assert pg.evaluate("TELA.nome") == "boasvindas", pg.evaluate("TELA.nome")
    assert pg.evaluate("window.__anon") is None and pg.evaluate("USER") is None, "não deve criar conta anônima"
    corpo = pg.evaluate("document.body.innerText"); assert "Continuar com Google" in corpo and "Continuar com e-mail" in corpo
    assert "Explorar sem criar conta" in corpo
    pg.click("text=Continuar com Google"); pg.wait_for_timeout(300); assert pg.evaluate("window.__oauth.provider") == "google" and pg.evaluate("window.__oauth.options.redirectTo").endswith("/index.html")
    pg.click("text=Continuar com e-mail"); pg.wait_for_timeout(300); assert pg.evaluate("TELA.nome") == "entrar"
    pg.fill('input[name="email"]', "Camila@Exemplo.com"); pg.click('form[data-f="entrar"] button[type="submit"]'); pg.wait_for_timeout(400)
    assert pg.evaluate("window.__otp") == "camila@exemplo.com", pg.evaluate("window.__otp")
    assert "Confira seu e-mail" in pg.evaluate("document.body.innerText") and pg.evaluate("document.getElementById('reenviar').disabled") is True
    pg.evaluate("document.getElementById('reenviar').disabled = false"); pg.click("#reenviar"); pg.wait_for_timeout(300); assert pg.evaluate("window.__otp_n") == 2
    pg.fill('input[name="codigo"]', "000000"); pg.click('form[data-f="codigo"] button'); pg.wait_for_timeout(400); assert pg.evaluate("TELA.nome") == "entrar", "código errado não pode entrar"
    pg.fill('input[name="codigo"]', "123456"); pg.click('form[data-f="codigo"] button'); pg.wait_for_timeout(1200)
    assert pg.evaluate("window.__verify.type") == "email" and pg.evaluate("window.__verify.email") == "camila@exemplo.com"
    assert pg.evaluate("TELA.nome") == "cadastro" and pg.input_value('input[name="mae"]') == "Camila", "nome do Google não veio preenchido"
    pg.goto(URL); pg.wait_for_timeout(1000)
    assert pg.evaluate("TELA.nome") == "cadastro", "sessão deve voltar logada: " + pg.evaluate("TELA.nome")
    pg.evaluate("go('cadastro', { step: 1, novo: true }, true)"); pg.wait_for_timeout(300)
    pg.fill('input[name="mae"]', "Camila"); pg.set_input_files('input[data-foto]', "/tmp/art/foto_teste.jpg"); pg.wait_for_timeout(400); pg.click('form button[type="submit"]')
    pg.fill('input[name="crianca"]', "Theo"); pg.set_input_files('input[data-foto]', "/tmp/art/foto_teste.jpg"); pg.wait_for_timeout(400); pg.fill('input[name="nascimento"]', "2023-03-10"); pg.click('form button[type="submit"]')
    pg.click('label.opt:has(input[value="TEA"]) span'); pg.check('input[name="consent"]'); pg.click('form button[type="submit"]'); pg.wait_for_timeout(400); pg.click('button[data-a="tour-fim"] >> nth=0'); pg.wait_for_timeout(300); pg.wait_for_timeout(600)
    assert pg.evaluate("__db.perfis.length") == 1 and pg.evaluate("__db.perfis[0].crianca") == "Theo"
    assert str(pg.evaluate("__db.perfis[0].foto")).startswith("data:image/jpeg"), "foto de quem cuida não foi para o banco"
    assert str(pg.evaluate("__db.membros[0].foto")).startswith("data:image/jpeg"), "foto de quem recebe o cuidado não foi para o banco"
    pg.click("text=Terapia fixa")
    for d in ["1", "3"]: pg.click(f'label.opt:has(input[name="dias"][value="{d}"]) span')
    pg.click(' .pk[data-pk="hora"] .pkf[data-k="h"]'); pg.click('.pkpop button[data-v="10"]'); pg.click(' .pk[data-pk="hora"] .pkf[data-k="n"]'); pg.click('.pkpop button[data-v="00"]'); pg.click('form button[type="submit"]'); pg.wait_for_timeout(500)
    assert pg.evaluate("__db.tratamentos.length") == 1 and pg.evaluate("__db.tratamentos[0].dias") == [1, 3]
    assert pg.evaluate("__db.membros.length") == 1 and pg.evaluate("__db.membros[0].nome") == "Theo"
    assert pg.evaluate("__db.tratamentos[0].membro_id") == pg.evaluate("__db.membros[0].id")
    # consulta avulsa vai para o banco
    pg.evaluate("go('rotina',{},true)"); pg.wait_for_timeout(300)
    pg.click('button[data-a="consulta-nova"]'); pg.wait_for_timeout(300)
    pg.fill('form[data-f="consulta"] input[name="titulo"]', "Neuropediatra"); pg.click('form[data-f="consulta"] .pk[data-pk="data"] .pkf[data-k="d"]'); pg.click('.pkpop button[data-v="26"]'); pg.click('form[data-f="consulta"] .pk[data-pk="data"] .pkf[data-k="m"]'); pg.click('.pkpop button[data-v="11"]'); pg.click('form[data-f="consulta"] .pk[data-pk="data"] .pkf[data-k="a"]'); pg.click('.pkpop button[data-v="2026"]'); pg.click('form[data-f="consulta"] .pk[data-pk="hora"] .pkf[data-k="h"]'); pg.click('.pkpop button[data-v="23"]'); pg.click('form[data-f="consulta"] .pk[data-pk="hora"] .pkf[data-k="n"]'); pg.click('.pkpop button[data-v="00"]')
    pg.click('form[data-f="consulta"] button[type="submit"]'); pg.wait_for_timeout(500)
    assert pg.evaluate("__db.consultas.length") == 1 and pg.evaluate("__db.consultas[0].hora") == "23:00"
    pg.evaluate("go('rotina',{data:'2026-11-16'},true)"); pg.wait_for_timeout(400)
    pg.click('button.check'); pg.wait_for_timeout(400); assert pg.evaluate("__db.marcacoes.length") == 1, pg.evaluate("__db.marcacoes")
    pg.click('button.check'); pg.wait_for_timeout(400); assert pg.evaluate("__db.marcacoes.length") == 0
    # nota e chat
    pg.evaluate("go('assistente',{},true)"); pg.wait_for_timeout(300)
    pg.fill("#pergunta", "Devo me preocupar?"); pg.press("#pergunta", "Enter"); pg.wait_for_timeout(800)
    assert pg.evaluate("__db.notas_consulta.length") == 1
    for cod, trecho in [("limite_plus", "300 perguntas deste mês"), ("limite_dia", "limite de perguntas de hoje"), ("servico_ocupado", "muito concorrida")]:
        pg.evaluate(f"window.__forcaErro = '{cod}'"); pg.fill("#pergunta", "Oi " + cod); pg.press("#pergunta", "Enter"); pg.wait_for_timeout(700)
        ult = pg.evaluate("[...document.querySelectorAll('.bubble.ai')].pop().textContent"); assert trecho in ult, (cod, ult)
    pg.evaluate("window.__forcaErro = null"); assert pg.evaluate("TELA.nome") == "assistente", "limite do teia+ não deve levar ao paywall"
    # leitura de laudo (imagem)
    pg.evaluate("go('inicio',{},true)"); pg.wait_for_timeout(400)
    img = "/tmp/laudo_teste.png"
    from PIL import Image; Image.new("RGB", (800, 1000), "white").save(img)
    pg.click('button.bn[data-v="laudo"]'); pg.wait_for_timeout(500)
    with pg.expect_file_chooser() as fc: pg.click('label[data-v="laudo|galeria"]')
    fc.value.set_files(img); pg.wait_for_timeout(9000)
    assert pg.evaluate("TELA.nome") == "conflaudo", pg.evaluate("TELA.nome")
    assert pg.evaluate("window.__dataurl").startswith("data:image/"), pg.evaluate("window.__dataurl")
    pg.click('form[data-f="laudo"] button[type="submit"]'); pg.wait_for_timeout(800)
    assert pg.evaluate("__db.documentos.length") == 1 and pg.evaluate("__db.documentos[0].arquivos[0]").startswith("u1/")
    assert pg.evaluate("__files.length") == 1
    # recarregar: os dados vêm do banco
    pg.reload(); pg.wait_for_timeout(1200)
    if pg.evaluate("TELA.nome") != "inicio": print("DEBUG", pg.evaluate("JSON.stringify({perfis: __db.perfis.length, membros: __db.membros.length, logado: sessionStorage.getItem('logado'), anon: window.__anon||0, user: !!USER, demo: MODO_DEMO, perfil: !!S.perfil})"))
    assert pg.evaluate("TELA.nome") == "inicio", pg.evaluate("TELA.nome")
    assert (pg.evaluate("window.__anon") or 0) == 0, "criou outra conta anônima ao recarregar"
    assert pg.evaluate("S.trat.items.length") == 1 and pg.evaluate("S.docs.items.length") == 1 and pg.evaluate("S.notas.items.length") == 1
    assert pg.evaluate("S.consultas.items.length") == 1 and pg.evaluate("membroAtivo().nome") == "Theo"
    assert pg.evaluate("CONTEUDOS[0].titulo") == "Artigo do banco"
    ops0 = pg.evaluate("window.__ops || 0"); pg.evaluate("salvar('trat')"); pg.wait_for_timeout(300)
    assert pg.evaluate("window.__ops || 0") == ops0, "salvou sem mudança"
    # limite de leituras -> paywall
    pg.evaluate("__db.uso_ia[0].leituras = 3; sessionStorage.setItem('__db', JSON.stringify(__db))"); pg.evaluate("atualizarPlano().then(()=>go('inicio',{},true))"); pg.wait_for_timeout(500)
    pg.click('button.bn[data-v="laudo"]'); pg.wait_for_timeout(500); assert pg.evaluate("TELA.nome") == "teiaplus"
    pg.click('button[data-a="plus-assinar"]'); pg.wait_for_timeout(600); assert pg.evaluate("S.plano.plus") is True
    pg.evaluate("go('perfil',{},true)"); pg.wait_for_timeout(500); pg.screenshot(path=f"{OUT}/s_perfil.png", full_page=True)
    assert pg.evaluate("!!document.querySelector('[data-a=sair]')") is True and "Acesso livre" not in pg.evaluate("document.body.innerText")
    # link para o profissional (com servidor)
    pg.evaluate("go('relatorio',{},true)"); pg.wait_for_timeout(400)
    pg.evaluate("navigator.clipboard && (navigator.clipboard.writeText = async t => { window.__clip = t; })")
    pg.click('button[data-a="rel-link"]'); pg.wait_for_timeout(500)
    assert pg.evaluate("__db.links_profissional.length") == 1 and len(pg.evaluate("__db.links_profissional[0].token")) == 32
    # convite (teia+ ativo neste ponto do teste)
    pg.evaluate("go('conta',{},true)"); pg.wait_for_timeout(400); pg.click('button[data-a="convidar"]'); pg.wait_for_timeout(500)
    assert pg.evaluate("__db.convites.length") == 1 and len(pg.evaluate("__db.convites[0].codigo")) == 8
    pg.fill('form[data-f="aceitar-convite"] input', "ABCDEFGH"); pg.click('form[data-f="aceitar-convite"] button'); pg.wait_for_timeout(400)
    assert pg.evaluate("window.__rpc[0]") == "aceitar_convite"
    # marco com foto vai para o Storage
    pg.evaluate("go('marcos',{},true)"); pg.wait_for_timeout(300); pg.click('button[data-a="marco-novo"] >> nth=0'); pg.wait_for_timeout(300)
    pg.fill('form[data-f="marco"] input[name="titulo"]', "Primeira palavra"); pg.set_input_files('form[data-f="marco"] input[name="foto"]', img); pg.click('form[data-f="marco"] button[type="submit"]'); pg.wait_for_timeout(900)
    assert pg.evaluate("__db.marcos.length") == 1 and pg.evaluate("__db.marcos[0].foto").startswith("u1/"), pg.evaluate("__db.marcos")
    # apagar tudo
    pg.evaluate("go('perfil',{},true)"); pg.wait_for_timeout(500)
    pg.click('button[data-a="apagar-tudo"]'); pg.wait_for_timeout(400); pg.click('button[data-a="confirmar-ok"]'); pg.wait_for_timeout(800)
    assert pg.evaluate("__db.documentos.length + __db.tratamentos.length + __db.perfis.length + __db.membros.length + __db.consultas.length + __files.length") == 0
    # sair
    pg.evaluate("go('perfil',{},true)"); pg.wait_for_timeout(300)
    b.close()
print("ERROS:", erros or "nenhum")
