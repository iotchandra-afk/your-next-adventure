-- Atomic global budget reservation for every future paid provider request.
-- The policy remains closed; this migration does not enable any paid mode.

create table if not exists public.model_spend_reservations (
  id uuid primary key default gen_random_uuid(),
  request_key text not null unique,
  capability text not null,
  model_id text not null,
  model_run_id uuid references public.model_runs(id),
  reserved_usd numeric(10,4) not null check (reserved_usd > 0),
  actual_usd numeric(10,4) check (actual_usd is null or actual_usd >= 0),
  status text not null default 'RESERVED' check (status in ('RESERVED','RECONCILED','RELEASED','EXPIRED')),
  outcome text check (outcome is null or outcome in ('CHARGED','NO_CHARGE','UNCERTAIN')),
  cycle_started_at timestamptz not null,
  reserved_at timestamptz not null default now(),
  expires_at timestamptz not null,
  reconciled_at timestamptz
);

create index if not exists model_spend_reservations_budget_idx
  on public.model_spend_reservations (status, reserved_at, cycle_started_at);

-- A second worker may race between cache lookup and claim. The database rejects
-- the duplicate RUNNING/PASSED identity before either worker can reserve spend.
create unique index if not exists model_runs_paid_identity_once_idx
  on public.model_runs (
    capability,
    coalesce(opportunity_id, '00000000-0000-0000-0000-000000000000'::uuid),
    input_hash,
    policy_version,
    output_schema_version
  )
  where input_hash is not null and status in ('RUNNING','PASSED');

alter table public.model_spend_reservations enable row level security;
revoke all on table public.model_spend_reservations from public, anon, authenticated;
grant select, insert, update on table public.model_spend_reservations to service_role;

create or replace function public.reserve_model_spend(
  p_request_key text,
  p_capability text,
  p_model_id text,
  p_reserved_usd numeric,
  p_model_run_id uuid default null,
  p_ttl_seconds integer default 900
)
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_policy public.model_spend_policy%rowtype;
  v_existing public.model_spend_reservations%rowtype;
  v_cycle_committed numeric(10,4);
  v_day_committed numeric(10,4);
  v_id uuid;
begin
  if p_request_key is null or btrim(p_request_key) = '' or p_reserved_usd is null or p_reserved_usd <= 0 then
    return jsonb_build_object('allowed', false, 'reason', 'INVALID_RESERVATION');
  end if;

  -- One canonical policy row is the global mutex. Concurrent workers cannot both
  -- observe the same remaining budget and oversubscribe it.
  select * into v_policy from public.model_spend_policy where id = 1 for update;
  if not found or not v_policy.paid_runtime_enabled
     or (p_model_id = 'gpt-5.6-sol' and not v_policy.sol_enabled)
     or (p_model_id = 'gpt-6-astra' and not v_policy.astra_enabled)
     or p_model_id not in ('gpt-5.6-sol','gpt-6-astra') then
    return jsonb_build_object('allowed', false, 'reason', 'PAID_RUNTIME_DISABLED');
  end if;

  select * into v_existing from public.model_spend_reservations where request_key = p_request_key;
  if found then
    return jsonb_build_object(
      'allowed', false,
      'reason', 'REQUEST_ALREADY_RESERVED',
      'reservation_id', v_existing.id,
      'status', v_existing.status
    );
  end if;

  update public.model_spend_reservations
     set status = 'EXPIRED', outcome = 'UNCERTAIN', actual_usd = reserved_usd, reconciled_at = now()
   where status = 'RESERVED' and expires_at <= now();

  select coalesce(sum(case when status = 'RESERVED' then reserved_usd else actual_usd end), 0)
    into v_cycle_committed
    from public.model_spend_reservations
   where reserved_at >= v_policy.cycle_started_at and status in ('RESERVED','RECONCILED','EXPIRED');
  select coalesce(sum(case when status = 'RESERVED' then reserved_usd else actual_usd end), 0)
    into v_day_committed
    from public.model_spend_reservations
   where reserved_at >= date_trunc('day', now()) and status in ('RESERVED','RECONCILED','EXPIRED');

  if v_cycle_committed + p_reserved_usd > v_policy.validation_cycle_budget_usd
     or v_day_committed + p_reserved_usd > v_policy.validation_daily_budget_usd then
    return jsonb_build_object('allowed', false, 'reason', 'BUDGET_EXHAUSTED');
  end if;

  insert into public.model_spend_reservations (
    request_key, capability, model_id, model_run_id, reserved_usd,
    cycle_started_at, expires_at
  ) values (
    p_request_key, p_capability, p_model_id, p_model_run_id, round(p_reserved_usd, 4),
    v_policy.cycle_started_at, now() + make_interval(secs => greatest(30, least(p_ttl_seconds, 3600)))
  ) returning id into v_id;

  return jsonb_build_object('allowed', true, 'reason', 'RESERVED', 'reservation_id', v_id);
