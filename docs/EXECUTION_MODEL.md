# Execution Model

**Status:** Architectural companion, non-normative explanation  
**Normative autonomous behavior:** [`../AGENTS.md`](../AGENTS.md)  
**Machine policy:** [`../contracts/execution_policy.v1.json`](../contracts/execution_policy.v1.json)  
**Product contract:** [`../SPEC.md`](../SPEC.md)

## Purpose

YourNextAdventure is designed for sustained AI-native execution with minimal human interruption.

The architectural goal is not merely automation. It is **exception-driven autonomy with durable observability**.

The critical distinction is:

```text
CONTROL PLANE
GitHub + spec + policy + database + CI
    stores truth, state, evidence, and authority

EXECUTION PLANE
persistent agent/worker
    performs work and can continue without a conversational turn
```

A durable control plane does not create a persistent execution plane.

## 1. Why ordinary chat is not the persistent executor

A synchronous assistant turn ends when the assistant sends a response. No repository instruction can alter that product lifecycle.

Therefore ordinary chat is used for:

- steering;
- exceptions;
- approvals;
- human-only actions;
- direct questions.

It must not be represented as a background worker that continues after a response.

For work that must continue after a response, use a persistent execution surface such as ChatGPT Work or a repository-native/durable agent runner.

## 2. Correct autonomous operating model

When a persistent execution surface is active:

```text
AI executes
  -> durable state changes
  -> tests / evals / traces
  -> checkpoint evidence persisted
  -> AI continues automatically

Human interaction occurs only when:
  BLOCKED
  APPROVAL REQUIRED
  HUMAN ACTION REQUIRED
  DONE
```

When only synchronous chat is active:

```text
AI executes as much as possible in the current turn
  -> persists state/evidence
  -> answers only when the user explicitly asks or a stop condition is reached
  -> does NOT claim execution will continue after that answer
```

## 3. Control plane vs conversation

Execution state must live outside chat.

```text
Product intent          -> SPEC.md
Agent operating policy  -> AGENTS.md
Machine policy          -> contracts/execution_policy.v1.json
Authority binding       -> SPEC_MANIFEST.json
Checkpoint evidence     -> GitHub control board / CI
Runtime state           -> PostgreSQL / Supabase
Operational visibility  -> cockpit
Conversation            -> steering + exceptions
```

This prevents conversational turns from becoming the system of record, but it does not make chat persistent.

## 4. Pull-based visibility

The user should be able to inspect progress whenever desired without requiring the agent to push routine updates.

Checkpoint passes, deployments, source health, model traces, retries, and test evidence belong in durable system surfaces.

The product should behave more like a well-instrumented service than a chatty project manager.

## 5. Exception-driven communication

Routine success does not require human attention.

The communication layer therefore behaves like alerting infrastructure:

- informational events are persisted;
- attention events are surfaced in the cockpit;
- action-required events may interrupt when they genuinely block progress;
- approval-gated actions remain human controlled.

## 6. Deterministic stop policy

Whether to interrupt the user should not be left to open-ended model judgment.

The machine-readable policy defines:

```text
if task_incomplete
and no_blocker
and no_approval_boundary
and no_human_action
and execution_surface_active
then CONTINUE
```

The model may reason about whether evidence constitutes a blocker, but the allowed response classes are constrained.

## 7. Checkpoints are evidence events

A checkpoint does not require user acknowledgement.

```text
checkpoint passes
  -> write evidence
  -> advance state
  -> continue if the execution surface remains active
```

Human acknowledgement is not part of the state transition unless the checkpoint itself contains a reserved approval boundary.

## 8. Failure behavior

Recoverable failures remain inside the autonomous execution envelope.

The system should:

1. diagnose;
2. retry when safe;
3. use an alternate provider/adapter/strategy when supported;
4. preserve evidence and state;
5. escalate only if autonomous remediation is exhausted and the failure now matches a stop condition.

Consequential uncertainty fails closed rather than inventing facts or authority.

## 9. Human authority boundaries

The user retains control over consequential side effects:

- material new paid commitments;
- destructive production actions;
- security-boundary changes;
- outbound communications;
- final job-application submission.

A human-only authentication, verification, or execution-surface switch may also be requested when no available tool can perform it and it blocks further autonomous work.

## 10. Regression philosophy

Behavioral failures are engineering failures when they recur.

A repeated unwanted interruption should therefore result in one or more of:

- a normative agent rule;
- a machine-readable policy condition;
- a regression test;
- a control-plane change;
- an eval.

The goal is to make learned operating behavior durable while never confusing durable state with durable execution.
