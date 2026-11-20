# Login (Google + e-mail)

Supabase (Authentication):
1. Providers: ative Email (magic link) e Google (Client ID e Secret); desative Anonymous sign-ins.
2. URL Configuration: Site URL https://minhateia.vercel.app ; Redirect URLs https://minhateia.vercel.app/**
3. Ative Manual linking (quem usava o acesso anônimo poderá salvar a conta).
4. SMTP próprio (o padrão é limitado e só envia a membros do time).

Google Cloud (ID do cliente OAuth, tipo Web):
- Origem JavaScript: https://minhateia.vercel.app
- URI de redirecionamento: https://sdubzubcfizfvgbsuucw.supabase.co/auth/v1/callback
