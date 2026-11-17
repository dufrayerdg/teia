-- teia · esquema inicial
-- Cada família (conta) só enxerga os próprios dados (RLS por user_id = auth.uid()).

create extension if not exists pgcrypto;

-- ---------- helpers ----------
create or replace function public.tocar_atualizado() returns trigger
language plpgsql set search_path = '' as $$
begin new.atualizado_em = now(); return new; end $$;

-- ---------- perfil da família ----------
create table public.perfis (
  user_id      uuid primary key references auth.users(id) on delete cascade,
  mae          text not null default '',
  crianca      text not null default '',
  nascimento   date,
  diagnosticos text not null default '',
  plano_saude  text not null default '',
  consentimento_em timestamptz,
  criado_em    timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- ---------- rotina ----------
create table public.medicamentos (
  id          text primary key default gen_random_uuid()::text,
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  nome        text not null,
  dose        text not null default '',
  horarios    text[] not null default '{}',
  inicio      date,
  fim         date,
  receita_id  text,
  medico      text not null default '',
  criado_em   timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

create table public.tratamentos (
  id          text primary key default gen_random_uuid()::text,
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  tipo        text not null,
  profissional text not null default '',
  local       text not null default '',
  dias        smallint[] not null default '{}',
  hora        text not null default '',
  meta        text not null default '',
  progresso   smallint not null default 0 check (progresso between 0 and 100),
  criado_em   timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

create table public.tarefas (
  id          text primary key default gen_random_uuid()::text,
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  titulo      text not null,
  dias        smallint[] not null default '{}',
  hora        text not null default '',
  criado_em   timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- itens da rotina marcados como feitos (remédio, sessão ou tarefa em um dia)
create table public.marcacoes (
  user_id   uuid not null default auth.uid() references auth.users(id) on delete cascade,
  dia       date not null,
  chave     text not null,
  por       text not null default '',
  hora      text not null default '',
  criado_em timestamptz not null default now(),
  primary key (user_id, dia, chave)
);

-- ---------- documentos (catálogo) ----------
create table public.documentos (
  id            text primary key default gen_random_uuid()::text,
  user_id       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  tipo          text not null default 'outro' check (tipo in ('laudo','receita','exame','relatorio','outro')),
  titulo        text not null default '',
  data          date,
  profissional  text not null default '',
  registro      text not null default '',
  especialidade text not null default '',
  origem        text not null default '',
  resumo        text not null default '',
  pontos        jsonb not null default '[]',
  termos        jsonb not null default '[]',
  recomendacoes jsonb not null default '[]',
  perguntas     jsonb not null default '[]',
  medicamentos  jsonb not null default '[]',
  arquivos      text[] not null default '{}',   -- caminhos no bucket "documentos"
  mime          text not null default '',
  lido_por_ia   boolean not null default false,
  criado_em     timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- ---------- diário e evolução ----------
create table public.registros (
  id            text primary key default gen_random_uuid()::text,
  user_id       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  data          date not null,
  humor         smallint not null default 3 check (humor between 1 and 5),
  sono          text not null default '',
  crise         boolean not null default false,
  tratamento_id text,
  conquista     text not null default '',
  nota          text not null default '',
  criado_em     timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- ---------- rede de apoio ----------
create table public.rede (
  id          text primary key default gen_random_uuid()::text,
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  nome        text not null,
  papel       text not null default '',
  contato     text not null default '',
  obs         text not null default '',
  criado_em   timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- ---------- anotações para a consulta ----------
create table public.notas_consulta (
  id          text primary key default gen_random_uuid()::text,
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  data        date not null default current_date,
  titulo      text not null,
  texto       text not null,
  para        text not null default '',
  feito       boolean not null default false,
  origem      text not null default 'manual' check (origem in ('manual','ia')),
  pergunta    text not null default '',
  criado_em   timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- ---------- teia+ (somente o servidor altera) ----------
create table public.assinaturas (
  user_id      uuid primary key references auth.users(id) on delete cascade,
  plano        text not null default 'gratis' check (plano in ('gratis','plus')),
  ciclo        text check (ciclo in ('mensal','anual')),
  status       text not null default 'ativa' check (status in ('ativa','teste','cancelada','atrasada')),
  desde        date,
  renova_em    date,
  gateway      text,
  gateway_id   text,
  atualizado_em timestamptz not null default now()
);

create table public.uso_ia (
  user_id    uuid not null references auth.users(id) on delete cascade,
  mes        text not null,                 -- 'AAAA-MM'
  leituras   integer not null default 0,
  perguntas  integer not null default 0,
  resumos    integer not null default 0,
  primary key (user_id, mes)
);

-- ---------- conteúdos (publicados pela equipe) ----------
create table public.conteudos (
  id         text primary key,
  categoria  text not null check (categoria in ('artigo','noticia','video','dica','direitos')),
  titulo     text not null,
  minutos    smallint not null default 3,
  autor      text not null default 'Equipe teia',
  profissional_registro text not null default '',
  corpo      jsonb not null default '[]',
  video_url  text,
  destaque   boolean not null default false,
  publicado  boolean not null default false,
  publicado_em timestamptz,
  criado_em  timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- ---------- índices ----------
create index on public.medicamentos (user_id);
create index on public.tratamentos (user_id);
create index on public.tarefas (user_id);
create index on public.documentos (user_id, data desc);
create index on public.registros (user_id, data desc);
create index on public.rede (user_id);
create index on public.notas_consulta (user_id, feito);
create index on public.conteudos (publicado, publicado_em desc);

-- ---------- atualizado_em automático ----------
do $$ declare t text; begin
  foreach t in array array['perfis','medicamentos','tratamentos','tarefas','documentos','registros','rede','notas_consulta','assinaturas','conteudos'] loop
    execute format('create trigger tocar_%1$s before update on public.%1$I for each row execute function public.tocar_atualizado()', t);
  end loop;
end $$;

-- ---------- segurança (RLS) ----------
do $$ declare t text; begin
  foreach t in array array['perfis','medicamentos','tratamentos','tarefas','marcacoes','documentos','registros','rede','notas_consulta'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('create policy "%1$s: ler os meus" on public.%1$I for select to authenticated using ((select auth.uid()) = user_id)', t);
    execute format('create policy "%1$s: criar os meus" on public.%1$I for insert to authenticated with check ((select auth.uid()) = user_id)', t);
    execute format('create policy "%1$s: editar os meus" on public.%1$I for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id)', t);
    execute format('create policy "%1$s: apagar os meus" on public.%1$I for delete to authenticated using ((select auth.uid()) = user_id)', t);
  end loop;
end $$;

alter table public.assinaturas enable row level security;
create policy "assinaturas: ler a minha" on public.assinaturas for select to authenticated using ((select auth.uid()) = user_id);

alter table public.uso_ia enable row level security;
create policy "uso_ia: ler o meu" on public.uso_ia for select to authenticated using ((select auth.uid()) = user_id);

alter table public.conteudos enable row level security;
create policy "conteudos: publicados para todos" on public.conteudos for select to anon, authenticated using (publicado);

-- ---------- conta nova: cria a assinatura grátis ----------
create or replace function public.nova_conta() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.assinaturas (user_id, plano) values (new.id, 'gratis') on conflict do nothing;
  return new;
end $$;
create trigger ao_criar_conta after insert on auth.users for each row execute function public.nova_conta();

-- ---------- contador de uso da IA (chamado só pela Edge Function) ----------
create or replace function public.registrar_uso_ia(p_user uuid, p_tipo text) returns void
language plpgsql security definer set search_path = '' as $$
declare m text := to_char(now() at time zone 'America/Sao_Paulo', 'YYYY-MM');
begin
  insert into public.uso_ia (user_id, mes) values (p_user, m) on conflict do nothing;
  update public.uso_ia set
    leituras  = leituras  + (p_tipo = 'leitura')::int,
    perguntas = perguntas + (p_tipo = 'pergunta')::int,
    resumos   = resumos   + (p_tipo = 'resumo')::int
  where user_id = p_user and mes = m;
end $$;
revoke all on function public.registrar_uso_ia(uuid, text) from public, anon, authenticated;

-- ---------- arquivos originais (fotos e PDFs) ----------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('documentos', 'documentos', false, 15728640, array['image/jpeg','image/png','image/webp','image/heic','application/pdf'])
on conflict (id) do nothing;

create policy "documentos: ler os meus" on storage.objects for select to authenticated
  using (bucket_id = 'documentos' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "documentos: enviar os meus" on storage.objects for insert to authenticated
  with check (bucket_id = 'documentos' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "documentos: apagar os meus" on storage.objects for delete to authenticated
  using (bucket_id = 'documentos' and (storage.foldername(name))[1] = (select auth.uid())::text);