end;
$$;

create or replace function public.reconcile_model_spend(
  p_reservation_id uuid,
  p_actual_usd numeric,
  p_outcome text
)
returns boolean
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_row public.model_spend_reservations%rowtype;
begin
  if p_outcome not in ('CHARGED','NO_CHARGE','UNCERTAIN') then
    return false;
  end if;
  select * into v_row from public.model_spend_reservations where id = p_reservation_id for update;
  if not found then return false; end if;
  if v_row.status <> 'RESERVED' then return v_row.status in ('RECONCILED','RELEASED','EXPIRED'); end if;

  update public.model_spend_reservations set
    actual_usd = case
      when p_outcome = 'NO_CHARGE' then 0
      when p_outcome = 'UNCERTAIN' then reserved_usd
      else greatest(0, coalesce(p_actual_usd, reserved_usd))
    end,
    status = case when p_outcome = 'NO_CHARGE' then 'RELEASED' else 'RECONCILED' end,
    outcome = p_outcome,
    reconciled_at = now()
  where id = p_reservation_id;
  return true;
end;
$$;

revoke all on function public.reserve_model_spend(text,text,text,numeric,uuid,integer) from public, anon, authenticated;
revoke all on function public.reconcile_model_spend(uuid,numeric,text) from public, anon, authenticated;
grant execute on function public.reserve_model_spend(text,text,text,numeric,uuid,integer) to service_role;
grant execute on function public.reconcile_model_spend(uuid,numeric,text) to service_role;

create or replace function public.model_spend_telemetry()
returns jsonb
language sql
security invoker
set search_path = public, pg_temp
as $$
  with policy as (
    select * from public.model_spend_policy where id = 1
  ), committed as (
    select
      coalesce(sum(case when r.status = 'RESERVED' then r.reserved_usd else r.actual_usd end)
        filter (where r.reserved_at >= p.cycle_started_at and r.status in ('RESERVED','RECONCILED','EXPIRED')), 0) cycle_usd,
      coalesce(sum(case when r.status = 'RESERVED' then r.reserved_usd else r.actual_usd end)
        filter (where r.reserved_at >= date_trunc('day', now()) and r.status in ('RESERVED','RECONCILED','EXPIRED')), 0) day_usd,
      count(*) filter (where r.status = 'RESERVED') reserved_count,
      count(*) filter (where r.status = 'EXPIRED') uncertain_count
    from policy p left join public.model_spend_reservations r on true
    group by p.cycle_started_at
  )
  select jsonb_build_object(
    'mode', p.mode,
    'paid_runtime_enabled', p.paid_runtime_enabled,
    'cycle', jsonb_build_object('committed_usd', c.cycle_usd, 'ceiling_usd', p.validation_cycle_budget_usd,
      'remaining_usd', greatest(0, p.validation_cycle_budget_usd - c.cycle_usd)),
    'day', jsonb_build_object('committed_usd', c.day_usd, 'ceiling_usd', p.validation_daily_budget_usd,
      'remaining_usd', greatest(0, p.validation_daily_budget_usd - c.day_usd)),
    'reserved_count', c.reserved_count,
    'uncertain_count', c.uncertain_count
  ) from policy p cross join committed c;
$$;

revoke all on function public.model_spend_telemetry() from public, anon, authenticated;
grant execute on function public.model_spend_telemetry() to service_role;

