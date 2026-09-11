-- Issue #7: durable per-model circuit breaker and safe provider diagnostics.
-- This is additive and keeps all queued/model work available for later retry.

alter table public.model_capacity
  add column if not exists consecutive_throttles integer not null default 0,
  add column if not exists last_error_type text,
  add column if not exists last_error_code text,
  add column if not exists circuit_opened_at timestamptz;

create or replace function public.release_model_lease(
  p_model_id text, p_holder text, p_succeeded boolean default false
) returns boolean
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  update public.model_capacity set
    lease_holder = null,
    lease_expires_at = null,
    last_success_at = case when p_succeeded then now() else last_success_at end,
    blocked_until = case when p_succeeded then null else blocked_until end,
    consecutive_throttles = case when p_succeeded then 0 else consecutive_throttles end,
    circuit_opened_at = case when p_succeeded then null else circuit_opened_at end,
    recent_throttles = case when p_succeeded and (last_throttle_at is null or last_throttle_at < now() - interval '24 hours') then 0 else recent_throttles end,
    updated_at = now()
  where model_id = p_model_id and lease_holder = p_holder;
  return found;
end;
$$;

create or replace function public.throttle_model_capacity(
  p_model_id text, p_holder text, p_delay_seconds integer
) returns boolean
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  next_count integer;
  cooldown_seconds integer;
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

  cooldown_seconds := least(21600, greatest(
    5,
    least(p_delay_seconds, 900),
    (60 * power(2, least(next_count - 1, 8)))::integer
  ));

  update public.model_capacity set
    blocked_until = greatest(coalesce(blocked_until, now()), now() + make_interval(secs => cooldown_seconds)),
    consecutive_throttles = next_count,
    circuit_opened_at = case when next_count >= 3 then coalesce(circuit_opened_at, now()) else circuit_opened_at end,
    recent_throttles = recent_throttles + 1,
    last_throttle_at = now(),
    updated_at = now()
  where model_id = p_model_id and lease_holder = p_holder;
  return found;
end;
$$;

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

  hard_limit := coalesce(p_error_code, '') in ('insufficient_quota', 'billing_hard_limit_reached');
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
