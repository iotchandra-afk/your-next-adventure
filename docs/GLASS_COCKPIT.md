# Glass Cockpit Reference

**Status:** Planning reference, non-normative  
**Canonical product contract:** [`../SPEC.md`](../SPEC.md)

## Principle

The product should present **one coherent pane of glass** over a modular autonomous system.

The operating metaphor is:

> **Lego architecture underneath, glass cockpit on top.**

The user should not need to understand individual services, models, retries, queues, adapters, or logs to trust the system.

## 1. Why this matters

Autonomy creates an observability obligation.

The more the system acts without constant instruction, the more clearly it must answer:

- What exists?
- What matters?
- What is happening now?
- Why did the system do that?
- What changed?
- What failed?
- What needs human intervention?
- What already happened?

The product should never behave like an invisible autonomous black box.

## 2. Business-first navigation

Primary navigation should be oriented around the user's work, not infrastructure.

Likely primary areas:

```text
Home
Opportunities
Companies
People
Relationships
Insights
Applications
Outreach
Artifacts
```

Operational and administrative areas can sit beneath them:

```text
Activity
Automation
Connections
Observability
Settings
```

Infrastructure must be inspectable without dominating the product experience.

## 3. Persistent activity rail

A persistent activity stream should answer: **What is the system doing right now?**

Example:

```text
ACTIVITY

2m   Company research updated
     New earnings evidence changed trajectory

6m   Qualification completed
     Opportunity moved to deep-qualify

8m   Stakeholder discovery running
     7 candidate stakeholders being verified

14m  Role changed
     Job-description revision detected

21m  Application blocked
     Novel legal attestation requires review
```

Suggested activity filters:

- Discovery
- Research
- Reasoning
- Artifacts
- Outreach
- Applications
- System
- Failures

The activity rail should be useful to a non-technical operator. Deep logs belong elsewhere.

## 4. Progressive disclosure

The default view should show conclusions first, with provenance one click away.

Pattern:

```text
Opportunity card
  -> role workspace
  -> conclusion / status
  -> evidence and derivation
  -> raw source
```

Do not dump all evidence, traces, and system metadata onto the primary screen.

## 5. Opportunity workspace

A role workspace should make the complete pursuit understandable in one place.

Suggested sections:

- Role
- Qualification
- Company
- Native Candidate
- Commercial Pressure
- Stakeholders
- Two-Notch-Up
- Core of X
- Positioning
- Resume
- Outreach
- Cover Letter
- Thought Leadership
- Application
- Activity
- Evidence

The workspace is a projection of shared state, not a rigid sequential workflow.

## 6. Trust drill-down

Every consequential conclusion should support this inspection chain:

```text
Conclusion
  -> Why
  -> Evidence
  -> Source
  -> Confidence
  -> Capability + version
  -> What changed
  -> What became stale / invalidated
```

Example:

```text
Core of X v3 replaced v2

Reason:
Latest earnings evidence materially changed the margin-pressure thesis.

Affected:
- commercial pressure: recomputed
- positioning: stale
- outreach: stale
- resume: still valid
```

This should be understandable without opening engineering logs.

## 7. Human-readable state plus machine-level traceability

The UI should speak in business language:

> Native Candidate Analysis completed

Engineering metadata should still exist underneath:

```text
run_id
trace_id
capability_version
model_version
input_hash
policy_version
cost
duration
retry_count
```

Humans should not need UUIDs to use the system. Engineers and AI maintainers need them for reproducibility.

## 8. Connections as a first-class surface

Connections should not be buried as incidental settings.

The system should show whether the capabilities it depends on are available and healthy.

Example:

```text
CONNECTIONS

Job Sources
  Greenhouse       Healthy
  Lever            Healthy
  Workday          Degraded

Research
  Company IR       Healthy
  Public filings   Healthy

Private Data
  Candidate Vault  Healthy

Execution
  Browser          Healthy
  Email            Healthy

Models
  Reasoning         Healthy
  Fast model        Healthy
```

The orchestrator should depend on capabilities, not provider names.

## 9. Capability registry / resource discovery

The platform should be able to know what capabilities are currently available.

Conceptually:

```text
Job Sources
Research Providers
Browser Executors
Email / Calendar
Model Providers
Private Context
Artifact Engines
Observability Backends
```

This should enable provider replacement without rewriting business workflows.

## 10. Design-time vs run-time vs observe-time

Keep these concerns distinct.

### Configure / build

- sources
- rules
- qualification policies
- prompts
- capability versions
- ATS adapters
- templates
- models

### Run

- discover opportunities
- analyze
- research
- generate artifacts
- apply
- schedule / prepare outreach

### Observe

- activity
- traces
- failures
- cost
- stale state
- retries
- decisions
- policy blocks

Do not mix all three into one dashboard.

## 11. Model, capability, workflow, and agent are different concepts

The system should keep these separate:

```text
MODEL
reasoning engine

CAPABILITY
derive Core of X

WORKFLOW
respond to new opportunity or changed evidence

AGENT
persistent autonomous responsibility when truly needed
```

Avoid using the word "agent" for every AI-enabled feature.

## 12. Knowledge as a shared platform service

Knowledge should be governed centrally rather than hidden inside individual agents.

Useful knowledge domains include:

- candidate truth
- company intelligence
- role evidence
- market intelligence
- people intelligence
- relationship intelligence
- resume evidence
- past pursuits
- outcome learning
- thought leadership

Capabilities consume permitted slices of shared knowledge.

## 13. Product observability vs engineering observability

The glass cockpit should expose product-level observability:

- what ran
- why
- outcome
- evidence
- cost
- failure
- required intervention

Specialized infrastructure tools can provide deep technical diagnostics.

Do not recreate every specialist observability console inside the product.

## 14. Cost visibility

The cockpit should eventually surface operational economics.

Example:

```text
THIS MONTH

Infrastructure          $31.42
AI reasoning            $18.70
Research                 $7.20
Browser                  $2.16
Contact enrichment       $4.00
--------------------------------
Total                    $63.48

Cost / opportunity       $0.91
Cost / deep pursue       $4.88
```

The exact metrics may change, but cost drift should be visible.

## 15. Intervention design

A single clear surface should show what actually requires human attention.

Examples:

- consequential unknown
- ambiguous hiring-manager identity
- novel legal attestation
- numeric salary field without approved policy
- blocked ATS session
- conflicting candidate truth
- high-risk outbound communication

The system should not ask for intervention when a deterministic rule or trusted context can resolve the issue.

## 16. UX principles to preserve

1. **One system, not a collection of tools.**
2. **Business conclusion first, technical detail on demand.**
3. **Autonomous activity should always be visible.**
4. **Every consequential decision should be explainable.**
5. **Filters and search should handle operational density.**
6. **Health and blocked states should be obvious.**
7. **Connections and capabilities should be inspectable.**
8. **Progressive disclosure should prevent information overload.**
9. **The user should always know what needs attention next.**
10. **The cockpit should increase trust without requiring supervision of every step.**

## 17. North-star experience

The user should be able to open the product and answer, within seconds:

> What are my best opportunities, what changed since I last looked, what is the system doing about them, why does it believe what it believes, and where exactly do I need to intervene?

That is the purpose of the glass cockpit.
