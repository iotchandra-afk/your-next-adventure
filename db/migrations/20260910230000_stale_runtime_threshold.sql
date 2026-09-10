-- Align stale-run recovery to the 30-minute worker timeout with a five-minute grace period.
create or replace function public.recover_stale_model_runs(p_timeout_minutes integer default 35)
returns integer
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare repaired integer;
begin
  update public.model_runs set
    status = 'FAILED',
    finished_at = now(),
    error_text = 'STALE_RUNNING_RECOVERED: lease exceeded; work remains eligible for idempotent retry.'
  where status = 'RUNNING'
    and started_at < now() - make_interval(mins => greatest(15, least(p_timeout_minutes, 240)));
  get diagnostics repaired = row_count;
  return repaired;
end;
$$;

revoke all on function public.recover_stale_model_runs(integer) from public, anon, authenticated;
grant execute on function public.recover_stale_model_runs(integer) to service_role;
