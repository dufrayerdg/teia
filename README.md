# teia

App de cuidado para mães e famílias de crianças atípicas: rotina (remédios, terapias e tarefas), leitura de receitas e laudos com IA, catálogo de documentos, evolução, anotações para a consulta, conteúdos e o plano **teia+**.

## Estrutura

| Pasta | O que tem |
|---|---|
| `web/` | O app (uma página, sem build). É o que vai para o ar (Vercel ou qualquer hospedagem estática). |
| `web/config.js` | URL e chave pública do Supabase. |
| `src/` | Fonte do app (`app.template.html`) e ícones (`icons.json`, base Phosphor Icons, MIT). |
| `scripts/build_web.py` | Gera `web/index.html` a partir de `src/`, ligando o Supabase. |
| `supabase/migrations/` | Banco: tabelas, segurança (RLS), bucket de arquivos e conteúdos iniciais. |
| `supabase/functions/ia` | IA no servidor: leitura de receita/laudo, assistente e resumo do mês. Controla os limites do plano grátis. |
| `supabase/functions/assinatura` | teia+ (por enquanto só simulação, com `PAGAMENTOS_TESTE=true`). |
| `tests/` | Teste de ponta a ponta com Supabase simulado. |

## Banco de dados (Supabase)

Cada conta só enxerga os próprios dados (Row Level Security por `user_id = auth.uid()`).

- `perfis` — mãe, criança, nascimento, diagnósticos, plano de saúde, consentimento
- `medicamentos`, `tratamentos`, `tarefas`, `marcacoes` — a rotina e o que foi feito em cada dia
- `documentos` — catálogo de laudos, receitas, exames e relatórios lidos pela IA (+ arquivos no bucket privado `documentos/<user_id>/...`)
- `registros` — diário (humor, sono, crise, conquistas)
- `rede` — família e rede de apoio
- `notas_consulta` — anotações para levar à consulta (manuais ou criadas pela IA)
- `assinaturas`, `uso_ia` — plano e consumo da IA no mês (só o servidor altera)
- `conteudos` — artigos, dicas e direitos publicados pela equipe (`publicado = true` aparece no app)

## Ambiente atual

- Supabase: projeto `teia` (`sdubzubcfizfvgbsuucw`, São Paulo) com banco, RLS, bucket e as funções `ia` e `assinatura` publicados.

## Como subir (do zero)

1. **Supabase**: crie o projeto (região `sa-east-1`) e aplique as migrations de `supabase/migrations/` em ordem.
2. **Segredos das funções** (Painel → Edge Functions → Secrets):
   - `ANTHROPIC_API_KEY` — chave da API da Anthropic
   - `PAGAMENTOS_TESTE=true` — só enquanto o pagamento real não estiver ligado
   - opcionais: `MODELO_LEITURA` (padrão `claude-sonnet-5-5`), `MODELO_CONVERSA` (padrão `claude-haiku-5-5`)
3. **Funções**: `supabase functions deploy ia` e `supabase functions deploy assinatura`.
4. **Login**: em Authentication → URL Configuration, coloque o endereço do site em *Site URL* e *Redirect URLs*.
5. **Site**: preencha `web/config.js` com a URL e a chave *publishable/anon* do projeto e publique a pasta `web/` (o `vercel.json` já aponta para ela).

## Publicar um conteúdo

```sql
insert into conteudos (id, categoria, titulo, minutos, autor, corpo, publicado, publicado_em)
values ('sono-e-rotina', 'artigo', 'Sono e rotina', 4, 'Dra. Fulana (CRP 00/00000)',
        '[{"p":"Parágrafo"},{"h":"Subtítulo"},{"ul":["item 1","item 2"]}]', true, now());
```

## Desenvolvimento

```bash
python3 scripts/build_web.py          # gera web/index.html
python3 tests/test_supabase.py /tmp   # teste de ponta a ponta (Playwright)
```

Sem `config.js` preenchido o app abre em **modo de demonstração** (dados só na tela, sem IA).

## Avisos

O app organiza e explica documentos, mas não substitui a orientação de médicos e terapeutas. Dados de saúde são sensíveis (LGPD): mantenha o RLS ligado, não exponha a chave `service_role` e revise os textos de consentimento com um advogado antes do lançamento.
