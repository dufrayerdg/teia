# Executado por build_web.py (mesmo escopo: usa a variável `s`).
# Liga no site: família (dono dos dados), campos novos, arquivos, link para o profissional,
# convites, conta com e-mail, notificações e app instalável.

VAPID_PUBLICA = "BJyR4Bf9lmad5nsTOZkb82JCG_rja1rfBo_n0BfpwaLL9SPdCAuMt5lxyr6vMqeAWVK55VXChIEmnNurKX0P0xM"


def rep3(a, b):
    global s
    assert a in s, "MISS3: " + a[:100]
    s = s.replace(a, b, 1)


rep3('<meta name="theme-color" content="#F8F5FE">',
     '<meta name="theme-color" content="#F8F5FE">\n<link rel="manifest" href="/manifest.webmanifest">\n'
     '<link rel="apple-touch-icon" href="/icones/apple-touch-icon.png">\n<meta name="apple-mobile-web-app-capable" content="yes">\n'
     '<meta name="mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-title" content="teia">\n'
     '<meta name="apple-mobile-web-app-status-bar-style" content="default">')

# ---- dono dos dados: a própria conta ou a de quem convidou ----
rep3("let USER = null, MODO_DEMO = !SB,", "let DONO_ID = null; const DONO = () => DONO_ID || (USER && USER.id);\nlet USER = null, MODO_DEMO = !SB,")
rep3('const { error } = await SB.from("perfis").upsert({ user_id: USER.id,',
     'const { error } = await SB.from("perfis").upsert({ user_id: DONO(), tour: !!p.tour, lembretes: p.lembretes || {},')
rep3('.map(([, v]) => ({ ...v, user_id: USER.id }));', '.map(([, v]) => ({ ...v, user_id: DONO() }));')
rep3('const pega = t => SB.from(t).select("*");',
     'const ac = await SB.from("acessos").select("dono").eq("convidado", USER.id).order("criado_em").limit(1).maybeSingle(); DONO_ID = (ac.data && ac.data.dono) || USER.id;\n'
     '  const pega = t => SB.from(t).select("*").eq("user_id", DONO());')
rep3('SB.from("perfis").select("*").maybeSingle(), SB.from("assinaturas").select("*").maybeSingle(), SB.from("uso_ia").select("*").eq("mes", mesAtual()).maybeSingle(),',
     'SB.from("perfis").select("*").eq("user_id", DONO()).maybeSingle(), SB.from("assinaturas").select("*").eq("user_id", DONO()).maybeSingle(), SB.from("uso_ia").select("*").eq("user_id", DONO()).eq("mes", mesAtual()).maybeSingle(),')
rep3('SB.from("marcacoes").select("dia,chave,por,hora").gte("dia",', 'SB.from("marcacoes").select("dia,chave,por,hora").eq("user_id", DONO()).gte("dia",')
rep3('consent: !!r.consentimento_em, consentEm: r.consentimento_em } : null;',
     'consent: !!r.consentimento_em, consentEm: r.consentimento_em, tour: !!r.tour, lembretes: r.lembretes || {} } : null;')
rep3('const [a, u] = await Promise.all([SB.from("assinaturas").select("*").maybeSingle(), SB.from("uso_ia").select("*").eq("mes", mesAtual()).maybeSingle()]);',
     'const [a, u] = await Promise.all([SB.from("assinaturas").select("*").eq("user_id", DONO()).maybeSingle(), SB.from("uso_ia").select("*").eq("user_id", DONO()).eq("mes", mesAtual()).maybeSingle()]);')
rep3('const caminho = `${USER.id}/${uid()}${ext}`;', 'const caminho = `${DONO()}/${uid()}${ext}`;')

# ---- campos novos ----
rep3('medico: m.medico || "" }),', 'medico: m.medico || "", estoque: m.estoque === "" || m.estoque == null ? null : Number(m.estoque), por_tomada: Number(m.porTomada) || 1 }),')
rep3('receitaId: r.receita_id || "", medico: r.medico })', 'receitaId: r.receita_id || "", medico: r.medico, estoque: r.estoque == null ? "" : Number(r.estoque), porTomada: Number(r.por_tomada) || 1 })')
rep3('crise: !!x.crise, tratamento_id: nul(x.tratId),', 'crise: !!x.crise, crise_info: x.criseInfo || null, tratamento_id: nul(x.tratId),')
rep3('crise: r.crise, tratId: r.tratamento_id || "",', 'crise: r.crise, criseInfo: r.crise_info || null, tratId: r.tratamento_id || "",')
rep3('origem: n.origem || "manual", pergunta: n.pergunta || "" }),', 'origem: n.origem || "manual", pergunta: n.pergunta || "", resposta: n.resposta || "", respondida_em: nul(n.respondidaEm) }),')
rep3('origem: r.origem, pergunta: r.pergunta })],', 'origem: r.origem, pergunta: r.pergunta, resposta: r.resposta || "", respondidaEm: r.respondida_em || "" })],')
rep3('  membros: ["membros",',
     '  marcos: ["marcos", x => ({ membro_id: nul(x.membroId), titulo: x.titulo, data: x.data, nota: x.nota || "", foto: x.foto || "" }),\n'
     '          r => ({ id: r.id, membroId: r.membro_id || "", titulo: r.titulo, data: r.data, nota: r.nota, foto: r.foto })],\n  membros: ["membros",')

