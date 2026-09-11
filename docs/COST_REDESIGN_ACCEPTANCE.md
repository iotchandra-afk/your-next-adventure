# Cost Redesign Acceptance

**Priority:** P0
**Mode while open:** `ZERO_PAID_RUNTIME`

This acceptance gate converts the current model-heavy pipeline into a sustainable cost architecture before any provider credit is restored or used.

## Required implementation

### 1. Deterministic pre-triage
Use the existing persisted paid decisions as the offline labeled corpus. Build conservative deterministic/heuristic screening that removes obvious non-target roles before Sol without materially harming known-good recall.

Required evidence:
- replay across the historical labeled corpus;
- confusion matrix by deterministic outcome;
- examples of prevented title-inflation failures such as specialist `Vice President` roles;
- known-good opportunity recall audit;
- projected percentage of canonical roles requiring Sol.

### 2. Paid-result reuse
Before a paid capability executes, check for a successful reusable result with the same material identity. Workflow reruns, state repair, deployment, or queue retries must not repurchase identical reasoning.

Required evidence:
- duplicate successful same-input calls are prevented;
- cache invalidation occurs only on material input/version change;
- previously paid outputs remain traceable and reusable after state repair.

### 3. Atomic spend reservation
The current `model_spend_allowed` zero-mode gate prevents spending now. Before bounded mode is enabled, replace/check it with atomic reservation so concurrent Sol/Astra workers cannot overshoot a global cycle/day ceiling.

Required evidence:
- two concurrent workers cannot reserve beyond the ceiling;
- failed/no-charge requests reconcile reservations correctly;
- actual charged cost and reserved cost reconcile;
- budget exhaustion leaves work queued and unchanged.

### 4. Model routing economics
- Sol only receives residual ambiguous executive-plausible roles.
- Astra only receives roles surviving positive/ambiguous prior reasoning.
- expensive intelligence runs only for surfaced Tier 1/Tier 2 or active pursuits.
- broad discovery must prefer deterministic/web/structured signal collection before any reasoning step.

### 5. Development discipline
- production backlog is never used as a development test corpus;
- live model tests use bounded golden/adversarial samples only;
- all model-calling workflows remain manual and DB-gated in zero-paid mode;
- offline fixtures/recorded results drive normal CI.

## Economics gate

Before requesting paid-runtime approval, prove using offline replay/projection:

- representative universe: at least 1,000 roles;
- known-good recall remains acceptable and every known miss is explained;
- <=10% of canonical roles require Sol, unless evidence proves a higher fraction is necessary for recall;
- <=2% require Astra;
- expensive intelligence is pursuit-gated;
- projected paid screening cost for 1,000 roles is <=$2.00;
- no duplicate unchanged paid reasoning;
- hard budget control and atomic reservation tests pass.

## One bounded live proof

Only after the offline gate passes may the system request owner approval for one bounded live validation cycle. The request must state the exact maximum spend and test corpus size.

Passing that one live proof does not authorize unlimited or scheduled paid runtime. Production-bounded economics require a separate explicit policy state.
