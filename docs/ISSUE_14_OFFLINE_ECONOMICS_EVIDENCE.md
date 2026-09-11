# Issue #14 Offline Economics Evidence

**Evidence date:** 2026-09-11  
**Runtime mode:** `ZERO_PAID_RUNTIME`  
**Paid provider calls during redesign:** 0

## Change-impact map

```text
official source records
-> canonical opportunities
-> append-only deterministic eligibility decisions
-> residual-ambiguity pre-triage rule
-> ELIGIBLE backlog query
-> awaiting-triage count/status
-> auditable screening decision + source provenance
-> shared model lease
-> atomic global spend reservation and reconciliation
```

Affected product invariants: `INV-001` through `INV-008`, `INV-011`, `INV-013`, `INV-014`, and `INV-015`. Affected economics rules: deterministic-first routing, known-good recall, <=10% Sol, <=2% Astra, exact successful-result reuse, pursuit-gated deep intelligence, zero-paid development, and the $2 cycle/day hard stop.

## Independent canonical replay

The database-side `offline_economics_replay_v3()` independently replayed 1,264 canonical roles using 41 already-paid `RELEVANT`/`POSSIBLE` labels. It retained all 41 known-good roles and produced zero labeled false negatives.

| Measure | Result | Gate |
|---|---:|---:|
| Deterministically eliminated | 1,175 / 1,264 (92.9589%) | high-confidence non-target only |
| Known-good recall | 41 / 41 (100%) | no known miss |
| Projected Sol | 89 / 1,264 (7.0411%) | <=10% |
| Projected Astra qualification | 8 / 1,264 (0.6329%) | <=2% |
| Projected paid screening per 1,000 | $1.6130 | <=$2.00 |

The ambiguity bucket deliberately contains 41 historical `CLEAR_NO` roles as the cost of preserving recall. Ambiguous titles are not deterministically rejected to improve precision. Conversely, `Data Engineer, Vice President`, `AI & Machine Learning Engineer, Vice President`, `Account Executive, Vice President`, actuary, operator, junior, and service roles are rejected before paid triage despite inflated title tokens.

Downstream Astra qualification is not counted as the Sol screening gate: at the historical unit cost its separate projection is $0.7759 per 1,000 raw roles. It is independently limited to 0.6329% of the universe and the same global $2 reservation ceiling. Deep intelligence now requires a surfaced Tier 1/Tier 2 record or explicit active pursuit.

## Runtime and negative proof

- Canonical repair appended new deterministic decisions and reconciled 1,174 active unprocessed roles: 1,114 clear-no and 60 residual Sol candidates. A second execution changed 0 rows.
- Zero-paid state remains closed: paid runtime, Sol, and Astra are all disabled; cycle/day ceilings remain $2.
- Two runtime reservation attempts (one Sol, one Astra) were denied before creating a reservation. No provider request was made.
- The partial unique model-run identity admitted one synthetic claim and rejected the duplicate claim; the exact synthetic row was then removed.
- Unknown/timeout charges retain their full reservation; known no-charge failures release it; successful calls reconcile actual charged cost.
- Every paid path checks a successful exact material identity, including batched triage and freshness-bucketed discovery. A database uniqueness constraint closes the cache-check/claim race.
- Normal CI and development use fixtures. Paid workflows remain manual and database-gated.

## Validation layers

- Contract/static assertions: zero-paid policy, workflow scheduling, deployment boundary, SQL grants/RLS, row lock, budget ceilings, unique paid identity.
- Unit/adversarial replay: 1,000-role fixture, known-good mandates, title-inflated specialists, no-model fail-closed behavior.
- Runtime reconciliation: 1,264 canonical roles, idempotent state repair, closed spend telemetry, no running work.
- Independent mechanism: database replay and uniqueness probe, separate from the Python classifier/replay path.

Machine-readable evidence is in `evals/issue-14-offline-economics-2026-09-11.json`.
