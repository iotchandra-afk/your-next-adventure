# Zero-Paid-Runtime Build Handoff

Use this while `contracts/model_economics.v1.json` is in `ZERO_PAID_RUNTIME` mode.

## Execution objective

Continue building the system without purchasing Sol/Astra inference. The current goal is to make the economics correct before restoring API credits.

## Work that MUST continue

- deterministic intake, normalization, canonicalization, dedupe, source coverage, and provenance;
- offline analysis of existing persisted model outcomes;
- deterministic pre-triage design using historical labeled outcomes as the evaluation corpus;
- duplicate-reasoning prevention and input-hash reuse;
- spend-policy enforcement, telemetry, and budget reservation design;
- fixtures, contract tests, state-transition tests, UI work, and deployed verification that require no paid inference;
- recall probes using already-known/persisted opportunities;
- cost reconciliation from `model_runs`;
- failure recovery, queue semantics, and cockpit truthfulness.

## Work that MUST NOT happen

- no live Sol/Astra inference;
- no live model golden eval;
- no broad-market discovery path that invokes a paid model;
- no automated attempt to restore/buy provider credit;
- no speculative deep intelligence;
- no full-backlog model run;
- no changing `model_spend_policy.paid_runtime_enabled` or model-tier switches to true;
- no raising the `$2` validation ceilings.

## Offline redesign sequence

1. Treat existing successful `model_runs` + persisted screening decisions as a free labeled corpus.
2. Quantify where deterministic screening could have removed obvious non-target roles without changing known-good retention.
3. Build conservative deterministic/heuristic rules and regression cases from those observed failure modes.
4. Re-run the entire historical corpus offline through the deterministic gate.
5. Measure:
   - share eliminated before paid triage;
   - known-good recall;
   - false-negative risk by stratum;
   - projected Sol calls and cost;
   - projected Astra calls and cost.
6. Add idempotent paid-result reuse so unchanged role/candidate/policy inputs cannot be repurchased.
7. Implement atomic spend reservation before provider calls; the current zero-mode gate is sufficient to stop spend now but is not sufficient for bounded concurrency once paid runtime resumes.
8. Prove the 1,000-role <=$2 economics gate using replay/projection first.
9. Only then request one explicit owner approval for a bounded live validation cycle.

## Resume-live criterion

The next paid test is permitted only after repository evidence shows all offline acceptance gates pass and the owner explicitly approves the bounded amount. Available OpenAI balance alone is not authorization.
