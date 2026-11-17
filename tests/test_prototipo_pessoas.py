import sys
from playwright.sync_api import sync_playwright
U="file://"+sys.argv[1]; O=sys.argv[2]; erros=[]
clean="document.querySelectorAll('.toast,.banner').forEach(t=>t.remove());document.querySelectorAll('.rv').forEach(e=>e.classList.add('in'))"
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":390,"height":844},device_scale_factor=2); pg.on("pageerror",lambda e: erros.append(str(e)))
    pg.goto(U); pg.wait_for_timeout(600)
    pg.click("text=Começar"); pg.fill('input[name="mae"]',"Camila"); pg.click('label.opt:has(input[value="Mãe"]) span'); pg.click('form button[type="submit"]')
    pg.fill('input[name="crianca"]',"Keke"); pg.click('form button[type="submit"]')
    pg.check('input[name="consent"]'); pg.click('form button[type="submit"]'); pg.wait_for_timeout(500)
    assert pg.evaluate("S.perfil.papel")=="Mãe" and pg.evaluate("membroAtivo().nome")=="Keke"
    # consulta avulsa 26/11 23h
    pg.click('button[data-a="consulta-nova"]'); pg.wait_for_timeout(400)
    pg.fill('form[data-f="consulta"] input[name="titulo"]',"Neuropediatra"); pg.fill('form[data-f="consulta"] input[name="data"]',"2026-11-26"); pg.fill('form[data-f="consulta"] input[name="hora"]',"23:00")
    pg.fill('form[data-f="consulta"] input[name="local"]',"Clínica Viver"); pg.click('form[data-f="consulta"] button[type="submit"]'); pg.wait_for_timeout(500)
    assert pg.evaluate("S.consultas.items.length")==1
    pg.evaluate("go('inicio',{},true)"); pg.wait_for_timeout(900); pg.evaluate(clean)
    txt=pg.evaluate("document.body.innerText"); assert "Neuropediatra" in txt and "23:00" in txt, "consulta não aparece no início"
    pg.screenshot(path=f"{O}/c1.png")
    pg.evaluate("go('rotina',{data:'2026-11-26'},true)"); pg.wait_for_timeout(900); pg.evaluate(clean)
    assert "Neuropediatra" in pg.evaluate("document.body.innerText"); pg.screenshot(path=f"{O}/c2.png",full_page=True)
    # segunda pessoa: plano grátis -> teia+
    pg.evaluate("go('inicio',{},true)"); pg.wait_for_timeout(400)
    pg.click('button[data-a="membro-novo"]'); pg.wait_for_timeout(400); assert pg.evaluate("TELA.nome")=="teiaplus" and pg.evaluate("TELA.p.motivo")=="membro"
    pg.click('button[data-a="plus-assinar"]'); pg.wait_for_timeout(400)
    pg.click('button[data-a="membro-novo"]'); pg.wait_for_timeout(400); assert pg.evaluate("TELA.nome")=="cadastro"
    pg.fill('form[data-f="membro"] input[name="nome"]',"Dona Rosa"); pg.click('label.opt:has(input[value="Avô/Avó"]) span'); pg.click('form[data-f="membro"] button[type="submit"]'); pg.wait_for_timeout(600)
    assert pg.evaluate("membroAtivo().nome")=="Dona Rosa" and pg.evaluate("S.consultas.items.length")==0, "dados misturados"
    pg.evaluate(clean); pg.screenshot(path=f"{O}/c3.png")
    pg.click('button.pessoa[data-a="membro-trocar"] >> nth=0'); pg.wait_for_timeout(500); assert pg.evaluate("membroAtivo().nome")=="Keke" and pg.evaluate("S.consultas.items.length")==1
    # salvar não perde dados de outra pessoa
    assert pg.evaluate("ALL.consultas.length")==1
    # quem cuida junto
    pg.evaluate("go('familia',{},true)"); pg.wait_for_timeout(400)
    pg.click('button[data-a="rede-novo"]'); pg.wait_for_timeout(300); pg.fill('form[data-f="rede"] input[name="nome"]',"Marcos"); pg.select_option('form[data-f="rede"] select[name="papel"]',"Pai"); pg.click('form[data-f="rede"] button[type="submit"]'); pg.wait_for_timeout(400)
    pg.click('button[data-a="quem-sou"]:has-text("Marcos")'); pg.wait_for_timeout(300)
    pg.evaluate(clean); pg.screenshot(path=f"{O}/c4.png")
    pg.evaluate("go('rotina',{data:'2026-11-26'},true)"); pg.wait_for_timeout(400); pg.click("button.check"); pg.wait_for_timeout(300)
    assert pg.evaluate("Object.values(S.checks.d['2026-11-26'])[0].by")=="Marcos"
    pg.evaluate("go('perfil',{},true)"); pg.wait_for_timeout(900); pg.evaluate(clean); pg.screenshot(path=f"{O}/c5.png",full_page=True)
    # linguagem
    for t in ['boasvindas','inicio','perfil','familia','assistente','teiaplus','conteudos']:
        pg.evaluate(f"go('{t}',{{}},true)"); pg.wait_for_timeout(150)
        tx=pg.evaluate("document.body.innerText").lower()
        for ruim in ["mães","sozinha","seu filho","bem-vinda","mamãe"]: assert ruim not in tx, (t, ruim)
    b.close()
print("ERROS:", erros or "nenhum")
