# Delivery Assurance Contract

**Status:** NORMATIVE FOR AUTONOMOUS BUILD AND RELEASE
**Applies to:** ChatGPT Work, repository-native agents, CI/evals, runtime workflows, and the deployed cockpit

## Purpose

YourNextAdventure must improve iteratively without allowing a local engineering fix to create a new product-level failure elsewhere.

The control plane already governs authority, autonomy, provenance, and iteration. This contract adds the missing layer: **cross-layer product invariants and release assurance**.

The key rule is:

> No implementation artifact, test pass, workflow success, or UI rendering may be treated as product correctness unless the relevant cross-layer invariants remain true in current runtime state and deployed behavior.

## Why this exists

Recent owner review exposed three classes of defect that can pass ordinary engineering checks:

1. a technically valid drill-down exposed an unprocessed working set as if it were meaningful user-facing opportunity intelligence;
2. a presentation fallback converted a `NULL` priority into the substantive label `NEEDS_DATA`, manufacturing a decision that did not exist in canonical state;
3. model-calling workflows could overlap, hit provider 429 limits, and leave large populations stranded between pipeline stages while the UI continued to render them.

These are not isolated UI bugs. They are failures of **semantic truth, state-machine integrity, runtime capacity control, and end-to-end release verification**.

## 1. Cross-layer invariant rule

The product MUST maintain a machine-readable invariant registry at `contracts/product_invariants.v1.json`.

Each material change MUST identify which invariants it can affect and MUST verify those invariants before claiming the slice complete.

A change that touches any of the following is automatically cross-layer:

- discovery or ingestion;
- canonicalization/deduplication;
- deterministic screening;
- relevance triage;
- deep qualification;
- model routing or model client behavior;
- workflow scheduling/concurrency;
- runtime state or migrations;
- cockpit queries, labels, badges, counts, filters, or drill-downs;
- source/provenance rendering;
- completion/checkpoint semantics.

## 2. Semantic truth rule

The UI MUST NOT infer a substantive business state from absence of data.

Specifically:

- `NULL`, missing, stale, failed, or not-yet-processed values MUST render as an explicit non-semantic state such as `AWAITING TRIAGE`, `UNPROCESSED`, `STALE`, `FAILED`, or `UNKNOWN` as appropriate;
- `NULL` MUST NOT be silently mapped to `NEEDS_DATA`, `RELEVANT`, `REJECT`, `MONITOR`, `TIER_1`, `TIER_2`, or any other decision outcome;
- labels MUST describe the exact backing state/query, not an aspirational interpretation of it;
- a count labeled `Executive eligible`, `Relevant`, `Priority`, or similar MUST have an explicit query contract proving which persisted states it represents;
- presentation code MUST NOT manufacture a decision class merely for visual convenience.

If a human-facing label could reasonably be interpreted as a recommendation or assessment, it requires a persisted assessment or an explicitly marked pending/unknown state.

## 3. Human-attention boundary

The primary human view MUST remain narrow.

Raw or partially processed roles may be inspectable in Intake for auditability, but they MUST be visually and semantically separated from qualified opportunity intelligence.

Rules:

- pre-triage roles MUST NOT appear as surfaced/relevant opportunities;
- partially processed roles MUST NOT inherit recommendation styling;
- a working-set drill-down MUST say what stage the records are actually in;
- the cockpit MUST distinguish `discovered`, `canonicalized`, `hard-screen retained`, `awaiting triage`, `triaged`, `qualified`, and `surfaced` rather than collapsing them into a single implied funnel of quality;
- when downstream reasoning is materially backlogged, user-facing recommendation counts MUST not imply that zero results means zero relevant opportunities.

## 4. State-machine integrity

Every canonical opportunity MUST have a valid state transition history.

The implementation MUST enforce:

