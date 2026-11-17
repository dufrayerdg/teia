-- Mais de uma pessoa cuidada por conta, consultas avulsas e papel de quem cuida.
alter table public.perfis add column if not exists papel text not null default '';

create table public.membros (
  id           text primary key default gen_random_uuid()::text,
  user_id      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  nome         text not null,
  relacao      text not null default '',
  nascimento   date,
  diagnosticos text not null default '',
  plano_saude  text not null default '',
  criado_em    timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
create index on public.membros (user_id);

create table public.consultas (
  id           text primary key default gen_random_uuid()::text,
  user_id      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  membro_id    text,
  titulo       text not null,
  data         date not null,
  hora         text not null default '',
  profissional text not null default '',
  local        text not null default '',
  obs          text not null default '',
  criado_em    timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
create index on public.consultas (user_id, data);

alter table public.medicamentos   add column if not exists membro_id text;
alter table public.tratamentos    add column if not exists membro_id text;
alter table public.tarefas        add column if not exists membro_id text;
alter table public.documentos     add column if not exists membro_id text;
alter table public.registros      add column if not exists membro_id text;
alter table public.notas_consulta add column if not exists membro_id text;

do $$ declare t text; begin
  foreach t in array array['membros','consultas'] loop
    execute format('create trigger tocar_%1$s before update on public.%1$I for each row execute function public.tocar_atualizado()', t);
    execute format('alter table public.%I enable row level security', t);
    execute format('create policy "%1$s: ler os meus" on public.%1$I for select to authenticated using ((select auth.uid()) = user_id)', t);
    execute format('create policy "%1$s: criar os meus" on public.%1$I for insert to authenticated with check ((select auth.uid()) = user_id)', t);
    execute format('create policy "%1$s: editar os meus" on public.%1$I for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id)', t);
    execute format('create policy "%1$s: apagar os meus" on public.%1$I for delete to authenticated using ((select auth.uid()) = user_id)', t);
  end loop;
end $$;

-- teia+ conferido no banco: mais de uma pessoa cuidada e perfis de outros cuidadores
create or replace function public.eh_plus(p_user uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.assinaturas a where a.user_id = p_user and a.plano = 'plus' and a.status in ('ativa','teste'));
$$;
revoke all on function public.eh_plus(uuid) from public, anon, authenticated;

-- O app salva com upsert; atualizar uma linha que já existe não conta como adicionar.
create or replace function public.limite_plano_gratis() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if public.eh_plus(new.user_id) then return new; end if;
  if tg_table_name = 'membros' then
    if exists (select 1 from public.membros m where m.id = new.id) then return new; end if;
    if (select count(*) from public.membros m where m.user_id = new.user_id) >= 1 then
      raise exception 'teia_plus_necessario' using errcode = 'P0001', hint = 'membro';
    end if;
  end if;
  if tg_table_name = 'rede' and coalesce(new.papel, '') <> 'Profissional' then
    if exists (select 1 from public.rede r where r.id = new.id) then return new; end if;
    raise exception 'teia_plus_necessario' using errcode = 'P0001', hint = 'rede';
  end if;
  return new;
end $$;
revoke all on function public.limite_plano_gratis() from public, anon, authenticated;
create trigger limite_membros before insert on public.membros for each row execute function public.limite_plano_gratis();
create trigger limite_rede before insert on public.rede for each row execute function public.limite_plano_gratis();
