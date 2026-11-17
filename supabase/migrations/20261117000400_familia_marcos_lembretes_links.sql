-- Estoque, detalhes de crise, respostas, preferências; marcos; família com acesso; links para profissionais; notificações.

alter table public.medicamentos   add column if not exists estoque numeric, add column if not exists por_tomada numeric not null default 1;
alter table public.registros      add column if not exists crise_info jsonb;
alter table public.notas_consulta add column if not exists resposta text not null default '', add column if not exists respondida_em date;
alter table public.perfis         add column if not exists tour boolean not null default false, add column if not exists lembretes jsonb not null default '{}';

create table public.marcos (
  id         text primary key default gen_random_uuid()::text,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  membro_id  text,
  titulo     text not null,
  data       date not null default current_date,
  nota       text not null default '',
  foto       text not null default '',
  criado_em  timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
create index on public.marcos (user_id, data desc);
create trigger tocar_marcos before update on public.marcos for each row execute function public.tocar_atualizado();

-- ---------- família com acesso ----------
create table public.acessos (
  dono       uuid not null references auth.users(id) on delete cascade,
  convidado  uuid not null references auth.users(id) on delete cascade,
  nome       text not null default '',
  papel      text not null default '',
  criado_em  timestamptz not null default now(),
  primary key (dono, convidado)
);
create index on public.acessos (convidado);

create table public.convites (
  codigo     text primary key,
  dono       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  papel      text not null default '',
  criado_em  timestamptz not null default now(),
  expira_em  timestamptz not null default now() + interval '7 days',
  usado_por  uuid references auth.users(id) on delete set null,
  usado_em   timestamptz
);

-- quem pode ver e editar os dados de uma conta: a própria pessoa e quem ela convidou
create or replace function public.pode_acessar(p_dono uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select p_dono = (select auth.uid())
      or exists (select 1 from public.acessos a where a.dono = p_dono and a.convidado = (select auth.uid()));
$$;
revoke all on function public.pode_acessar(uuid) from public, anon;
grant execute on function public.pode_acessar(uuid) to authenticated;

-- regras novas: dono ou família
do $$ declare t text; begin
  foreach t in array array['perfis','medicamentos','tratamentos','tarefas','marcacoes','documentos','registros','rede','notas_consulta','membros','consultas','marcos'] loop
    execute format('drop policy if exists "%1$s: ler os meus" on public.%1$I', t);
    execute format('drop policy if exists "%1$s: criar os meus" on public.%1$I', t);
    execute format('drop policy if exists "%1$s: editar os meus" on public.%1$I', t);
    execute format('drop policy if exists "%1$s: apagar os meus" on public.%1$I', t);
    execute format('alter table public.%I enable row level security', t);
    execute format('create policy "%1$s: ler da família" on public.%1$I for select to authenticated using (public.pode_acessar(user_id))', t);
    execute format('create policy "%1$s: criar na família" on public.%1$I for insert to authenticated with check (public.pode_acessar(user_id))', t);
    execute format('create policy "%1$s: editar na família" on public.%1$I for update to authenticated using (public.pode_acessar(user_id)) with check (public.pode_acessar(user_id))', t);
    execute format('create policy "%1$s: apagar na família" on public.%1$I for delete to authenticated using (public.pode_acessar(user_id))', t);
  end loop;
end $$;

drop policy if exists "assinaturas: ler a minha" on public.assinaturas;
create policy "assinaturas: ler da família" on public.assinaturas for select to authenticated using (public.pode_acessar(user_id));
drop policy if exists "uso_ia: ler o meu" on public.uso_ia;
create policy "uso_ia: ler da família" on public.uso_ia for select to authenticated using (public.pode_acessar(user_id));

alter table public.acessos enable row level security;
create policy "acessos: ver os meus" on public.acessos for select to authenticated using (dono = (select auth.uid()) or convidado = (select auth.uid()));
create policy "acessos: dono remove" on public.acessos for delete to authenticated using (dono = (select auth.uid()) or convidado = (select auth.uid()));

alter table public.convites enable row level security;
create policy "convites: ver os meus" on public.convites for select to authenticated using (dono = (select auth.uid()));
create policy "convites: criar (teia+)" on public.convites for insert to authenticated with check (dono = (select auth.uid()) and public.eh_plus((select auth.uid())));
create policy "convites: apagar os meus" on public.convites for delete to authenticated using (dono = (select auth.uid()));

create or replace function public.aceitar_convite(p_codigo text, p_nome text default '') returns uuid
language plpgsql security definer set search_path = '' as $$
declare c public.convites; eu uuid := auth.uid();
begin
  if eu is null then raise exception 'nao_autenticado'; end if;
  select * into c from public.convites where codigo = upper(trim(p_codigo)) for update;
  if not found or c.usado_por is not null or c.expira_em < now() then raise exception 'convite_invalido'; end if;
  if c.dono = eu then raise exception 'convite_proprio'; end if;
  if not public.eh_plus(c.dono) then raise exception 'convite_sem_plus'; end if;
  insert into public.acessos (dono, convidado, nome, papel) values (c.dono, eu, coalesce(p_nome, ''), c.papel) on conflict (dono, convidado) do nothing;
  update public.convites set usado_por = eu, usado_em = now() where codigo = c.codigo;
  return c.dono;
end $$;
revoke all on function public.aceitar_convite(text, text) from public, anon;
grant execute on function public.aceitar_convite(text, text) to authenticated;

-- arquivos: pasta do dono, liberada para a família
drop policy if exists "documentos: ler os meus" on storage.objects;
drop policy if exists "documentos: enviar os meus" on storage.objects;
drop policy if exists "documentos: apagar os meus" on storage.objects;
create policy "documentos: ler da família" on storage.objects for select to authenticated
  using (bucket_id = 'documentos' and public.pode_acessar(((storage.foldername(name))[1])::uuid));
create policy "documentos: enviar na família" on storage.objects for insert to authenticated
  with check (bucket_id = 'documentos' and public.pode_acessar(((storage.foldername(name))[1])::uuid));
create policy "documentos: apagar na família" on storage.objects for delete to authenticated
  using (bucket_id = 'documentos' and public.pode_acessar(((storage.foldername(name))[1])::uuid));

-- ---------- link de leitura para o profissional ----------
create table public.links_profissional (
  token      text primary key,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  membro_id  text,
  criado_em  timestamptz not null default now(),
  expira_em  timestamptz not null default now() + interval '7 days',
  revogado   boolean not null default false,
  acessos    integer not null default 0
);
alter table public.links_profissional enable row level security;
create policy "links: ler da família" on public.links_profissional for select to authenticated using (public.pode_acessar(user_id));
create policy "links: criar na família" on public.links_profissional for insert to authenticated with check (public.pode_acessar(user_id) and length(token) >= 24);
create policy "links: revogar na família" on public.links_profissional for update to authenticated using (public.pode_acessar(user_id)) with check (public.pode_acessar(user_id));

-- ---------- notificações (web push) ----------
create table public.push_inscricoes (
  endpoint   text primary key,
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  dono       uuid not null references auth.users(id) on delete cascade,
  p256dh     text not null,
  auth       text not null,
  criado_em  timestamptz not null default now()
);
alter table public.push_inscricoes enable row level security;
create policy "push: ver as minhas" on public.push_inscricoes for select to authenticated using (user_id = (select auth.uid()));
create policy "push: criar a minha" on public.push_inscricoes for insert to authenticated with check (user_id = (select auth.uid()) and public.pode_acessar(dono));
create policy "push: atualizar a minha" on public.push_inscricoes for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()) and public.pode_acessar(dono));
create policy "push: apagar a minha" on public.push_inscricoes for delete to authenticated using (user_id = (select auth.uid()));

create table public.lembretes_enviados (
  chave      text primary key,
  enviado_em timestamptz not null default now()
);
alter table public.lembretes_enviados enable row level security;  -- só o servidor usa
