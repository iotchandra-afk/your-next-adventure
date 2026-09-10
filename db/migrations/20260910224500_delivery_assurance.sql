-- Issue #7: shared model capacity and recovery telemetry.
-- The table is owner-readable and service-role writable. RPCs execute as caller.

create table if not exists public.model_capacity (
  model_id text primary key,
  lease_holder text,
  lease_expires_at timestamptz,
  blocked_until timestamptz,
  recent_throttles integer not null default 0,
  last_throttle_at timestamptz,
  last_success_at timestamptz,
  updated_at timestamptz not null default now()
);

alter table public.model_capacity enable row level security;
drop policy if exists owner_read on public.model_capacity;
create policy owner_read on public.model_capacity for select to authenticated
  using (private.is_app_owner());
revoke all on public.model_capacity from public, anon, authenticated;
grant select on public.model_capacity to authenticated;
grant all on public.model_capacity to service_role;

create or replace function public.acquire_model_lease(
  p_model_id text, p_holder text, p_ttl_seconds integer default 420
) returns boolean
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare acquired text;
begin
  insert into public.model_capacity(model_id, lease_holder, lease_expires_at, updated_at)
  values (p_model_id, p_holder, now() + make_interval(secs => greatest(30, least(p_ttl_seconds, 900))), now())
  on conflict(model_id) do update set
    lease_holder = excluded.lease_holder,
    lease_expires_at = excluded.lease_expires_at,
    updated_at = now()
  where (public.model_capacity.lease_holder = p_holder or public.model_capacity.lease_expires_at is null or public.model_capacity.lease_expires_at <= now())
    and (public.model_capacity.blocked_until is null or public.model_capacity.blocked_until <= now())
  returning lease_holder into acquired;
  return acquired = p_holder;
end;
$$;

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
begin
  update public.model_capacity set
    blocked_until = greatest(coalesce(blocked_until, now()), now() + make_interval(secs => greatest(5, least(p_delay_seconds, 900)))),
    recent_throttles = recent_throttles + 1,
    last_throttle_at = now(),
    updated_at = now()
  where model_id = p_model_id and lease_holder = p_holder;
  return found;
end;
$$;

create or replace function public.recover_stale_model_runs(p_timeout_minutes integer default 45)
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

revoke all on function public.acquire_model_lease(text,text,integer) from public, anon, authenticated;
revoke all on function public.release_model_lease(text,text,boolean) from public, anon, authenticated;
revoke all on function public.throttle_model_capacity(text,text,integer) from public, anon, authenticated;
revoke all on function public.recover_stale_model_runs(integer) from public, anon, authenticated;
grant execute on function public.acquire_model_lease(text,text,integer) to service_role;
grant execute on function public.release_model_lease(text,text,boolean) to service_role;
grant execute on function public.throttle_model_capacity(text,text,integer) to service_role;
grant execute on function public.recover_stale_model_runs(integer) to service_role;
