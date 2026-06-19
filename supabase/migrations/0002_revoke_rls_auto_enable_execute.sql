-- 0002_revoke_rls_auto_enable_execute.sql — MetSyn · Sprint 2 (hardening).
--
-- El advisor de seguridad de Supabase marca `public.rls_auto_enable()` (función
-- preexistente con SECURITY DEFINER) como ejecutable por `anon` y `authenticated`
-- vía /rest/v1/rpc. Revocamos EXECUTE para esos roles.
--
-- El EXECUTE se concede por defecto al pseudo-rol PUBLIC, del que `anon` y
-- `authenticated` heredan; por eso revocamos también de PUBLIC para que el
-- privilegio desaparezca de forma efectiva.

revoke execute on function public.rls_auto_enable() from public;
revoke execute on function public.rls_auto_enable() from anon;
revoke execute on function public.rls_auto_enable() from authenticated;
