# Cockpit Drill-Down Acceptance

**Status:** P0 usability requirement
**Applies to:** Home, Intake, Opportunities, Companies, Activity / Needs Me

## Problem

The cockpit currently surfaces consequential counts and conclusions, but most of those surfaces are not interactive. A user can see that information exists without being able to inspect the underlying roles, decisions, evidence, sources, or activity.

That violates the glass-cockpit rule: **conclusions first; provenance one click away**.

## Required behavior

Every consequential surfaced item MUST support a direct drill-down path.

### Home
- Tier 1 count -> filtered Tier 1 opportunity set.
- Tier 2 count -> filtered Tier 2 opportunity set.
- Monitor count -> filtered Monitor opportunity set.
- Gray-zone count -> filtered gray-zone audit set.
- Needs Me count -> filtered action-required activity set.
- Priority opportunity row -> opportunity decision glass.

### Intake
- Every funnel stage -> underlying role set for that stage.
- Clear No -> hidden/rejected audit set with reason and evidence.
- Possible / Gray Zone -> gray-zone role set.
- Relevant -> surfaced relevant role set.
- Needs Data -> needs-data role set.
- Source row -> source-specific health, recent runs, counts, errors, and recent source records.
- **Every role or source record shown anywhere in Intake MUST expose a direct clickable posting/source URL when one is known.** The user must not be forced to open decision intelligence merely to reach the original job posting.
- The preferred link is the company's canonical career/ATS posting URL. A discovery-only URL may be shown secondarily when official resolution has not yet succeeded.
- A role with a known persisted canonical URL MUST NOT render without an `Open posting ↗` affordance.
- If no resolvable source URL exists, show `Source URL unavailable` explicitly. Do not silently omit the affordance.

### Opportunities
- Every role row -> full opportunity decision glass.
- Every opportunity decision glass MUST expose the canonical company job posting URL near the role identity when known, in addition to provenance links deeper in the evidence trail.
- Decision glass MUST support conclusion -> why -> evidence -> source -> confidence -> capability/policy/model/version -> changed/stale state.

### Companies
- Company row -> company aggregation view containing surfaced roles, reusable company intelligence, trajectory, stakeholders, and opportunity history.
- From company view, each opportunity MUST be drillable into its decision glass and MUST retain direct posting access.

### Activity / Needs Me
- Activity event with an entity reference -> linked entity detail.
- Action-required event -> exact action context and blocking reason.
- Events without an entity reference may remain informational.

## Interaction rules

- Drill-down must not navigate the user away from the cockpit unnecessarily.
- Prefer a stable side drawer or focused in-context detail surface.
- External job/source links intentionally open the authoritative source in a new tab.
- Every interactive count/card/row must visually signal interactivity and support keyboard activation.
- Back/close must return the user to the same filtered context.
- Loading and query failures must be explicit; no silent no-op clicks.
- Hidden/raw universes remain on-demand only and MUST NOT become the default browsing experience.
- A click target that has no implemented handler is a P0 defect, not an acceptable placeholder.

## Acceptance test

A user starting from any visible consequential number, role, company, source, or actionable activity item can reach the underlying evidence or entity in no more than two interactions, without needing to infer where the data lives.

Additionally, any Intake role whose canonical/source URL is persisted can reach the authoritative posting in **one interaction**.
