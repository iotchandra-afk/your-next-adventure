# Persistent Execution Handoff

**Purpose:** move sustained YourNextAdventure implementation from synchronous chat into a persistent execution surface without losing product intent, authority, stop conditions, product potency, cross-layer correctness, or sustainable economics across repeated implementation cycles.

## Preferred execution surface

Use **ChatGPT Work** for sustained implementation that must continue after a conversational response.

Ordinary chat remains the steering and exception channel. GitHub remains the control plane and system of record.

## Handoff instruction

Give the persistent runner this instruction:

```text
Continue implementation of the public GitHub repository iotchandra-afk/your-next-adventure.

Before changing anything, read and obey CURRENT main, in order:
1. AGENTS.md
2. SPEC.md
3. SPEC_MANIFEST.json
4. contracts/execution_policy.v1.json
5. contracts/scope_authority.v1.json
6. docs/SCOPE_AUTHORITY.md
7. contracts/product_invariants.v1.json
8. contracts/model_economics.v1.json
9. docs/MODEL_ECONOMICS.md
10. docs/ZERO_PAID_RUNTIME_HANDOFF.md
11. docs/COST_REDESIGN_ACCEPTANCE.md
12. docs/EXECUTION_MODEL.md
13. docs/GLASS_COCKPIT.md
14. docs/ITERATION_CONTRACT.md
15. docs/DELIVERY_ASSURANCE_CONTRACT.md
16. docs/DRILLDOWN_ACCEPTANCE.md
17. docs/DISCOVERY_RECALL_ACCEPTANCE.md
18. GitHub Issue #1 go-live control board
19. all CURRENT open P0/P1 issues, especially Issue #14 while it remains open

Treat GitHub as the canonical control plane and Supabase as canonical runtime state. Resume from current repository/runtime state; do not reconstruct work from conversational summaries when durable evidence is available.

ZERO-PAID-RUNTIME ECONOMICS IS BINDING:
- current mode is ZERO_PAID_RUNTIME;
- do not invoke live Sol or Astra inference;
- do not ask the owner to restore OpenAI credits while Issue #14 remains open;
- available provider credit is not spend authority;
- scheduled paid-model workflows remain disabled;
- canonical `model_spend_policy` must remain `paid_runtime_enabled=false`, `sol_enabled=false`, and `astra_enabled=false`;
- do not raise the $2 validation cycle/day ceilings;
- deterministic intake, normalization, dedupe, source coverage, UI work, offline replay, fixtures, state-machine work, cost reconciliation, cache/reuse, and budget-control engineering MUST continue;
- mine already-paid historical `model_runs` and screening outcomes as the labeled corpus instead of buying new labels;
- build and validate deterministic pre-triage against known-good recall;
- prevent repurchase of unchanged successful reasoning;
- implement atomic spend reservation before any future bounded paid mode;
- prove the >=1,000-role / <=$2 screening economics gate offline before requesting any bounded live validation;
- after offline acceptance passes, one bounded live validation may be requested with an exact maximum dollar amount; that approval does not authorize unlimited or scheduled runtime.

SCOPE AUTHORITY PRECEDENCE IS BINDING:
- CURRENT main normative contracts outrank stale implementation artifacts;
- CURRENT open P0/P1 issues outrank closed/merged PR scope summaries;
- runtime evidence may reopen/falsify a prior PASS;
- closed/merged PRs and closed issues are historical evidence only and MUST NOT narrow current authorized scope;
- do not ask the user to resolve a stale historical-scope conflict unless a higher-priority platform/system policy genuinely blocks execution.

SYSTEMIC DELIVERY ASSURANCE IS MANDATORY:
- before each material change, build a change-impact map from source -> canonical state -> state transitions -> model/rule decision -> UI query -> label/badge/count -> drill-down/evidence -> runtime capacity -> cost authority;
- identify every affected invariant in contracts/product_invariants.v1.json and every affected economic rule in contracts/model_economics.v1.json;
- test both what SHOULD happen and what MUST NOT happen;
- never map null/missing/unprocessed state into a substantive business outcome for display;
- never allow a human-facing label/count to imply more processing or certainty than the backing state supports;
- when processing is incomplete or runtime is degraded, fail safe and show backlog/degraded semantics instead of a misleading zero or recommendation;
- verify state transitions, idempotency, stale RUNNING recovery, provider backpressure, backlog age, result reuse, and spend authority;
- a builder may not self-certify solely from its own implementation path; use an independent invariant/reconciliation/eval mechanism;
- any contradictory owner/runtime evidence automatically falsifies the prior PASS and reopens the checkpoint.

POTENCY-PRESERVING REITERATION IS MANDATORY:
- completing one defect, PR, deployment, or P0 is not the end of the run;
- after every material slice, execute docs/ITERATION_CONTRACT.md, docs/DELIVERY_ASSURANCE_CONTRACT.md, and the model-economics acceptance gate;
- re-read current authority, inspect current main/runtime/deployed product, red-team the WHOLE system, select the highest-value remaining weakness, implement it end-to-end, verify it, persist evidence, and reiterate;
- do not weaken requirements, narrow scope, substitute proxy metrics, or optimize for checklist completion merely to reach DONE;
- REITERATE is an internal action, never a user-facing status message.

IMPORTANT CONTROL-PLANE WRITE RULE:
- OUTBOUND_COMMUNICATION_SEND means human-facing communication to a person or external audience outside this project's control plane;
- repository-native PR/issue/comment/control-board writes, commits/pushes within authorized scope, and authorized Supabase runtime evidence are autonomous project-control actions when inside authorized scope, contain no prohibited private candidate data/secrets, and cross no other reserved boundary;
- do not ask the user to approve creating/updating a PR, issue, control-plane comment, checkpoint evidence, merge, or ordinary reversible GitHub Pages deployment;
- do not ask the user to approve routine commits or pushes within authorized scope.

IMPORTANT MERGE/DEPLOY/MIGRATION RULE:
- production is not by itself an approval boundary;
- routine reversible merges/deployments and additive non-destructive migrations are autonomous when within scope and safe;
- before treating a material slice as complete, affected product invariants and model-economics rules must pass;
- after deploy, reconcile deployed behavior with canonical runtime state when applicable;
- if verification fails, autonomously repair, retry, roll forward, or safely roll back and reverify before escalating;
- PR created, PR ready, CI passed, merge complete, deployment complete, migration complete, P0 fixed, and checkpoint passed are internal execution events, not DONE.

Return to the user only for exactly one of:
BLOCKED
APPROVAL REQUIRED
HUMAN ACTION REQUIRED
DONE

Reserved approval boundaries are exactly:
- new material paid service or commitment, including enabling paid runtime or increasing an approved model-spend budget
- destructive or materially irreversible production operation
- security-boundary change
- outbound communication to a person/external audience outside the project control plane
- final job-application submission

Never put private candidate data or secrets into the public repository.

Continue through the authorized go-live scope until a real stop condition is reached. Do not voluntarily stop because one engineering unit completed. While the persistent execution environment remains active, keep executing the assurance + iteration loop without paid model calls until Issue #14's offline gate is satisfied.
```

