# YourNextAdventure repository instructions

Before making changes, read and follow:

1. [`../AGENTS.md`](../AGENTS.md) for autonomous execution behavior and stop conditions.
2. [`../SPEC.md`](../SPEC.md) for product requirements.
3. [`../SPEC_MANIFEST.json`](../SPEC_MANIFEST.json) for authority and implementation status.
4. [`../contracts/execution_policy.v1.json`](../contracts/execution_policy.v1.json) for the machine-readable communication policy.

Implementation is authorized when `SPEC_MANIFEST.json` says so. Do not ask the user to reconfirm ordinary implementation work already covered by the specification.

During autonomous execution, persist checkpoint evidence and continue automatically. Do not emit routine progress or checkpoint messages. Unsolicited interruption is reserved for `BLOCKED`, `APPROVAL REQUIRED`, `HUMAN ACTION REQUIRED`, or `DONE` as defined in `AGENTS.md`.
