-- Funções de gatilho não podem ser chamadas pela API.
revoke all on function public.nova_conta() from public, anon, authenticated;
revoke all on function public.tocar_atualizado() from public, anon, authenticated;
