# Potency-Preserving Iteration Contract

**Status:** NORMATIVE EXECUTION REQUIREMENT FOR PERSISTENT BUILD RUNS  
**Applies to:** ChatGPT Work and any durable implementation runner operating YourNextAdventure

## Purpose

YourNextAdventure must not become weaker as implementation progresses.

A common failure mode in long autonomous builds is local completion: the agent solves the immediate defect, optimizes for the current test or checklist, declares the nearby checkpoint complete, and stops challenging whether the product still fulfills its original purpose.

That behavior is prohibited here.

The system must iterate as a closed learning loop while preserving the potency of the original product objective:

> Continuously improve the probability that the candidate lands one of the highest-value mandates available, while minimizing unnecessary intervention, preserving truth and accumulated intelligence, and spending AI reasoning only where it materially improves decisions or outcomes.

## Core loop

After completing any material implementation slice, including a P0 fix, PR, merge, deployment, migration, checkpoint, or acceptance test, the persistent runner MUST execute this loop:

```text
RE-READ CURRENT AUTHORITY
-> INSPECT CURRENT MAIN + RUNTIME + DEPLOYED PRODUCT
-> RE-EVALUATE AGAINST PRODUCT PURPOSE, NOT JUST THE LAST TASK
-> RED-TEAM FOR MISSED SCOPE, FALSE PASS, AND LOCAL OPTIMIZATION
-> IDENTIFY THE HIGHEST-VALUE UNMET OR WEAK REQUIREMENT
-> IMPLEMENT THE NEXT END-TO-END SLICE
-> TEST
-> DEPLOY / APPLY WHEN SAFE
-> VERIFY WITH REAL DATA AND USER-VISIBLE BEHAVIOR
-> PERSIST EVIDENCE
-> REPEAT
```

The loop continues while the persistent execution surface remains active and no legitimate stop condition exists.

## Potency preservation rules

The runner MUST NOT make progress look better by weakening the product.

Specifically, it MUST NOT:

- narrow discovery simply because the currently implemented source list is easier to operate;
- substitute source health for market coverage;
- substitute unit tests for deployed behavior when the requirement is user-visible;
- mark a checkpoint PASS because code exists when real-data verification is missing;
- convert ambiguous high-value opportunities into rejects merely to improve precision metrics;
- expose a broad internet dump merely to improve recall;
- remove provenance, uncertainty, or material-unknown handling to simplify UI or data models;
- collapse the product into a resume tool, ATS matcher, PMO tracker, or generic job board;
- optimize for completion of a PR, issue, checklist, or engineering task at the expense of the product objective;
- silently reinterpret a difficult requirement into an easier proxy;
- lower acceptance thresholds because the current architecture makes the requirement inconvenient;
- treat a previously passed checkpoint as permanently true when new evidence disproves it.

## Reopening rule

All prior PASS decisions are falsifiable.

When owner review, runtime evidence, live-scan evidence, production behavior, or a regression reveals that a prior checkpoint was overstated, the runner MUST:

1. reopen the affected checkpoint or acceptance condition;
2. record the evidence that invalidated the prior PASS;
3. repair the underlying system rather than patch only the presentation;
4. add a regression/acceptance control where practical;
5. continue the iteration loop.

Reopening a checkpoint is evidence of a functioning learning system, not a failure to be hidden.

## Whole-system red-team questions

At the end of every material slice, answer internally from current durable evidence:

1. **Purpose:** Does the product now increase the probability of finding and converting the highest-value mandates, or did we merely complete engineering work?
2. **Recall:** What valuable opportunity could still be missed and why?
3. **Precision:** What irrelevant opportunity could still consume human attention and why?
4. **Trust:** Can every consequential conclusion be traced to evidence, source, confidence, policy/model/version, and changed/stale state?
5. **Actionability:** Can the user move from a surfaced item to the underlying role/source/decision without guessing where to click?
6. **Truth:** Did any implementation choice require unsupported candidate claims or erase an important unknown?
7. **Autonomy:** Is the user being asked to do something the system could reasonably do itself?
8. **Architecture:** Did the latest change preserve modularity, reversibility, provider independence, and the public-repo/private-runtime boundary?
9. **Economics:** Are expensive reasoning and external services used only where they improve expected outcome?
10. **Evidence of completion:** Would an independent reviewer looking only at the live product and durable state agree with the claimed PASS?

Any material negative answer becomes candidate work for the next iteration. Prioritize by expected impact on the core objective, not implementation convenience.

## Real-world verification requirement

For user-visible or market-facing capabilities, verification MUST include the live system and real runtime data whenever feasible.

Examples:

- drill-down is not complete until clickable paths work in the deployed cockpit;
- discovery recall is not complete until independently known relevant opportunities are reconciled and at least one non-static-list role enters canonical intake autonomously;
- provenance is not complete until the user can reach authoritative source evidence;
- a model capability is not complete merely because a mocked or synthetic test passes.

Synthetic tests remain necessary regression controls, but they are not substitutes for end-to-end proof.

## Iteration scope

The next iteration is selected from the **entire authorized product scope**, not merely from the files touched in the previous iteration.

The runner SHOULD favor the highest expected-value bottleneck using this order of concern:

1. defects that can cause high-value opportunities to be missed;
2. defects that surface materially wrong decisions;
3. dead ends that prevent the user from validating or acting on intelligence;
4. truth/provenance/security failures;
5. reliability/recovery/cost failures;
6. usability improvements that materially improve decision velocity;
7. cosmetic refinement.

## Completion condition

The persistent runner MUST NOT stop because the current defects are fixed.

It may return `DONE` only when:

- the active authorized scope's acceptance criteria are satisfied;
- all open P0 requirements are verified in production or the appropriate real environment;
- no known evidence contradicts a claimed checkpoint PASS;
- the latest whole-system red-team finds no unresolved issue that materially blocks the agreed go-live scope;
- durable evidence is persisted;
- no further authorized iteration is required by the current go-live control board.

Otherwise:

```text
TASK INCOMPLETE
AND no blocker
AND no approval boundary
AND no human-only action
=> REITERATE
```

`REITERATE` is an internal action, not a user-facing message. It means begin the next potency-preserving iteration immediately.
