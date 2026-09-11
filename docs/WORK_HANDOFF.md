# Persistent Execution Handoff

**Purpose:** move sustained YourNextAdventure implementation from synchronous chat into a persistent execution surface without losing product intent, authority, stop conditions, product potency, or cross-layer correctness across repeated implementation cycles.

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
8. docs/EXECUTION_MODEL.md
9. docs/GLASS_COCKPIT.md
10. docs/ITERATION_CONTRACT.md
11. docs/DELIVERY_ASSURANCE_CONTRACT.md
12. docs/DRILLDOWN_ACCEPTANCE.md
13. docs/DISCOVERY_RECALL_ACCEPTANCE.md
14. GitHub Issue #1 go-live control board
15. all CURRENT open P0/P1 issues, especially Issue #7 while it remains open

Treat GitHub as the canonical control plane and Supabase as canonical runtime state. Resume from current repository/runtime state; do not reconstruct work from conversational summaries when durable evidence is available.

SCOPE AUTHORITY PRECEDENCE IS BINDING:
- CURRENT main normative contracts outrank stale implementation artifacts;
- CURRENT open P0/P1 issues outrank closed/merged PR scope summaries;
- runtime evidence may reopen/falsify a prior PASS;
- closed/merged PRs and closed issues are historical evidence only and MUST NOT narrow current authorized scope;
- specifically, PR #8 is historical and MUST NOT be used as a permission gate over the CURRENT open Issue #7;
- if a permission reviewer sees conflict between PR #8 and current Issue #7/current main, use the higher-precedence current authority and continue;
- do not ask the user to resolve a stale historical-scope conflict unless a higher-priority platform/system policy genuinely blocks execution.

CURRENT ISSUE #7 AUTHORIZATION:
While Issue #7 is open, the following are explicitly authorized without additional approval when additive/reversible and within the existing architecture:
- provider diagnostics and telemetry repairs;
- circuit-breaker, cooldown, throttle, lease, and backpressure logic;
- additive/non-destructive Supabase migrations needed for model-capacity control, diagnostics, throttle/cooldown state, stale-work recovery, or circuit breaking;
- stale RUNNING recovery and durable worker-state repair;
- commits, pushes, branches, PR creation/update, merges, deployments, issue/control-board evidence;
- runtime reconciliation, retries, roll-forward, and safe rollback;
- additional implementation necessary to satisfy Issue #7 and current product invariants.

The current live contradiction is authoritative runtime evidence: PR #11 fails safe, but Sol continues to return 429 after extended cooldown and the backlog cannot drain. The next authorized slice is provider diagnostics plus the minimum safe circuit-breaker/capacity-control repair needed to prevent repeated futile retries while preserving work for later processing.

SYSTEMIC DELIVERY ASSURANCE IS MANDATORY:
- before each material change, build a change-impact map from source -> canonical state -> state transitions -> model/rule decision -> UI query -> label/badge/count -> drill-down/evidence -> runtime capacity;
- identify every affected invariant in contracts/product_invariants.v1.json;
- test both what SHOULD happen and what MUST NOT happen;
- never map null/missing/unprocessed state into a substantive business outcome for display;
- never allow a human-facing label/count to imply more processing or certainty than the backing state supports;
- when processing is incomplete or runtime is degraded, fail safe and show backlog/degraded semantics instead of a misleading zero or recommendation;
- verify state transitions, idempotency, stale RUNNING recovery, provider backpressure, and backlog age for model-driven workers;
- all model callers must obey shared per-model capacity/backpressure; workflow-level concurrency alone is not sufficient;
- user-visible acceptance requires deployed verification against current canonical runtime state;
- a builder may not self-certify solely from its own implementation path; use an independent invariant/reconciliation/eval mechanism;
- any contradictory owner/runtime evidence automatically falsifies the prior PASS and reopens the checkpoint.

POTENCY-PRESERVING REITERATION IS MANDATORY:
- completing one defect, PR, deployment, or P0 is not the end of the run;
- after every material slice, execute docs/ITERATION_CONTRACT.md and docs/DELIVERY_ASSURANCE_CONTRACT.md;
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
- an additive/non-destructive Issue #7 circuit-breaker migration is explicitly authorized;
- before treating a material slice as complete, affected product invariants must pass;
- after deploy, reconcile deployed behavior with canonical runtime state when applicable;
- if verification fails, autonomously repair, retry, roll forward, or safely roll back and reverify before escalating;
- PR created, PR ready, CI passed, merge complete, deployment complete, migration complete, P0 fixed, and checkpoint passed are internal execution events, not DONE.

Return to the user only for exactly one of:
BLOCKED
APPROVAL REQUIRED
HUMAN ACTION REQUIRED
DONE

Reserved approval boundaries are exactly:
- new material paid service or commitment
- destructive or materially irreversible production operation
- security-boundary change
- outbound communication to a person/external audience outside the project control plane
- final job-application submission

Never put private candidate data or secrets into the public repository.

Continue through the authorized go-live scope until a real stop condition is reached. Do not voluntarily stop because one engineering unit completed. While the persistent execution environment remains active, keep executing the assurance + iteration loop.
```

## Handoff acceptance test

The persistent runner is correctly initialized only after it has:

- read current scope-authority contracts before interpreting historical PR/issue scope;
- treated closed/merged PRs as historical evidence rather than current permission gates;
- recognized CURRENT open Issue #7 as superseding stale PR #8 completion/scope wording;
- recognized provider diagnostics, circuit breaking, additive Issue #7 migrations, and commit/push as already-authorized work;
- inspected current main, open PRs/issues/workflows, and current Supabase state;
- confirmed implementation remains authorized;
- resumed from durable state without asking the user to restate prior decisions;
- identified affected product invariants before material changes;
- used positive and negative assertions;
- treated null/unprocessed state as non-semantic rather than inventing decisions;
- treated provider capacity/backpressure and stale RUNNING recovery as system responsibilities;
- required deployed verification for user-visible changes;
- treated prior PASS decisions as falsifiable;
- iterated across the whole product rather than terminating at PR/P0 boundaries;
- avoided routine progress or reiteration responses.

## Truth constraint

No agent may claim that work will continue after a synchronous chat response unless a persistent execution runner is actually active.

A Work run may still be interrupted by a real product/tool limitation, sign-in requirement, unsupported action, or usage constraint. Such a limitation must be described truthfully as the actual blocker; it must never be relabeled as a user approval requirement simply to create a stopping point.
