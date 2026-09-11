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

## 2. Execution-surface truth

This contract governs agent behavior **while an execution surface is active**. It does not create persistence by itself.

A synchronous chat turn ends when the assistant sends a response. Repository instructions cannot override that lifecycle. Therefore ordinary chat MUST be treated as a **steering and exception surface**, not as the persistent executor for sustained autonomous work.

Any task expected to continue after an assistant response MUST run on a persistent execution surface, such as:

- ChatGPT Work;
- a repository-native coding/automation agent;
- another durable worker that can read this contract, persist state, and resume without a conversational turn.

Agents MUST NOT claim that GitHub, `AGENTS.md`, a control board, or a machine policy alone makes synchronous chat continue after a response. GitHub is the durable **control plane and system of record**; a persistent runner is the **execution plane**.

If sustained autonomous work is requested but the current surface is synchronous chat and no persistent runner is active, that is an execution-surface limitation. The agent may complete as much work as possible in the current turn, but MUST NOT imply that work will continue after the response. If continuation genuinely requires a persistent runner, request the minimum human action needed to enter or authorize that runner.

## 3. Default execution mode

Within an active execution surface, the default action is:

```text
TASK INCOMPLETE
AND no genuine blocker
AND no approval boundary
AND no human-only action
=> CONTINUE
```

Silence is the default during autonomous execution.

A successful intermediate step is not a reason to return control to the user.

## 4. Do not interrupt for routine execution

Agents MUST NOT return control merely to report:

- progress or percentages;
- a checkpoint passing;
- commits, merges, migrations, deployments, or tests succeeding;
- a pull request becoming review-ready or merge-ready;
- creating or updating a pull request, issue, issue comment, PR body, control-board entry, or other project-control evidence inside this repository;
- a routine merge to `main` or a routine deployment becoming ready to execute;
- routine implementation choices covered by existing architecture;
- recoverable errors or retries;
- debugging progress;
- source-sync status;
- model-run status;
- an intermediate recommendation that does not require a user decision;
- a request to "proceed", "continue", or reconfirm already-granted implementation authority.

Checkpoint evidence MUST be persisted to the project control plane and execution MUST continue automatically **when the active execution surface supports continuation**.

## 5. The only autonomous-build stop conditions

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
- a **destructive or materially irreversible** production operation;
- a security-boundary change;
- sending an outbound communication **to a person or external audience outside the project's own control plane**;
- final job-application submission.

#### Outbound communication boundary: exact meaning

`OUTBOUND_COMMUNICATION_SEND` means a human-facing communication sent outside the project's own GitHub/Supabase control plane, for example:

- email to a recruiter, hiring manager, employer, networking contact, or other external person;
- LinkedIn/Slack/WhatsApp/SMS/social message or post to an external audience;
- application free text or other candidate representation transmitted to an employer;
- any communication that presents the candidate to another person or organization.

It **does not** include routine project-control writes performed inside `iotchandra-afk/your-next-adventure`, including:

- creating, updating, or closing a pull request;
- writing or editing a PR title/body;
- creating, updating, commenting on, or closing a GitHub issue;
- persisting implementation evidence, checkpoint evidence, decision logs, or verification results;
- updating the go-live control board;
- creating commits, branches, tags, or other repository-native implementation metadata;
- writing runtime evidence to the project's authorized Supabase control/runtime state.

These are **internal control-plane mutations**, not outbound candidate communication. They are autonomous when within already-authorized scope, contain no prohibited private data/secrets, and do not independently cross another reserved approval boundary.

**Production is not synonymous with destructive.** A routine, reversible production change inside the already-authorized architecture is autonomous work, not an approval boundary.

The following MUST proceed without asking the user for approval when they are within already-authorized scope, required checks pass, no reserved boundary changes, and a normal rollback path exists:

- creating or updating implementation PRs and their titles/bodies;
- creating/updating GitHub issues, issue comments, and control-board evidence;
- updating/rebasing an implementation branch against `main`;
- resolving routine merge conflicts that do not change product intent or a reserved boundary;
- squash-merging or otherwise merging an implementation PR to `main`;
- deployment only through the explicitly authorized runtime surface defined by current project policy;
- verification of that authorized deployment;
- GitHub Pages, `chandrakanojia.com`, `iotchandra-afk.github.io`, and personal-site repositories/DNS are forbidden deployment surfaces for YourNextAdventure;
- additive/non-destructive schema migrations already required by the approved architecture.