create or replace function public.deterministic_pretriage_v3(p_title text)
returns jsonb
language plpgsql
immutable
security invoker
set search_path = public, pg_temp
as $$
declare
  v_title text := regexp_replace(lower(trim(coalesce(p_title,''))), '[^a-z0-9]+', ' ', 'g');
  v_altitude boolean;
  v_target boolean;
begin
  if v_title ~ '\m(sales development representative|business development representative|administrative assistant|executive assistant|intern|internship|cashier)\M'
     or v_title ~ '\mwarehouse (associate|worker)\M' then
    return jsonb_build_object('stage','TRIAGE_CLEAR_NO','visibility','HIDDEN','reason_code','CLEAR_NON_TARGET_TITLE','confidence',0.99);
  end if;
  if v_title ~ '\m(chief|ceo|coo|cio|cto|cdo|cdao|caio|general manager|managing director|global head|head of|executive director|svp|evp)\M' then
    return jsonb_build_object('stage','ELIGIBLE','visibility','HIDDEN','reason_code','RESIDUAL_EXECUTIVE_AMBIGUITY','confidence',0.72);
  end if;
  v_altitude := v_title ~ '\m(vice president|vp|svp|evp|senior director|sr director|director|head|chief|president|partner)\M';
  v_target := v_title ~ '\m(transformation|digital strategy|product|portfolio lead|operations|automation|enterprise platform|ai software engineering|ai and software engineering|applied ai|client engagement|data product|digital assets|revenue operations|network strategy|partnerships operations|application engineer|application engineering|infrastructure engineering|data science engineering|enterprise architect|technology relationship|strategy and|governance|data management|devops|implementation consultant|reliability engineering|engineering team)\M';
  if (v_altitude and v_target) or v_title ~ '\m(client partner|senior product manager)\M' then
    return jsonb_build_object('stage','ELIGIBLE','visibility','HIDDEN','reason_code','RESIDUAL_MANDATE_AMBIGUITY','confidence',0.68);
  end if;
  if v_altitude then
    return jsonb_build_object('stage','TRIAGE_CLEAR_NO','visibility','HIDDEN','reason_code','TITLE_INFLATED_SPECIALIST','confidence',0.97);
  end if;
  return jsonb_build_object('stage','TRIAGE_CLEAR_NO','visibility','HIDDEN','reason_code','BELOW_EXECUTIVE_MANDATE','confidence',0.98);
end;
$$;

create or replace function public.reconcile_deterministic_pretriage_v3()
returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_reconciled integer;
  v_eligible integer;
  v_clear_no integer;
begin
  with candidates as (
    select o.id, o.title, public.deterministic_pretriage_v3(o.title) result
    from public.opportunities o
    where o.lifecycle_state = 'ACTIVE' and o.visibility = 'HIDDEN'
      and o.screening_stage in ('NORMALIZED','ELIGIBLE')
      and o.policy_version is distinct from 'screening-v3-residual-ambiguity'
  ), inserted as (
    insert into public.screening_decisions (
      opportunity_id, stage, outcome, reason_code, reason_text, confidence,
      evidence, policy_version, evaluator_type
    )
    select id, 'DETERMINISTIC_ELIGIBILITY', result->>'stage', result->>'reason_code',
      case when result->>'stage' = 'ELIGIBLE'
        then 'Retained for paid triage because executive-mandate ambiguity remains.'
        else 'Resolved before paid triage by the conservative deterministic gate.' end,
      (result->>'confidence')::numeric,
      jsonb_build_array(jsonb_build_object('type','TITLE','value',title,'gate','deterministic_pretriage_v3')),
      'screening-v3-residual-ambiguity', 'DETERMINISTIC'
    from candidates returning opportunity_id, outcome
  ), updated as (
    update public.opportunities o set
      screening_stage = c.result->>'stage', visibility = c.result->>'visibility',
      current_reason_code = c.result->>'reason_code',
      current_reason_text = case when c.result->>'stage' = 'ELIGIBLE'
        then 'Retained for paid triage because executive-mandate ambiguity remains.'
        else 'Resolved before paid triage by the conservative deterministic gate.' end,
      current_confidence = (c.result->>'confidence')::numeric,
      policy_version = 'screening-v3-residual-ambiguity', updated_at = now()
    from candidates c where o.id = c.id returning c.result->>'stage' stage
  )
  select count(*), count(*) filter (where stage='ELIGIBLE'), count(*) filter (where stage='TRIAGE_CLEAR_NO')
    into v_reconciled, v_eligible, v_clear_no from updated;
  return jsonb_build_object('reconciled',v_reconciled,'eligible_for_sol',v_eligible,'deterministic_clear_no',v_clear_no);
