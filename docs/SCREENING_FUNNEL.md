# Screening Funnel Contract

**Status:** Locked implementation direction

## Core principle

> **Discover broadly. Screen generously. Qualify demanding. Present narrowly.**

The product must never turn broad market discovery into a human browsing burden. The machine may inspect thousands of signals. The user-facing cockpit should surface only plausible executive opportunities plus a very small gray zone that protects against false negatives.

## Five layers

```text
SIGNAL UNIVERSE
  -> NORMALIZED ROLE UNIVERSE
  -> ELIGIBLE UNIVERSE
  -> RELEVANCE TRIAGE
  -> OPPORTUNITY PORTFOLIO
```

### 1. Signal universe
All discovered source records. Machine-only by default.

### 2. Normalized role universe
Current, canonical, deduplicated roles with source provenance retained.

### 3. Eligible universe
Only deterministic, high-confidence hard exclusions are removed. Examples include stale/closed postings, clearly impossible geography, obviously junior scope, pure quota sales, or genuinely non-transferable deep-specialist requirements.

### 4. Relevance triage
Every eligible role becomes one of:
- `TRIAGE_RELEVANT`
- `TRIAGE_POSSIBLE`
- `TRIAGE_CLEAR_NO`

`TRIAGE_POSSIBLE` is a deliberate gray zone. Ambiguous but potentially valuable roles are retained for additional evidence or re-evaluation rather than silently discarded.

### 5. Opportunity portfolio
Relevant roles receive deeper qualification and may become:
- `TIER_1`
- `TIER_2`
- `MONITOR`
- `NEEDS_DATA`
- `REJECT`

## Visibility policy

- `HIDDEN`: raw/canonical/rejected universe. Retained and auditable, not part of the default cockpit.
- `GRAY_ZONE`: plausible ambiguity requiring evidence or periodic re-evaluation.
- `SURFACED`: roles that cleared relevance screening.

The default Intake and Opportunities views show `SURFACED` roles only, with gray-zone count/attention when useful. Raw source records must never be the default user experience.

## Asymmetric optimization

At the top of the funnel, optimize for **recall**. Near the user, optimize for **precision**.

- Early false positive cost: compute.
- Cockpit false positive cost: user attention.
- Early false negative cost: a potentially valuable executive opportunity disappears entirely.

Therefore, a role may be hidden only under a high-confidence exclusion or after explicit relevance triage with retained reasoning.

## False-negative audit

The system must automatically sample hidden/rejected roles using stratified sampling. Audit findings are persisted.

If the audit identifies strong roles among rejects, the screening policy must be recalibrated and the affected universe should be eligible for re-evaluation.

## Explainability

Every consequential screen or triage decision retains:
- source and source record
- policy version
- evaluator type
- reason code and reason text
- confidence
- evidence
- model class/id when a model was used
- trace id
- timestamp
- supersession link where applicable

No opaque numeric fit score is required.

## Model policy

- ingestion, normalization, dedupe, freshness, deterministic exclusion: **no model**
- standard mandate/relevance reasoning: **Sol** through `STANDARD_REASONING`
- consequential ambiguity, deep qualification, Core X, Two-Notch-Up, positioning/red-team: **Astra** through `HIGH_CONSEQUENCE_REASONING`

The router owns model selection. A model may not silently downgrade itself or substitute a cheaper model without passing the relevant evaluation suite.
