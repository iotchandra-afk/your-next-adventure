create index if not exists model_spend_reservations_model_run_id_idx
  on public.model_spend_reservations (model_run_id)
  where model_run_id is not null;
