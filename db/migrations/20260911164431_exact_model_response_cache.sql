-- Exact provider-response reuse at the shared client boundary covers every model
-- path, including batches, evals, and discovery. Material input changes produce a
-- different request hash; workflow reruns do not.
create table if not exists public.model_response_cache (
  request_hash text primary key,
  capability text not null,
  model_id text not null,
  model_run_id uuid references public.model_runs(id),
  response_body jsonb not null,
  actual_cost_usd numeric(10,4) not null default 0 check (actual_cost_usd >= 0),
  created_at timestamptz not null default now(),
  last_reused_at timestamptz,
  reuse_count integer not null default 0 check (reuse_count >= 0)
);

create index if not exists model_response_cache_model_run_id_idx
  on public.model_response_cache (model_run_id) where model_run_id is not null;

alter table public.model_response_cache enable row level security;
revoke all on table public.model_response_cache from public, anon, authenticated;
grant select, insert, update on table public.model_response_cache to service_role;
