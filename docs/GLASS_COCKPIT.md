# Glass Cockpit Reference

**Status:** Active implementation reference  
**Canonical product contract:** [`../SPEC.md`](../SPEC.md)

## North star

> **Lego blocks underneath, glass cockpit on top.**

The cockpit must let the user understand what matters, what changed, what the system is doing, why it believes what it believes, and where human intervention is genuinely required.

## Primary information architecture

```text
Home
Intake
Opportunities
Companies
                     Activity / Needs Me ->
```

A backend entity does not earn a standalone screen merely because it exists. Opportunity is the default work context. Company is the aggregation context. Intake is the coverage/screening-control context. Activity is the operational context. People, relationships, outreach, applications, artifacts and similar entities remain contextual until a repeated cross-opportunity need proves otherwise.

## Intake is not a job dump

Broad discovery exists below the glass. Default Intake must show the funnel and only the roles that have cleared relevance screening.

Example:

```text
Signals discovered        4,811
Canonical roles           2,304
Executive eligible          187
Relevant                     31
Priority                      7
```

Raw/hidden roles remain auditable on demand. They are not the default experience.

See [`SCREENING_FUNNEL.md`](./SCREENING_FUNNEL.md).

## Two kinds of glass

### Operational glass
Answers whether the machine is functioning:
- source health
- sync freshness
- ingestion counts
- failures
- activity
- blockers
- cost

### Decision glass
Answers whether a conclusion can be trusted:
- why the role survived or was rejected
- supports / constrains
- material unknowns
- evidence used
- verified / inferred / unknown
- policy/model/version
- what changed

## Home
Home answers **What matters now?**

Show only:
- Tier 1 / Tier 2 / Monitor pulse
- genuinely new relevant roles
- meaningful changes to active pursuits
- source degradation
- Needs Me items

Do not duplicate the full Intake screen.

## Intake
Intake answers **What is the system seeing and what is it doing with it?**

Default surfaces:
- source health and last successful sync
- discovered -> canonical -> eligible -> relevant -> priority funnel
- roles that cleared relevance screening
- gray-zone count
- disposition summary

Audit drill-down may expose hidden/rejected roles, raw source records and change history, but only on demand.

## Opportunities
Opportunities answers **What should I pursue and what is happening?**

Only surfaced opportunities are shown by default. Each role should expose current assessment, priority, Core X/next action when available, blockers, source provenance, and one-click explanation.

## Companies
Companies answers **What do we know across multiple opportunities at this company?**

It aggregates reusable company intelligence, trajectory, stakeholders and opportunity history. It is not a generic CRM.

## Persistent Activity / Needs Me
Activity answers:
- Is the system alive?
- What did it just do?
- Did it work?
- Does it need me?

Prominence hierarchy:
- `INFO`
- `ATTENTION`
- `ACTION_REQUIRED`
- `ERROR`

Only the latter three should interrupt normal scanning.

## Trust drill-down

Every consequential conclusion should support:

```text
Conclusion
  -> Why
  -> Evidence
  -> Source
  -> Confidence
  -> Capability / policy / model version
  -> What changed
  -> What became stale or invalidated
```

Progressive disclosure is mandatory. The primary view shows the conclusion, not a trace dump.

## Progress verification

During build, GitHub Issue #1 is the temporary control board. Once this cockpit is live, product-level verification moves into the product itself. Engineering proof remains available through commits, CI, migrations and test artifacts.

## UX principles

1. Store richly. Surface sparingly.
2. Broad discovery must not become human browsing work.
3. Conclusions first; provenance one click away.
4. Opportunity is default context; company is aggregation context.
5. No frontend recreation of the backend relational model.
6. No animated agent-thinking theater.
7. Dense, calm, desktop-first, decision-oriented.
8. The system must expose false-negative risk without exposing the entire internet.
