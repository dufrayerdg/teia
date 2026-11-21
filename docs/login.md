# Login (Google + e-mail)

Supabase (Authentication):
1. Providers: ative Email (magic link) e Google (Client ID e Secret); mantenha **Anonymous sign-ins ATIVO** (é o "Explorar sem criar conta").
2. URL Configuration: Site URL https://minhateia.vercel.app ; Redirect URLs https://minhateia.vercel.app/**
3. Ative Manual linking (quem usava o acesso anônimo poderá salvar a conta).
4. SMTP próprio (o padrão é limitado e só envia a membros do time).

Google Cloud (ID do cliente OAuth, tipo Web):
- Origem JavaScript: https://minhateia.vercel.app
- URI de redirecionamento: https://sdubzubcfizfvgbsuucw.supabase.co/auth/v1/callback

## E-mail com código (6 dígitos)
Em Authentication > Emails > Templates, nos modelos "Magic link" e "Confirm signup" (e "Change email address"), inclua o código no corpo:

    <p>Seu código da teia: <b>{{ .Token }}</b></p>

Em Providers > Email, deixe o tamanho do código em 6 e a validade em 600 s.