```text
DISCOVERED
-> CANONICALIZED
-> HARD_SCREENED
-> AWAITING_TRIAGE | CLEAR_NO
-> TRIAGED_RELEVANT | TRIAGED_POSSIBLE | TRIAGED_CLEAR_NO
-> QUALIFIED / NEEDS_DATA / MONITOR / REJECT
-> SURFACED when policy permits
```

Equivalent existing enum names MAY be retained, but transition meaning must be explicit and testable.

Downstream stages MUST NOT run or render as complete before required upstream stages complete.

Each state-changing worker MUST be:

- idempotent;
- lease/claim based or otherwise duplicate-safe;
- recoverable after crash/timeout;
- explicit about retryable vs terminal failure;
- able to detect and repair stale `RUNNING` work.

A `RUNNING` model/work item older than its defined lease/timeout MUST become recoverable work, not permanent limbo.

## 5. Runtime capacity and backpressure

Provider rate limits are a system constraint and MUST be managed centrally rather than independently inside each workflow.

All model-calling execution MUST obey a shared capacity policy by model class/model ID.

Minimum required behavior:

- no two GitHub workflows may independently assume they own the same model rate budget;
- workflow-level concurrency groups MUST align with the model actually used;
- in-process worker parallelism MUST also respect the shared capacity budget;
- 429/provider-reset headers MUST reduce concurrency or delay subsequent work rather than create a retry storm;
- retries MUST use jitter/backoff and remain idempotent;
- a circuit breaker MUST stop new expensive calls during sustained throttling while retaining work for later retry;
- backlog size and oldest-unprocessed age MUST be observable;
- recovery MUST resume from durable state without duplicating decisions or model spend.

Preferred durable implementation: a shared runtime lease/token-budget mechanism in PostgreSQL/Supabase used by every model worker, with GitHub concurrency groups as an additional coarse guard rather than the sole guard.

Until that shared scheduler exists, all Sol workflows MUST serialize through the same coarse concurrency group and use conservative bounded worker counts; all Astra workflows MUST do the same for Astra.

## 6. Degraded-mode behavior

The product MUST fail safe rather than fail misleadingly.

If discovery, triage, qualification, provenance, or another consequential stage is materially unhealthy/backlogged:

- the cockpit MUST expose the degraded condition;
- affected counts/labels MUST disclose that processing is incomplete;
- unprocessed records remain auditable below the glass;
- the system MUST NOT present incomplete processing as a valid zero-result conclusion;
- the system MUST NOT substitute default recommendation labels for missing results;
- automation should continue retrying/recovering without human interruption unless a true stop condition exists.

Example: `0 relevant` while 74 roles are still awaiting triage must render as `0 processed as relevant; 74 awaiting triage`, not imply that 74 roles were assessed and none were relevant.

## 7. Change impact map

Before implementing a material slice, the runner MUST record internally which surfaces are affected:

```text
INPUT SOURCES
-> CANONICAL STATE
-> STATE TRANSITIONS
-> MODEL/RULE DECISIONS
-> USER-FACING QUERY
-> LABEL/BADGE/COUNT
-> DRILL-DOWN/EVIDENCE
-> RUNTIME CAPACITY
```

The runner MUST explicitly test both:

- what SHOULD happen; and
- what MUST NOT happen.

Negative assertions are first-class acceptance criteria.

Examples:

- a QA Engineer must not acquire a `NEEDS_DATA` badge solely because priority is null;
- a pre-triage role must not be described as relevant;
- a failed market scan must not count as market coverage success;
- a 429 must not leave indefinite `RUNNING` rows;
- broad discovery must not turn the primary cockpit into an internet dump.

## 8. Verification ladder

A material slice is not verified by one test layer.

Use the strongest applicable ladder:

1. **Contract/static checks**: schemas, enum mappings, forbidden fallbacks, configuration consistency.
2. **Unit tests**: deterministic logic and failure handling.
3. **State-transition tests**: canonical before/after records and idempotency.
4. **Golden/adversarial evals**: known good, known bad, ambiguous, and transition cases.
5. **Runtime smoke**: low-volume real model/source call where applicable.
6. **Deployed product verification**: real authenticated UI behavior and backing runtime query.
7. **Post-deploy reconciliation**: verify counts, labels, source links, backlog health, and no contradictory evidence.

