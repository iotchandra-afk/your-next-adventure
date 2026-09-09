# YourNextAdventure Agent Execution Contract

**Status:** NORMATIVE  
**Applies to:** AI agents, coding agents, reasoning agents, automation workers, and any human supervising autonomous implementation  
**Product requirements:** [`SPEC.md`](./SPEC.md)  
**Machine policy:** [`contracts/execution_policy.v1.json`](./contracts/execution_policy.v1.json)

## 1. Authority split

`SPEC.md` defines **what YourNextAdventure must do**.

`AGENTS.md` defines **how autonomous implementation and operation must behave while doing it**.

`SPEC_MANIFEST.json` binds both documents into the project control plane.

If implementation is authorized in `SPEC_MANIFEST.json`, agents MUST NOT ask the user to reconfirm ordinary implementation choices already covered by the specification, architecture, prior decisions, or this contract.

## 2. Default execution mode

The default action is:

```text
TASK INCOMPLETE
AND no genuine blocker
AND no approval boundary
AND no human-only action
=> CONTINUE
```

Silence is the default during autonomous execution.

A successful intermediate step is not a reason to return control to the user.

## 3. Do not interrupt for routine execution

Agents MUST NOT return control merely to report:

- progress or percentages;
- a checkpoint passing;
- commits, merges, migrations, deployments, or tests succeeding;
- routine implementation choices covered by existing architecture;
- recoverable errors or retries;
- debugging progress;
- source-sync status;
- model-run status;
- an intermediate recommendation that does not require a user decision;
- a request to "proceed", "continue", or reconfirm already-granted implementation authority.

Checkpoint evidence MUST be persisted to the project control plane and execution MUST continue automatically.

## 4. The only autonomous-build stop conditions

During an active autonomous build or execution task, an unsolicited agent response is permitted only for one of these four conditions.

### BLOCKED

A required fact, permission, dependency, or capability is unavailable and cannot reasonably be derived, repaired, substituted, or worked around autonomously.

Before escalating, the agent MUST attempt reasonable remediation and alternatives. The escalation MUST contain only:

- the blocker;
- evidence that it is real;
- remediation already attempted;
- the minimum action or information required from the user.

### APPROVAL REQUIRED

The next action crosses an explicitly reserved approval boundary:

- a new material paid service or commitment;
- a destructive production operation;
- a security-boundary change;
- sending an outbound communication;
- final job-application submission.

Routine reversible implementation does not require approval.

### HUMAN ACTION REQUIRED

A specific action can only be performed by the user and genuinely gates further progress, such as a required interactive sign-in or verification that available tools cannot perform.

The request MUST be concrete, minimal, and deferred until the action is actually needed.

### DONE

The active task's agreed acceptance criteria are satisfied and verified with observable evidence.

"Code written", "workflow started", "checkpoint reached", or "mostly complete" is not DONE.

## 5. User-requested questions are different

If the user explicitly asks for status, an explanation, a design decision, or another direct answer, answer the question. That is not an unsolicited execution interruption.

After answering, do not ask for permission to resume work that remains authorized.

## 6. Checkpoint behavior

Checkpoints are **durable evidence events**, not conversational events.

On checkpoint pass:

```text
verify gate
-> persist evidence in GitHub / database / CI / control board
-> continue automatically
-> no user acknowledgement required
```

On checkpoint failure:

```text
diagnose
-> repair / retry / substitute
-> rerun verification
-> continue
```

Only escalate if the failure becomes one of the stop conditions in Section 4.

## 7. Failure and uncertainty behavior

- Consequential unknowns fail closed.
- Recoverable failures are agent work, not user work.
- Prefer evidence over claims of completion.
- Bundle genuinely unresolved questions into one escalation rather than interrupting repeatedly.
- Never manufacture facts, access, completion, or background execution.
- If an execution environment mechanically terminates a run or tool window, do not reinterpret that limitation as a user approval requirement. Persist state where possible and resume from durable state on the next execution opportunity.

## 8. Control plane

Execution state belongs in durable project artifacts, not conversational memory.

Use:

- `SPEC.md` for product intent and requirements;
- `AGENTS.md` for autonomous operating behavior;
- `SPEC_MANIFEST.json` for authority and document binding;
- `contracts/execution_policy.v1.json` for machine-readable communication policy;
- GitHub issues / control board for checkpoint evidence;
- CI and evals for proof;
- PostgreSQL/Supabase for runtime state, provenance, and traces;
- the cockpit for operational and decision visibility.

The chat is a steering and exception channel, not the system of record.

## 9. Communication policy

During autonomous execution, unsolicited messages MUST begin with exactly one of:

```text
BLOCKED
APPROVAL REQUIRED
HUMAN ACTION REQUIRED
DONE
```

No routine `STATUS`, `PROGRESS`, `CHECKPOINT PASS`, or `CONTINUING` messages are permitted.

## 10. Regression rule

A repeated behavioral failure MUST become a durable control, test, policy, or fixture rather than remain a conversational reminder.

The repository CI MUST validate that this execution contract and its machine-readable policy remain present and internally consistent.
