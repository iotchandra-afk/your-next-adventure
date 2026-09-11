# YourNextAdventure

**Status:** Active build  
**Build authorization:** **GRANTED**  
**Canonical specification:** [`SPEC.md`](./SPEC.md)  
**Autonomous execution contract:** [`AGENTS.md`](./AGENTS.md)

YourNextAdventure is an executive opportunity intelligence and pursuit system. It is not a linear job-application pipeline, a job-board mirror, or primarily a resume tailor.

The system discovers broadly below the glass, normalizes and deduplicates signals, screens conservatively for plausible executive mandates, preserves a gray zone to protect against false negatives, and surfaces only relevant opportunities for deeper qualification and pursuit.

## Read this first

1. `SPEC.md` is the normative product source of truth.
2. `AGENTS.md` is the normative autonomous execution and communication contract.
3. `contracts/execution_policy.v1.json` is the machine-readable execution policy.
4. `SPEC_MANIFEST.json` binds product requirements and agent behavior into one control plane.
5. `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative.
6. The architecture is **shared-state + event-driven**, not a forced stage conveyor belt.
7. Deterministic work should consume zero AI tokens wherever practical.
8. AI reasoning is reserved for high-value inference, judgment, red-team work, and writing.
9. Unknown consequential facts fail closed. The system does not guess.
10. A job posting may be the first visible signal, but it is not necessarily the beginning of the pursuit.
11. Implementation is authorized and currently underway.

## Execution surface: important

GitHub, the specification, the control board, CI, and Supabase provide a durable **control plane**. They preserve truth, state, authority, evidence, and recovery points.

They do **not** make a synchronous chat turn persist after the assistant sends a response.

For implementation that must continue across conversational responses, a persistent **execution plane** is required. The preferred surface is **ChatGPT Work**; a repository-native durable agent/worker is also acceptable.

Ordinary chat is therefore the steering and exception channel. See [`docs/WORK_HANDOFF.md`](./docs/WORK_HANDOFF.md) for the exact persistent-runner handoff.

## Autonomous execution rule

Within an active execution surface, the default implementation behavior is:

```text
TASK INCOMPLETE
AND no genuine blocker
AND no approval boundary
AND no human-only action
AND execution surface remains active
=> CONTINUE
```

Routine checkpoint passes, successful tests, deployments, migrations, retries, and progress updates are persisted to the control plane and do **not** require user acknowledgement.

During autonomous execution, unsolicited interruption is reserved for exactly four conditions:

- `BLOCKED`
- `APPROVAL REQUIRED`
- `HUMAN ACTION REQUIRED`
- `DONE`

See [`AGENTS.md`](./AGENTS.md) and [`docs/EXECUTION_MODEL.md`](./docs/EXECUTION_MODEL.md).

## Core outcome

> Continuously improve the probability that the candidate lands one of the highest-value mandates available, while minimizing unnecessary intervention, preserving truth and accumulated intelligence, and spending AI reasoning only where it materially improves decisions or outcomes.

## Screening principle

> **Discover broadly. Screen generously. Qualify demanding. Present narrowly.**

The raw discovery universe is machine working data, not the user experience. See [`docs/SCREENING_FUNNEL.md`](./docs/SCREENING_FUNNEL.md).

## Public vs private data

This repository is designed to remain safe to keep public.

**Public repository contains**
- product specification and architecture
- source adapters and schemas
- decision rules and prompt contracts
- tests, fixtures, and deployment workflows
- artifact templates with placeholders
- examples containing no private candidate data

**Private runtime contains**
- candidate identity and contact information
- resume / employment history and verified evidence
- work authorization and compensation policy
- application answers and private relationship data
- private artifacts and pursuit history
- API credentials, OAuth tokens, cookies, and sessions

The public code refers to private values only through stable runtime keys. See [`PRIVATE_DATA_INJECTION.md`](./PRIVATE_DATA_INJECTION.md).

## Current product surfaces

```text
Home
Intake
Opportunities
Companies
                     Activity / Needs Me ->
```

Opportunity is the default work context. Company is the aggregation context. Intake is the source-coverage and screening-control context. Backend entities do not automatically become navigation items.

## Planning and implementation references

- [`AGENTS.md`](./AGENTS.md) — normative autonomous execution, stop conditions, execution-surface truth, and communication behavior.
- [`docs/EXECUTION_MODEL.md`](./docs/EXECUTION_MODEL.md) — control-plane vs execution-plane architecture, pull visibility, and exception-driven execution.
- [`docs/WORK_HANDOFF.md`](./docs/WORK_HANDOFF.md) — exact handoff for sustained execution in ChatGPT Work or another persistent runner.
- [`docs/ARCHITECTURE_REFERENCE.md`](./docs/ARCHITECTURE_REFERENCE.md) — durable Lego architecture and provider independence.
- [`docs/SCREENING_FUNNEL.md`](./docs/SCREENING_FUNNEL.md) — broad discovery, conservative exclusion, gray-zone handling, false-negative audit, and narrow presentation.
- [`docs/GLASS_COCKPIT.md`](./docs/GLASS_COCKPIT.md) — minimum user-facing information architecture and trust drill-down.
- [`docs/COST_MODEL.md`](./docs/COST_MODEL.md) — cost and paid-service guardrails.
- [`docs/BUILD_ENABLEMENT.md`](./docs/BUILD_ENABLEMENT.md) — external dependencies and autonomy boundary.

## Current runtime direction

- GitHub: public source of truth and CI/CD control plane
- ChatGPT Work / durable agent: sustained implementation execution plane
- Replit: authorized authenticated single-user cockpit runtime
- Supabase/PostgreSQL: canonical runtime state, Auth, RLS, provenance, activity
- React + TypeScript: cockpit
- Python workers: intake and capability execution
- OpenAI: disabled in `ZERO_PAID_RUNTIME`; future bounded Sol/Astra use remains database- and owner-authorized
- Public official ATS/company endpoints: discovery before paid job feeds

## Architectural rule

The visible interface may use backlogs, cards, tabs, and status indicators. Those are projections over shared opportunity intelligence. They must not turn the underlying system into a rigid sequential workflow.
