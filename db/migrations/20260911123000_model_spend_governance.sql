-- Sustainable economics guardrail.
-- Paid inference is disabled until bounded-economics acceptance is proven and
-- the owner explicitly authorizes a bounded paid validation budget.

create table if not exists public.model_spend_policy (
  id smallint primary key default 1 check (id = 1),
  mode text not null default 'ZERO_PAID_RUNTIME' check (mode in ('ZERO_PAID_RUNTIME','BOUNDED_VALIDATION','PRODUCTION_BOUNDED')),
  paid_runtime_enabled boolean not null default false,
  sol_enabled boolean not null default false,
  astra_enabled boolean not null default false,
  validation_cycle_budget_usd numeric(10,4) not null default 2.0000 check (validation_cycle_budget_usd >= 0),
  validation_daily_budget_usd numeric(10,4) not null default 2.0000 check (validation_daily_budget_usd >= 0),
  cycle_started_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.model_spend_policy (id, mode, paid_runtime_enabled, sol_enabled, astra_enabled)
values (1, 'ZERO_PAID_RUNTIME', false, false, false)
on conflict (id) do update set
  mode = 'ZERO_PAID_RUNTIME',
  paid_runtime_enabled = false,
  sol_enabled = false,
  astra_enabled = false,
  updated_at = now();

alter table public.model_spend_policy enable row level security;
revoke all on table public.model_spend_policy from public, anon, authenticated;
grant select, insert, update on table public.model_spend_policy to service_role;

create or replace function public.model_spend_allowed(p_model_id text)
returns boolean
language sql
security invoker
set search_path = public, pg_temp
as $$
  with policy as (
    select * from public.model_spend_policy where id = 1
  ), spend as (
    select
      coalesce(sum(coalesce(estimated_cost_usd,0) + coalesce(tool_cost_usd,0)) filter (where status = 'PASSED' and finished_at >= (select cycle_started_at from policy)), 0) as cycle_spend,
      coalesce(sum(coalesce(estimated_cost_usd,0) + coalesce(tool_cost_usd,0)) filter (where status = 'PASSED' and finished_at >= date_trunc('day', now())), 0) as daily_spend
    from public.model_runs
  )
  select coalesce(
    p.paid_runtime_enabled
    and case
      when p_model_id = 'gpt-5.6-sol' then p.sol_enabled
      when p_model_id = 'gpt-6-astra' then p.astra_enabled
      else false
    end
    and s.cycle_spend < p.validation_cycle_budget_usd
    and s.daily_spend < p.validation_daily_budget_usd,
    false
  )
  from policy p cross join spend s;
$$;

revoke all on function public.model_spend_allowed(text) from public, anon, authenticated;
grant execute on function public.model_spend_allowed(text) to service_role;