A lower layer MUST NOT substitute for a higher layer when the requirement is inherently runtime or user-facing.

## 9. Independent acceptance discipline

The builder MUST NOT self-certify a material product behavior solely from the implementation it just wrote.

Acceptance must include at least one independent mechanism appropriate to the change:

- deterministic invariant test against canonical state;
- separate golden/adversarial evaluator;
- independent runtime reconciliation query;
- deployed UI/browser verification against expected backing data;
- private recall/precision probes.

The independent verifier must test the requirement from the outside of the changed implementation path where feasible.

## 10. Release/promotion rule

Routine merge/deploy remains autonomous. This contract does NOT create a new user approval gate.

Instead:

```text
IMPLEMENT
-> VERIFY AFFECTED INVARIANTS
-> RUN REQUIRED TEST/EVAL LAYERS
-> MERGE/DEPLOY AUTONOMOUSLY WHEN SAFE
-> VERIFY LIVE RUNTIME + DEPLOYED BEHAVIOR
-> RECONCILE AGAINST PRODUCT INVARIANTS
-> IF FAILURE: REPAIR/ROLL FORWARD OR SAFE ROLLBACK
-> REVERIFY
-> CONTINUE ITERATION
```

The runner MUST NOT return to the user merely because a release verification failed if it can autonomously repair, roll forward, retry, or safely roll back.

## 11. Backlog and freshness SLOs

Pipeline health must include work-in-progress age, not only connector health.

The implementation MUST expose at least:

- count awaiting triage;
- oldest awaiting-triage age;
- count awaiting qualification;
- oldest awaiting-qualification age;
- stale `RUNNING` count;
- recent provider throttling count;
- discovery last-success time;
- triage last-success time;
- qualification last-success time.

Thresholds should be conservative and configurable. Crossing a threshold changes the affected surface to `DEGRADED` and triggers autonomous remediation.

## 12. Golden product probes

Maintain a private runtime probe set representing product truth, including:

- clearly relevant executive mandates;
- clearly irrelevant/junior/specialist roles;
- ambiguous executive-plausible roles;
- roles discovered outside static source registries;
- duplicate/multi-source roles;
- stale/closed roles;
- incomplete/null-state roles;
- provider failure and recovery cases.

These probes test recall, precision, semantics, provenance, and recovery together.

No private candidate information belongs in the public repository; only generic probe archetypes and public-safe fixtures may be committed.

## 13. Definition of PASS

A checkpoint or capability may be PASS only when:

- its backing data semantics are correct;
- affected product invariants pass;
- negative assertions pass;
- runtime health is sufficient for the conclusion being shown;
- real-data behavior has been verified where applicable;
- deployed user-visible behavior matches canonical state;
- no known contradictory evidence remains.

If any of those later become false, the PASS is automatically falsified and must be reopened under `docs/ITERATION_CONTRACT.md`.

## 14. Work behavior

On every material iteration, Work MUST:

```text
READ CURRENT CONTRACTS
-> INSPECT CURRENT RUNTIME
-> BUILD CHANGE IMPACT MAP
-> CHECK PRODUCT INVARIANTS
-> IMPLEMENT HIGHEST-VALUE SLICE
-> TEST POSITIVE + NEGATIVE BEHAVIOR
-> VERIFY RUNTIME CAPACITY/STATE TRANSITIONS
-> DEPLOY WHEN SAFE
-> VERIFY DEPLOYED PRODUCT AGAINST CANONICAL STATE
-> REOPEN ANY FALSE PASS
-> PERSIST EVIDENCE
-> REITERATE
```

This is an internal loop. It must not create routine user interruptions.