# ---- apagar tudo: quem foi convidado só sai da família ----
rep3('      if (SB && USER) { try { const { data: arqs } = await SB.storage.from("documentos").list(USER.id,',
     '      if (SB && USER && DONO() !== USER.id) { await SB.from("acessos").delete().eq("dono", DONO()).eq("convidado", USER.id); DONO_ID = null; for (const k of Object.keys(SINC)) delete SINC[k]; S.perfil = null; for (const n of Object.keys(MAPA)) S[n] = { items: [] }; S.checks = { d: {} }; go("boasvindas", {}, true); toast("Você saiu da família. Os dados continuam com quem te convidou."); return; }\n'
     '      if (SB && USER) { try { const { data: arqs } = await SB.storage.from("documentos").list(USER.id,')

NUVEM_JS = r'''/* ---------- recursos da nuvem ---------- */
const VAPID_PUBLICA = "__VAPID__";
const tokenAleatorio = (n = 32) => { const a = new Uint8Array(n); crypto.getRandomValues(a); return Array.from(a, b => "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"[b % 62]).join(""); };
const codigoConvite = () => { const a = new Uint8Array(8); crypto.getRandomValues(a); return Array.from(a, b => "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[b % 32]).join(""); };
let ACESSOS = [], PUSH_ON = false, INSTALAR = null;
function ligarNuvem() {
  if (!SB) return;
  NUVEM.ativo = true;
  NUVEM.conta = () => USER ? { email: USER.is_anonymous ? (USER.new_email || "") : (USER.email || ""), anonimo: !!USER.is_anonymous, convidado: DONO() !== USER.id, provedor: (USER.app_metadata && USER.app_metadata.provider) || "" } : null;
  NUVEM.entrarEmail = async (email, converter) => {
    const volta = location.origin + location.pathname;
    if (converter && USER && USER.is_anonymous) { const { error } = await SB.auth.updateUser({ email }, { emailRedirectTo: volta }); if (error) throw error; return true; }
    const { error } = await SB.auth.signInWithOtp({ email, options: { emailRedirectTo: volta, shouldCreateUser: true } }); if (error) throw error; return true; };
  NUVEM.compartilhar = async () => { const token = tokenAleatorio(32); const { error } = await SB.from("links_profissional").insert({ token, user_id: DONO(), membro_id: ATIVO || null }); if (error) throw error; return `${location.origin}/r?t=${token}`; };
  NUVEM.convidar = async () => { const codigo = codigoConvite(); const { error } = await SB.from("convites").insert({ codigo, dono: USER.id }); if (error) throw error; await carregarAcessos(); return { codigo, link: `${location.origin}/?convite=${codigo}` }; };
  NUVEM.acessos = () => ACESSOS;
  NUVEM.aceitarConvite = async (codigo) => { const { error } = await SB.rpc("aceitar_convite", { p_codigo: codigo, p_nome: nomeUsuario() || "" });
    if (error) { const m = error.message || ""; return /convite_proprio/.test(m) ? "Esse convite é seu." : /sem_plus/.test(m) ? "Quem convidou precisa ter o teia+." : "Código inválido ou vencido."; }
    for (const k of Object.keys(SINC)) delete SINC[k]; await carregar(); go(S.perfil ? "inicio" : "cadastro", S.perfil ? {} : { step: 1, novo: true }, true); return true; };
  NUVEM.pushAtivo = () => PUSH_ON;
  NUVEM.pushAtivar = async () => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) return /iPhone|iPad/.test(navigator.userAgent) ? "No iPhone, adicione o app à tela de início primeiro (Compartilhar, depois Adicionar à Tela de Início)." : "Este navegador não recebe notificações.";
    const perm = await Notification.requestPermission(); if (perm !== "granted") return "Você não permitiu as notificações. Dá para mudar nas configurações do celular.";
    const reg = await navigator.serviceWorker.ready;
    const b64 = VAPID_PUBLICA.replace(/-/g, "+").replace(/_/g, "/"); const chave = Uint8Array.from(atob(b64 + "=".repeat((4 - b64.length % 4) % 4)), c => c.charCodeAt(0));
    const sub = (await reg.pushManager.getSubscription()) || (await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: chave })); const j = sub.toJSON();
    const { error } = await SB.from("push_inscricoes").upsert({ endpoint: j.endpoint, user_id: USER.id, dono: DONO(), p256dh: j.keys.p256dh, auth: j.keys.auth }); if (error) throw error; PUSH_ON = true; return true; };
  NUVEM.pushDesativar = async () => { const reg = await navigator.serviceWorker.ready; const sub = await reg.pushManager.getSubscription(); if (sub) { await SB.from("push_inscricoes").delete().eq("endpoint", sub.endpoint); await sub.unsubscribe(); } PUSH_ON = false; };
  obterURL = id => { SB.storage.from("documentos").createSignedUrl(id, 3600).then(({ data }) => { if (data && data.signedUrl) { URLS[id] = data.signedUrl; if (["marcos", "linha"].includes(TELA.nome) || document.querySelector("#layer .sheet")) render(); } }).catch(() => {}); };
}
async function carregarAcessos() { if (!SB || !USER) return; const { data } = await SB.from("acessos").select("convidado,nome,papel,criado_em").eq("dono", USER.id);
  const { data: cv } = await SB.from("convites").select("codigo,expira_em,usado_por").eq("dono", USER.id).is("usado_por", null).gt("expira_em", new Date().toISOString());
  ACESSOS = [...(data || []).map(a => ({ nome: a.nome || "Pessoa da família", status: "Com acesso" + (a.papel ? " · " + a.papel : "") })), ...(cv || []).map(c => ({ nome: "Convite " + c.codigo, status: "Aguardando · vence " + fmtData(String(c.expira_em || "").slice(0, 10)) }))]; }
async function estadoPush() { try { if (!("serviceWorker" in navigator)) return; const reg = await navigator.serviceWorker.getRegistration(); const sub = reg && await reg.pushManager.getSubscription(); PUSH_ON = !!sub && Notification.permission === "granted"; } catch (e) {} }
if ("serviceWorker" in navigator && location.protocol === "https:") window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); INSTALAR = e; if (TELA.nome === "inicio") render(); });
const instalado = () => (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone === true;
let SEM_INSTALAR = false; try { SEM_INSTALAR = !!localStorage.getItem("teia.semInstalar"); } catch (e) {}

/* IA no servidor (Edge Function "ia") */'''
rep3('/* IA no servidor (Edge Function "ia") */', NUVEM_JS.replace("__VAPID__", VAPID_PUBLICA))
rep3("async function iniciar() {", "async function iniciar() {\n  ligarNuvem();\n  try { const c = new URLSearchParams(location.search).get(\"convite\"); if (c) { localStorage.setItem(\"teia.convite\", c.toUpperCase()); history.replaceState(null, \"\", location.pathname); } } catch (e) {}")
rep3('  try { await carregar(); if (!S.perfil) {',
     '  try { await carregar(); const cv = (() => { try { return localStorage.getItem("teia.convite") || ""; } catch (e) { return ""; } })();\n'
     '    if (cv) { try { localStorage.removeItem("teia.convite"); } catch (e) {} const r = await NUVEM.aceitarConvite(cv.toUpperCase()); toast(r === true ? "Pronto! Agora você cuida junto." : r); if (r === true) return; }\n'
     '    if (!S.perfil) {')
