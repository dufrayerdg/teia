-- Agendador dos lembretes: a cada 5 minutos chama a função "lembretes".
-- Os segredos (chave privada VAPID e senha do agendador) ficam no Vault, criados à parte:
--   select vault.create_secret('<chave privada VAPID>', 'teia_vapid_privada');
--   select vault.create_secret('<chave pública VAPID>', 'teia_vapid_publica');
--   select vault.create_secret('<senha aleatória>',      'teia_cron');
create extension if not exists pg_cron;
create extension if not exists pg_net;

create or replace function public.segredos_lembretes() returns jsonb
language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'cron',          (select decrypted_secret from vault.decrypted_secrets where name = 'teia_cron'),
    'vapid_publica', (select decrypted_secret from vault.decrypted_secrets where name = 'teia_vapid_publica'),
    'vapid_privada', (select decrypted_secret from vault.decrypted_secrets where name = 'teia_vapid_privada'));
$$;
revoke all on function public.segredos_lembretes() from public, anon, authenticated;
grant execute on function public.segredos_lembretes() to service_role;

select cron.schedule('teia-lembretes', '*/5 * * * *', $cron$
  select net.http_post(
    url := 'https://sdubzubcfizfvgbsuucw.supabase.co/functions/v1/lembretes',
    headers := jsonb_build_object('Content-Type', 'application/json',
                                  'x-teia-cron', (select decrypted_secret from vault.decrypted_secrets where name = 'teia_cron')),
    body := '{}'::jsonb, timeout_milliseconds := 20000);
$cron$);