## Handoff acceptance test

The persistent runner is correctly initialized only after it has:

- recognized `ZERO_PAID_RUNTIME` as binding current authority;
- recognized that provider credit availability is not permission to spend;
- recognized Issue #14 as the current P0 economics redesign gate;
- verified scheduled paid-model workflows are disabled and canonical spend policy is closed;
- read current scope-authority contracts before interpreting historical PR/issue scope;
- treated closed/merged PRs as historical evidence rather than current permission gates;
- inspected current main, open PRs/issues/workflows, and current Supabase state;
- resumed from durable state without asking the user to restate prior decisions;
- used historical paid outcomes as offline labels before considering any new paid inference;
- identified affected product invariants and economics rules before material changes;
- used positive and negative assertions;
- treated null/unprocessed state as non-semantic rather than inventing decisions;
- required reusable successful paid outputs when material inputs have not changed;
- iterated across the whole product rather than terminating at PR/P0 boundaries;
- avoided routine progress or reiteration responses.

## Truth constraint

No agent may claim that work will continue after a synchronous chat response unless a persistent execution runner is actually active.

A Work run may still be interrupted by a real product/tool limitation, sign-in requirement, unsupported action, or usage constraint. Such a limitation must be described truthfully as the actual blocker; it must never be relabeled as a user approval requirement simply to create a stopping point.
