-- Fotos de perfil e limites de uso da IA (aplicada no projeto em 2026-11-20)
alter table public.perfis  add column if not exists foto text;
alter table public.membros add column if not exists foto text;
alter table public.perfis  drop constraint if exists perfis_foto_tam;
alter table public.membros drop constraint if exists membros_foto_tam;
alter table public.perfis  add constraint perfis_foto_tam  check (foto is null or length(foto) <= 120000);
alter table public.membros add constraint membros_foto_tam check (foto is null or length(foto) <= 120000);

create table if not exists public.uso_ia_dia (
  user_id uuid not null, dia date not null,
  leituras int not null default 0, perguntas int not null default 0, resumos int not null default 0,
  primary key (user_id, dia)
);
alter table public.uso_ia_dia enable row level security;

create or replace function public.registrar_uso_ia(p_user uuid, p_tipo text)
returns void language plpgsql security definer set search_path to '' as $$
declare
  m text := to_char(now() at time zone 'America/Sao_Paulo', 'YYYY-MM');
  d date := (now() at time zone 'America/Sao_Paulo')::date;
begin
  insert into public.uso_ia (user_id, mes) values (p_user, m) on conflict do nothing;
  update public.uso_ia set leituras = leituras + (p_tipo = 'leitura')::int, perguntas = perguntas + (p_tipo = 'pergunta')::int, resumos = resumos + (p_tipo = 'resumo')::int
  where user_id = p_user and mes = m;
  insert into public.uso_ia_dia (user_id, dia) values (p_user, d) on conflict do nothing;
  update public.uso_ia_dia set leituras = leituras + (p_tipo = 'leitura')::int, perguntas = perguntas + (p_tipo = 'pergunta')::int, resumos = resumos + (p_tipo = 'resumo')::int
  where user_id = p_user and dia = d;
end $$;

create or replace function public.uso_global(p_dia date)
returns table (leituras bigint, perguntas bigint) language sql security definer set search_path to '' as $$
  select coalesce(sum(leituras), 0)::bigint, coalesce(sum(perguntas), 0)::bigint from public.uso_ia_dia where dia = p_dia
$$;
revoke execute on function public.uso_global(date) from public, anon, authenticated;
revoke execute on function public.registrar_uso_ia(uuid, text) from public, anon, authenticated;
