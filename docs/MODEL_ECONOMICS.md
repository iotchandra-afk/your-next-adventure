# Model Economics Contract

**Status:** NORMATIVE
**Current mode:** `ZERO_PAID_RUNTIME`

## Objective

YourNextAdventure must not require premium-model spend proportional to the raw job universe. Paid reasoning is reserved for uncertainty and decision value, not routine volume.

The economic architecture is:

> deterministic discovery/normalization/screening -> bounded Sol ambiguity resolution -> Astra only for qualified high-value opportunities -> deep intelligence only for active pursuits.

## Current zero-paid-runtime rule

Until the bounded-economics acceptance gate below passes:

- scheduled paid-model workflows MUST remain disabled;
- the shared runtime spend gate MUST reject paid Sol/Astra inference before a provider request is made;
- deterministic intake, normalization, dedupe, canonicalization, source health, UI work, tests, and offline fixtures MAY continue;
- live paid-model smoke/eval runs are prohibited unless the owner explicitly approves a bounded validation budget;
- adding OpenAI credits does not itself authorize paid runtime;
- no worker may treat available provider credit as permission to spend it.

## Cost hierarchy

### Tier 0 — deterministic, target $0 model spend
Use for:
- source polling and signal ingestion;
- normalization and canonicalization;
- duplicate collapse;
- location/work-authorization checks where explicit;
- obvious level/function/specialist exclusions with high-confidence rules;
- static provenance and freshness checks;
- cached-state reuse.

The deterministic layer must remain conservative. It may not improve cost by creating false negatives.

### Tier 1 — Sol only for residual ambiguity
Sol may run only when a role survives Tier 0 and the mandate cannot be classified confidently from deterministic evidence.

Target steady-state model-triage rate: **<=10% of canonical active roles**, subject to known-opportunity recall proving that the threshold does not suppress valuable mandates.

### Tier 2 — Astra qualification
Astra qualification may run only after a role receives a positive/ambiguous Sol triage outcome that makes deeper reasoning economically rational.

Target rate: **<=2% of canonical active roles**.

### Tier 3 — expensive intelligence
Company trajectory, stakeholder context, hiring-manager commercial pressure, Core X, Two-Notch-Up, positioning, and similar deep intelligence run only for:
- surfaced Tier 1/Tier 2 opportunities; or
- an explicitly activated pursuit.

They MUST NOT run speculatively across the broad candidate universe.

## No-repeat rule

A successful paid capability result MUST be reusable while all material inputs are unchanged.

The cache identity includes at least:
- capability + capability version;
- opportunity/company identity;
- normalized input hash;
- candidate-truth version when relevant;
- pursuit-policy version;
- material source freshness/version.

A worker MUST NOT purchase the same reasoning again merely because a workflow reran or canonical state was repaired. Recompute only when a material input changed or the prior output is explicitly invalidated with evidence.

## Hard spend controls

Paid runtime must be protected by all of the following before it is re-enabled:

1. **Global kill switch** persisted in canonical runtime state.
2. **Per-cycle budget**. Default validation ceiling: `$2.00`.
3. **Per-day budget**. Default validation ceiling: `$2.00`.
4. **Model-tier switches**, including independent Astra disablement.
5. **Pre-request budget check**. Rejection happens before the provider API call.
6. **No automatic budget increase or paid-runtime enablement.** Raising a budget above the approved amount or enabling paid runtime crosses the paid-service approval boundary.
7. **Budget telemetry** visible as spent / ceiling / remaining, by capability and model.
8. **No retry spend after hard quota/billing errors.** Preserve work and stop.

## Development validation discipline

During build/debug cycles:

- use deterministic fixtures and recorded outputs by default;
- use the smallest golden/adversarial set that can falsify the change;
- do not use the full production backlog as an integration test;
- live model validation is a final bounded step, not the development loop;
- one validation cycle must stop when its approved dollar ceiling is reached even if backlog remains.

## Bounded-economics acceptance gate

Paid runtime may not resume automatically until all of the following are proven:

- at least 1,000 representative raw/canonical role records can flow through discovery, normalization, dedupe, and deterministic screening without paid inference;
- known-good opportunity recall remains acceptable under the deterministic gate, with misses explicitly audited;
- no obvious specialist/junior/non-target role reaches paid triage solely because of title inflation such as `Vice President`;
- paid Sol triage is <=10% of the representative universe or there is evidence explaining why a larger fraction is required for recall;
- Astra is <=2% of the representative universe and only downstream of a positive/ambiguous prior gate;
- deep intelligence is pursuit-gated;
- duplicate successful paid reasoning is prevented by input-hash/version reuse;
- a representative 1,000-role screening cycle has a demonstrated paid-model cost of **<= $2.00**;
- the runtime hard-stops before exceeding the approved cycle/day budget;
- cost and outcome evidence are reconciled from canonical runtime records, not inferred from code paths alone.

If the system cannot satisfy this gate without materially damaging recall, the architecture must be simplified rather than funded with a larger recurring budget.

## Spend-quality metric

Cost optimization is not `lowest dollars`. The governing metric is:

> **paid dollars per correctly retained high-value mandate**, with false-negative recall as a hard constraint.

A cheap system that misses the target role fails. An expensive system that reasons about the entire internet also fails.