If a PR becomes non-mergeable because `main` advanced, the agent MUST repair/update the branch, rerun the required checks, merge when safe, verify the deployment, and continue. It MUST NOT convert ordinary branch drift into a user approval request.

Approval is required only when the operation itself is materially destructive/irreversible or crosses another reserved boundary. Examples include dropping production data without a verified recovery path, an irreversible rewrite of canonical runtime state, weakening a security boundary, introducing a new material paid commitment, or sending candidate-facing communication to an external person or organization.

### HUMAN ACTION REQUIRED

A specific action can only be performed by the user and genuinely gates further progress, such as a required interactive sign-in, verification, or switching to a persistent execution surface that available tools cannot activate.

The request MUST be concrete, minimal, and deferred until the action is actually needed.

### DONE

The active task's agreed acceptance criteria are satisfied and verified with observable evidence.

"Code written", "PR opened", "PR ready", "CI passed", "deployment ready", "workflow started", "checkpoint reached", or "mostly complete" is not DONE when broader authorized scope remains.

A PR is an internal unit of work, not the project deliverable. After a safe merge/deployment, the agent MUST continue to the next unmet acceptance criterion without returning control.

## 6. User-requested questions are different

If the user explicitly asks for status, an explanation, a design decision, or another direct answer, answer the question. That is not an unsolicited execution interruption.

After answering, do not ask for permission to resume work that remains authorized. Also do not claim that a synchronous chat will keep executing after the answer. Resume automatically only if a persistent execution surface remains active.

## 7. Checkpoint behavior

Checkpoints are **durable evidence events**, not conversational events.

On checkpoint pass:

```text
verify gate
-> persist evidence in GitHub / database / CI / control board
-> perform the next safe authorized action, including control-plane writes, merge/deploy where applicable
-> continue automatically if the execution surface remains active
-> no user acknowledgement required
```

On checkpoint failure:

```text
diagnose
-> repair / retry / substitute
-> rerun verification
-> continue while the execution surface remains active
```

Only escalate if the failure becomes one of the stop conditions in Section 5.

## 8. Failure and uncertainty behavior

- Consequential unknowns fail closed.
- Recoverable failures are agent work, not user work.
- Prefer evidence over claims of completion.
- Bundle genuinely unresolved questions into one escalation rather than interrupting repeatedly.
- Never manufacture facts, access, completion, or background execution.
- Never describe a synchronous chat response as a mechanical continuation point. Sending the response ends that chat turn.
- Do not voluntarily terminate a persistent Work run merely because one engineering unit, PR, checkpoint, or deployment completed. Decompose the remaining authorized scope and continue within the active run.
- If an execution environment mechanically terminates a run or tool window, do not reinterpret that limitation as a user approval requirement. Persist state where possible and resume from durable state on the next execution opportunity.

## 9. Control plane vs execution plane

Execution state belongs in durable project artifacts, not conversational memory.

Use:

- `SPEC.md` for product intent and requirements;
- `AGENTS.md` for autonomous operating behavior;
- `SPEC_MANIFEST.json` for authority and document binding;
- `contracts/execution_policy.v1.json` for machine-readable communication policy;
- GitHub issues / PRs / control board for checkpoint and implementation evidence;
- CI and evals for proof;
- PostgreSQL/Supabase for runtime state, provenance, and traces;
- the cockpit for operational and decision visibility.

These form the **control plane**. Writing to them as part of authorized implementation is internal project execution, not external outbound communication. They do not themselves provide persistent agent execution.

Sustained autonomous implementation requires an **execution plane** capable of continuing without a chat response, for example ChatGPT Work or a durable repository-native worker.

## 10. Communication policy

During autonomous execution, unsolicited messages MUST begin with exactly one of:

```text
BLOCKED
APPROVAL REQUIRED
HUMAN ACTION REQUIRED
DONE
```

No routine `STATUS`, `PROGRESS`, `CHECKPOINT PASS`, `PR READY`, `DEPLOYMENT READY`, or `CONTINUING` messages are permitted.

## 11. Regression rule

A repeated behavioral failure MUST become a durable control, test, policy, or fixture rather than remain a conversational reminder.

The repository CI MUST validate that this execution contract and its machine-readable policy remain present and internally consistent, including the distinction between control-plane durability and execution-plane persistence, the rule that routine reversible merges/deployments are autonomous rather than approval-gated, and the rule that repository-native GitHub control-plane writes are not `OUTBOUND_COMMUNICATION_SEND`.
