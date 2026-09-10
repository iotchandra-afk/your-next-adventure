# Persistent Execution Handoff

**Purpose:** move sustained YourNextAdventure implementation from synchronous chat into a persistent execution surface without losing product intent, authority, or stop conditions.

## Preferred execution surface

Use **ChatGPT Work** for sustained implementation that must continue after a conversational response.

Ordinary chat remains the steering and exception channel. GitHub remains the control plane and system of record.

## Handoff instruction

Give the persistent runner this instruction:

```text
Continue implementation of the public GitHub repository iotchandra-afk/your-next-adventure.

Before changing anything, read and obey, in order:
1. AGENTS.md
2. SPEC.md
3. SPEC_MANIFEST.json
4. contracts/execution_policy.v1.json
5. docs/EXECUTION_MODEL.md
6. docs/GLASS_COCKPIT.md
7. docs/DRILLDOWN_ACCEPTANCE.md
8. docs/DISCOVERY_RECALL_ACCEPTANCE.md
9. GitHub Issue #1 go-live control board
10. GitHub Issue #3 P0 drill-down defect
11. GitHub Issue #4 P0 broad-market discovery recall defect

Treat GitHub as the canonical control plane and Supabase as canonical runtime state. Resume from current repository/runtime state; do not reconstruct work from conversational summaries when durable evidence is available.

CURRENT P0 PRODUCT DEFECTS FROM OWNER REVIEW:

P0-A — DRILL-DOWN / SOURCE ACCESS
- the deployed cockpit still has consequential surfaces that do not drill down;
- implement docs/DRILLDOWN_ACCEPTANCE.md completely;
- every Intake role or source record with a persisted canonical/discovery URL must expose a one-click `Open posting ↗` / source link;
- opportunity decision glass should also expose the canonical posting near the role identity;
- no visible consequential card/count/row may be a dead end.

P0-B — BROAD-MARKET DISCOVERY RECALL
- the current runtime proves several ATS adapters work but polls only a limited static employer registry;
- independently discoverable relevant executive opportunities have been missed because their companies/sources are outside that registry;
- implement docs/DISCOVERY_RECALL_ACCEPTANCE.md and Issue #4;
- add a durable DISCOVERY_SIGNAL ingestion path;
- activate market discovery independent of the static employer list;
- reconcile a bounded private set of recent live-scan opportunities against canonical intake and explain every miss;
- source coverage and source health are different metrics;
- do not certify CP2 broad discovery PASS until recall acceptance is satisfied.

The delegated task is the full authorized go-live scope, NOT the completion of one PR, one CI run, one deployment, one checkpoint, or one engineering time slice.

Default behavior is autonomous execution. Do not send routine status, progress, checkpoint-pass, PR-ready, merge-ready, deployment-ready, test, retry, or debugging messages. Persist evidence to GitHub/control plane and continue.

IMPORTANT MERGE/DEPLOY RULE:
- "production" is not by itself an approval boundary;
- routine reversible merges to main are autonomous when within authorized scope, required checks pass, no reserved boundary changes, and normal rollback exists;
- routine GitHub Pages deployments triggered from main are autonomous under the same conditions;
- additive/non-destructive schema migrations already required by the approved architecture are autonomous;
- if an open PR is stale or non-mergeable because main advanced, update/rebase it, resolve routine conflicts, rerun checks, merge when safe, verify deployment, and continue;
- do NOT ask the user to approve a squash merge or ordinary Pages deployment merely because it is production;
- PR ready, CI passed, merge ready, deployment ready, and deployment complete are internal checkpoints, not DONE.

Only destructive/materially irreversible production operations remain approval-gated, along with the other reserved boundaries below.

Return to the user only for exactly one of:
BLOCKED
APPROVAL REQUIRED
HUMAN ACTION REQUIRED
DONE

Reserved approval boundaries are exactly:
- new material paid service or commitment
- destructive or materially irreversible production operation
- security-boundary change
- outbound communication send
- final job-application submission

Never put private candidate data or secrets into the public repository.

Continue through the established go-live checkpoints and specifications until a real stop condition is reached. Do not voluntarily stop because an internal engineering unit completed. If the persistent execution environment remains active, decompose the next unmet acceptance criterion and keep working.
```

## Handoff acceptance test

The persistent runner is considered correctly initialized only after it has:

- read the normative files above;
- inspected current `main`, open/active PRs and workflow runs, Issue #1, Issue #3, and Issue #4;
- inspected current Supabase runtime state before making state-dependent claims;
- confirmed that implementation remains authorized;
- resumed from durable state without asking the user to restate prior decisions;
- treated `docs/DRILLDOWN_ACCEPTANCE.md` as P0 until verified;
- treated `docs/DISCOVERY_RECALL_ACCEPTANCE.md` as P0 until verified;
- recognized that working ATS adapters do not by themselves prove broad-market recall;
- treated routine reversible PR merge and GitHub Pages deployment as autonomous actions, not approval boundaries;
- recognized that PR/CI/deploy completion is not project completion;
- avoided a routine progress response.

## Truth constraint

No agent may claim that work will continue after a synchronous chat response unless a persistent execution runner is actually active.

A Work run may still be interrupted by a real product/tool limitation, sign-in requirement, unsupported action, or usage constraint. Such a limitation must be described truthfully as the actual blocker; it must never be relabeled as a user approval requirement simply to create a stopping point.
