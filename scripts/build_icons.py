import json, os, re, sys

SRC, OUT = sys.argv[1], sys.argv[2]   # pasta SVGs/regular da Phosphor, arquivo .json
NAMES = {
 "inicio": "house", "rotina": "calendar-check", "familia": "users-three", "perfil": "user", "mais": "plus",
 "buscar": "magnifying-glass", "notificacao": "bell", "camera": "camera", "receita": "prescription",
 "laudo": "file-text", "exame": "heartbeat", "pasta": "folder", "ia": "sparkle", "relatorio": "chart-bar",
 "privacidade": "lock-simple", "medicacao": "pill", "lembrete": "alarm", "consulta": "calendar-plus",
 "medico": "stethoscope", "sono": "moon", "humor": "smiley", "crise": "lightning", "bemestar": "heart",
 "fono": "user-sound", "to": "hand", "psico": "brain", "aba": "steps", "fisio": "person-arms-spread",
 "musica": "music-notes", "hidro": "swimming-pool", "chat": "chat-circle", "evolucao": "trend-up",
 "meta": "target", "conquista": "star", "desenvolvimento": "plant", "diario": "notebook", "linha": "path",
 "feito": "check", "rede": "graph", "cuidador": "hand-heart", "crianca": "baby", "direitos": "scales",
 "escola": "backpack", "estudo": "book-open", "voltar": "arrow-left", "seta": "caret-right", "fechar": "x",
 "lixo": "trash", "editar": "pencil-simple", "upload": "upload-simple", "tarefa": "list-checks",
 "alerta": "warning-circle", "ajustes": "sliders-horizontal", "enviar": "arrow-up", "grade": "squares-four",
 "seta-dir": "arrow-right", "conteudos": "newspaper", "artigo": "article", "video": "play-circle", "dica": "lightbulb", "esquerda": "caret-left",
 "humor1": "smiley-angry", "humor2": "smiley-sad", "humor3": "smiley-meh", "humor4": "smiley",
}
icons = {}
for k, n in NAMES.items():
    p = os.path.join(SRC, f"{n}.svg")
    if not os.path.exists(p):
        print("faltando:", n); continue
    s = open(p, encoding="utf-8").read()
    s = re.sub(r'<rect width="256" height="256" fill="none"\s*/>', "", s)
    s = s.replace('stroke-width="16"', 'stroke-width="15"')
    icons[k] = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", s.strip())
FILL_DIR = os.path.join(os.path.dirname(SRC.rstrip("/")), "fill")
for k, n in {"inicio": "house", "rotina": "calendar-check", "familia": "users-three", "perfil": "user", "humor5": "smiley", "conteudos": "newspaper"}.items():
    s = open(os.path.join(FILL_DIR, f"{n}-fill.svg"), encoding="utf-8").read()
    s = re.sub(r'<rect width="256" height="256" fill="none"\s*/>', "", s)
    icons[k + "-f"] = '<g fill="currentColor">' + re.sub(r"^<svg[^>]*>|</svg>\s*$", "", s.strip()) + "</g>"
json.dump(icons, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
print(len(icons), "ícones,", os.path.getsize(OUT), "bytes")
