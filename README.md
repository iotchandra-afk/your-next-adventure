# YourNextAdventure

**Status:** Planning / specification only  
**Build authorization:** **NOT GRANTED**  
**Canonical specification:** [`SPEC.md`](./SPEC.md)

YourNextAdventure is an executive opportunity intelligence and pursuit system. It is not a linear job-application pipeline and it is not primarily a resume tailor.

The system continuously discovers opportunities, qualifies whether they are worth expensive attention, determines whether the candidate is native to the mandate or must beat a native candidate, understands the company's trajectory and the hiring manager's commercial pressure, identifies the real **Core of X**, develops a future-oriented **Two-Notch-Up / Aditya Lens**, locks positioning, and only then produces or executes the artifacts and actions appropriate to that opportunity.

## Read this first

1. `SPEC.md` is the normative source of truth.
2. `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative.
3. Structured YAML blocks define component contracts.
4. Narrative text explains why the contract exists.
5. The architecture is **shared-state + event-driven**, not a forced stage conveyor belt.
6. Deterministic work should consume zero AI tokens wherever practical.
7. AI reasoning is reserved for high-value inference, judgment, red-team work, and writing.
8. Unknown consequential facts fail closed. The system does not guess.
9. A job posting may be the first visible signal, but it is not necessarily the beginning of the pursuit.
10. No implementation should begin until the specification is explicitly approved.

## Core outcome

> Continuously improve the probability that the candidate lands one of the highest-value mandates available to him, while minimizing unnecessary intervention, preserving truth and accumulated intelligence, and spending AI reasoning only where it materially improves decisions or outcomes.

## Public vs private data

This repository is designed to be safe to keep public.

**Public repository contains**
- product specification
- schemas
- decision rules
- prompt contracts
- artifact templates with placeholders
- examples that contain no personal data
- public configuration examples

**Private runtime layer contains**
- candidate identity and contact information
- resume / employment history
- verified evidence and metrics
- work authorization
- compensation policy and application answers
- private relationship data
- emails and phone numbers
- API credentials, tokens, cookies, and session secrets
- private generated artifacts where appropriate

The public code refers to private values only through stable keys such as
`${CANDIDATE_FULL_NAME}`, `${CANDIDATE_PHONE}`, and `candidate.profile.*`.

See [`PRIVATE_DATA_INJECTION.md`](./PRIVATE_DATA_INJECTION.md).

## Major components

- Intake and source resolution
- Qualification and backlog filtering
- Native-candidate / winability analysis
- Role readiness and weighted mandate analysis
- Company health, trajectory, and pain-point analysis
- Hiring-manager commercial pressure
- Stakeholder roadmap
- Two-Notch-Up / Aditya Lens
- Core of X
- Positioning lock
- Red-team loop, maximum three passes
- Two-page executive resume generation
- Hiring-manager outreach
- Contact verification, local time, and send planning
- Autonomous official-career-site application
- Core-of-X cover letter
- Optional thought-leadership one-pager
- Opportunity search and faceted filtering
- Shared-state dependency / invalidation controller
- Reliability, provenance, and auditability

## Planning references

These documents capture the current architecture, UX, and economic direction. They are **non-normative planning references** and do not override `SPEC.md`.

- [`docs/ARCHITECTURE_REFERENCE.md`](./docs/ARCHITECTURE_REFERENCE.md) — Lego architecture, modular domain core, capability contracts, adapters, reconciliation, durable execution, provider independence, observability, and 10-year durability principles.
- [`docs/GLASS_COCKPIT.md`](./docs/GLASS_COCKPIT.md) — single-pane-of-glass UX, activity stream, progressive disclosure, trust drill-down, connections, health, intervention, and product observability.
- [`docs/COST_MODEL.md`](./docs/COST_MODEL.md) — red-teamed one-time and recurring costs, staged paid-service adoption, maintenance economics, and FinOps guardrails.

## Architectural rule

The visible interface may use backlogs, cards, tabs, and status indicators. Those are projections over shared opportunity intelligence. They must not turn the underlying system into a rigid sequential workflow.

See [`SPEC.md`](./SPEC.md) for the complete contract.