end;
$$;

create or replace function public.offline_economics_replay_v3()
returns jsonb
language sql
security invoker
set search_path = public, pg_temp
as $$
  with latest as (
    select distinct on (opportunity_id) opportunity_id, outcome
    from public.screening_decisions where stage='MANDATE_RELEVANCE_TRIAGE'
    order by opportunity_id, created_at desc
  ), classified as (
    select o.id, coalesce(l.outcome,'UNLABELED') label,
      public.deterministic_pretriage_v3(o.title)->>'stage' gate
    from public.opportunities o left join latest l on l.opportunity_id=o.id
  ), counts as (
    select count(*) total,
      count(*) filter (where gate='TRIAGE_CLEAR_NO') eliminated,
      count(*) filter (where gate='ELIGIBLE') sol,
      count(*) filter (where label in ('RELEVANT','POSSIBLE')) known_good,
      count(*) filter (where label in ('RELEVANT','POSSIBLE') and gate='ELIGIBLE') retained_good,
      count(*) filter (where label='RELEVANT' and gate='ELIGIBLE') astra
    from classified
  ), costs as (
    select
      coalesce(avg(estimated_cost_usd) filter (where capability='RELEVANCE_TRIAGE' and model_id='gpt-5.6-sol' and status='PASSED'),0) sol_unit,
      coalesce(avg(estimated_cost_usd) filter (where capability='DEEP_QUALIFICATION' and model_id='gpt-6-astra' and status='PASSED'),0) astra_unit
    from public.model_runs
  ), matrix as (
    select jsonb_object_agg(gate, labels) value from (
      select gate, jsonb_object_agg(label,n) labels from (
        select gate,label,count(*) n from classified group by gate,label
      ) x group by gate
    ) y
  )
  select jsonb_build_object(
    'representative_roles',n.total,
    'deterministic_elimination_count',n.eliminated,
    'deterministic_elimination_rate',round(n.eliminated::numeric/nullif(n.total,0),6),
    'known_good_count',n.known_good,
    'known_good_retained',n.retained_good,
    'known_good_recall',round(n.retained_good::numeric/nullif(n.known_good,0),6),
    'false_negative_count',n.known_good-n.retained_good,
    'confusion_matrix_by_gate',m.value,
    'projected_sol_count',n.sol,
    'projected_sol_fraction',round(n.sol::numeric/nullif(n.total,0),6),
    'projected_astra_count',n.astra,
    'projected_astra_fraction',round(n.astra::numeric/nullif(n.total,0),6),
    'historical_sol_unit_cost_usd',round(c.sol_unit,6),
    'historical_astra_unit_cost_usd',round(c.astra_unit,6),
    'projected_paid_screening_cost_per_1000_usd',round((1000*n.sol::numeric/nullif(n.total,0))*c.sol_unit,4),
    'projected_downstream_astra_cost_per_1000_usd',round((1000*n.astra::numeric/nullif(n.total,0))*c.astra_unit,4)
  ) from counts n cross join costs c cross join matrix m;
$$;

revoke all on function public.deterministic_pretriage_v3(text) from public, anon, authenticated;
revoke all on function public.reconcile_deterministic_pretriage_v3() from public, anon, authenticated;
revoke all on function public.offline_economics_replay_v3() from public, anon, authenticated;
grant execute on function public.deterministic_pretriage_v3(text) to service_role;
grant execute on function public.reconcile_deterministic_pretriage_v3() to service_role;
grant execute on function public.offline_economics_replay_v3() to service_role;