rep3('go(S.perfil ? "inicio" : "cadastro", S.perfil ? {} : { step: 1, novo: true }, true); }',
     'carregarAcessos().catch(() => {}); estadoPush().catch(() => {}); go(S.perfil ? "inicio" : "cadastro", S.perfil ? {} : { step: 1, novo: true }, true); }')

# instalar o app (cartão na Início)
rep3('  <div class="qts">\n',
     '  ${!instalado() && !SEM_INSTALAR && (INSTALAR || /iPhone|iPad/.test(navigator.userAgent)) ? `<div class="card row" style="gap:12px"><span class="ib c2">${simbolo(18)}</span><div class="grow"><p class="b small">Instale a teia no celular</p><p class="xs muted">${INSTALAR ? "Abre como app e recebe lembretes." : "Toque em Compartilhar e depois em Adicionar à Tela de Início."}</p></div>${INSTALAR ? `<button class="btn" style="height:36px;padding:0 14px;font-size:13px" data-a="instalar">Instalar</button>` : ""}<button class="circle" style="width:30px;height:30px;box-shadow:none;background:var(--soft)" data-a="instalar-nao" aria-label="Fechar">${ic("fechar", 14)}</button></div>` : ""}\n'
     '  <div class="qts">\n')
rep3('    case "voltar": voltar(); break;',
     '    case "voltar": voltar(); break;\n'
     '    case "instalar": if (INSTALAR) { INSTALAR.prompt(); const r = await INSTALAR.userChoice.catch(() => null); INSTALAR = null; if (r && r.outcome === "accepted") toast("teia instalada!"); render(); } break;\n'
     '    case "instalar-nao": SEM_INSTALAR = true; try { localStorage.setItem("teia.semInstalar", "1"); } catch (e) {} render(); break;')

# arquivos no site vêm de links assinados (ligarNuvem troca obterURL)
rep3('function obterURL(id) { URLS[id] = "/_blob/" + id; }', 'let obterURL = id => {};')
