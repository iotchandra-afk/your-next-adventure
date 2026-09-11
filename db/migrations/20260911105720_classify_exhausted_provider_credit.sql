-- Issue #7 live roll-forward: OpenAI reports exhausted credit as
-- type=insufficient_quota, code=credit_balance_exhausted. Treat either safe
-- classifier as a hard limit and retain all work behind a six-hour circuit.

update public.model_capacity set
  blocked_until = greatest(coalesce(blocked_until, now()), now() + interval '6 hours'),
  circuit_opened_at = coalesce(circuit_opened_at, now()),
  updated_at = now()
where (last_error_type = 'insufficient_quota'
    or last_error_code in ('insufficient_quota', 'billing_hard_limit_reached', 'credit_balance_exhausted'))
  and (last_success_at is null or last_success_at < last_throttle_at);

create or replace function public.throttle_model_capacity_v2(
  p_model_id text,
  p_holder text,
  p_delay_seconds integer,
  p_error_type text default 'unknown',
  p_error_code text default 'unknown'
) returns boolean
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  next_count integer;
  cooldown_seconds integer;
  hard_limit boolean;
begin
  select case
    when last_throttle_at is null
      or last_throttle_at < now() - interval '6 hours'
      or (last_success_at is not null and last_success_at >= last_throttle_at)
      then 1
    else least(consecutive_throttles + 1, 16)
  end into next_count
  from public.model_capacity
  where model_id = p_model_id and lease_holder = p_holder
  for update;

  if next_count is null then
    return false;
  end if;

  hard_limit := coalesce(p_error_type, '') = 'insufficient_quota'
    or coalesce(p_error_code, '') in ('insufficient_quota', 'billing_hard_limit_reached', 'credit_balance_exhausted');
  cooldown_seconds := case when hard_limit then 21600 else least(21600, greatest(
    5,
    least(p_delay_seconds, 900),
    (60 * power(2, least(next_count - 1, 8)))::integer
  )) end;

  update public.model_capacity set
    blocked_until = greatest(coalesce(blocked_until, now()), now() + make_interval(secs => cooldown_seconds)),
    consecutive_throttles = next_count,
    circuit_opened_at = case when hard_limit or next_count >= 3 then coalesce(circuit_opened_at, now()) else circuit_opened_at end,
    recent_throttles = recent_throttles + 1,
    last_throttle_at = now(),
    last_error_type = left(coalesce(nullif(p_error_type, ''), 'unknown'), 120),
    last_error_code = left(coalesce(nullif(p_error_code, ''), 'unknown'), 120),
    updated_at = now()
  where model_id = p_model_id and lease_holder = p_holder;
  return found;
end;
$$;

revoke all on function public.throttle_model_capacity_v2(text,text,integer,text,text) from public, anon, authenticated;
grant execute on function public.throttle_model_capacity_v2(text,text,integer,text,text) to service_role;
