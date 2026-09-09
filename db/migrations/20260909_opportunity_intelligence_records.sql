-- Applied to Supabase as migration opportunity_intelligence_records.
-- Public-safe schema only; no candidate-private values are stored in this file.

create table if not exists public.intelligence_records (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  opportunity_id uuid references public.opportunities(id) on delete cascade,
  capability text not null,
  capability_version text not null,
  status text not null check (status in ('COMPLETED','FAILED','STALE')),
  payload jsonb not null default '{}'::jsonb,
  evidence jsonb not null default '[]'::jsonb,
  confidence numeric check (confidence is null or (confidence >= 0 and confidence <= 1)),
  input_hash text not null,
  policy_version text not null,
  model_class text,
  model_id text,
  reasoning_effort text,
  trace_id text,
  supersedes_id uuid references public.intelligence_records(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists intelligence_records_completed_input_uq
  on public.intelligence_records (
    company_id,
    coalesce(opportunity_id, '00000000-0000-0000-0000-000000000000'::uuid),
    capability,
    input_hash
  ) where status = 'COMPLETED';

create index if not exists intelligence_records_opportunity_capability_idx
  on public.intelligence_records(opportunity_id, capability, created_at desc);
create index if not exists intelligence_records_company_capability_idx
  on public.intelligence_records(company_id, capability, created_at desc);

alter table public.intelligence_records enable row level security;
drop policy if exists owner_access on public.intelligence_records;
create policy owner_access on public.intelligence_records for all to authenticated
  using (private.is_app_owner()) with check (private.is_app_owner());

alter table public.model_runs
  add column if not exists tool_calls jsonb not null default '[]'::jsonb,
  add column if not exists web_search_calls integer not null default 0,
  add column if not exists tool_cost_usd numeric not null default 0;
