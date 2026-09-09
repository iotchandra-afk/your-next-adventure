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
6. GitHub Issue #1 go-live control board

Treat GitHub as the canonical control plane and Supabase as canonical runtime state. Resume from current repository/runtime state; do not reconstruct work from conversational summaries when durable evidence is available.

Default behavior is autonomous execution. Do not send routine status, progress, checkpoint-pass, deployment, test, retry, or debugging messages. Persist evidence to GitHub/control plane and continue.

Return to the user only for exactly one of:
BLOCKED
APPROVAL REQUIRED
HUMAN ACTION REQUIRED
DONE

Reserved approval boundaries remain:
- new material paid service or commitment
- destructive production operation
- security-boundary change
- outbound communication send
- final job-application submission

Never put private candidate data or secrets into the public repository.

Continue through the established go-live checkpoints and specifications until a real stop condition is reached.
```

## Handoff acceptance test

The persistent runner is considered correctly initialized only after it has:

- read the normative files above;
- inspected current `main`, open/active workflow runs, and Issue #1;
- inspected current Supabase runtime state before making state-dependent claims;
- confirmed that implementation remains authorized;
- resumed from durable state without asking the user to restate prior decisions;
- avoided a routine progress response.

## Truth constraint

No agent may claim that work will continue after a synchronous chat response unless a persistent execution runner is actually active.
