# Architecture Reference

**Status:** Active architecture reference, non-normative  
**Canonical product contract:** [`../SPEC.md`](../SPEC.md)  
**Intent:** Capture the active architectural direction while implementation authority is governed by `SPEC_MANIFEST.json` and `AGENTS.md`.

## TL;DR

The design principle is **Lego architecture underneath, glass cockpit on top**.

The system should be modular enough that models, ATS providers, browser infrastructure, hosting, workflow engines, and external APIs can be replaced without changing the meaning of YourNextAdventure.

The recommended foundation is:

> **Modular monolith + typed capability contracts + PostgreSQL system of record + event-driven reconciliation + durable workflow orchestration + ports/adapters + provider-independent AI layer.**

## 1. Durable domain core

The domain core owns meaning. It should not know which external vendor implements a capability.

Core entities include:

- opportunity
- company
- role / latent mandate
- person / stakeholder
- relationship
- signal
- evidence
- hypothesis
- conclusion
- positioning
- artifact
- action
- outcome
- policy
- provenance
- confidence
- time

PostgreSQL should own canonical state, provenance, audit history, and relationships.

## 2. Capability blocks, not pipeline stages

Capabilities should be independent Lego blocks with typed inputs and outputs. Examples:

- opportunity discovery
- qualification
- native-candidate analysis
- role-readiness analysis
- company trajectory
- commercial pressure
- stakeholder mapping
- Two-Notch-Up / Aditya Lens
- Core of X
- positioning lock
- red team
- resume generation
- outreach generation
- contact verification
- cover letter generation
- optional thought-leadership asset
- official-career-site application execution

A capability contract should declare:

```yaml
capability:
  id: company_trajectory
  version: 1.0
  consumes: []
  produces: []
  triggers: []
  deterministic: false
  side_effects: false
  output_schema: schemas/company_trajectory.v1.json
  stale_when: []
  fail_behavior: BLOCK_ON_CONSEQUENTIAL_UNKNOWN
  eval_suite: evals/company_trajectory/
```

## 3. Separate three kinds of work

### Deterministic

Examples:

- ingestion
- polling
- deduplication
- canonical URL resolution
- search and facets
- field mapping
- known application answers
- mechanical validation
- file movement
- state transitions

Target: **zero AI tokens wherever practical**.

### High-value reasoning

Examples:

- native-candidate analysis
- company trajectory interpretation
- commercial pressure
- stakeholder hypotheses
- Two-Notch-Up
- Core of X
- positioning
- red-team work

Spend reasoning budget deliberately here.

### Controlled generation / execution

Examples:

- resume
- outreach
- cover letter
- optional thought-leadership asset
- novel application responses
- ATS/browser execution

Generation must consume locked facts and positioning, not invent them.

## 4. Shared-state, non-linear execution

The system must not rerun a linear pipeline when new evidence arrives.

Instead, new evidence marks only dependent conclusions as stale.

Example:

```text
new earnings evidence
      -> company trajectory STALE
      -> commercial pressure STALE
      -> Core of X potentially STALE
      -> positioning potentially STALE
      -> affected artifacts potentially STALE
```

A reconciler should determine what actually needs recomputation.

This is the mechanism that makes the architecture genuinely non-linear.

## 5. Modular monolith first

Do not start with microservices.

Use hard internal module boundaries inside one deployable backend. Extract a module later only when independent scaling, ownership, or reliability warrants it.

Suggested shape:

```text
src/
  domain/
  capabilities/
  ports/
  adapters/
  policies/
workflows/
contracts/
prompts/
evals/
fixtures/
templates/
migrations/
tests/
scripts/
infra/
```

Scripts may execute capabilities. Scripts must not become the architecture.

## 6. Ports and adapters

External systems should sit behind stable interfaces.

```text
JobSource       -> Workday / Greenhouse / Lever / others
ModelProvider   -> whichever model provider is best at the time
BrowserPort     -> Playwright or a future browser executor
EmailPort       -> Gmail or another provider
SearchPort      -> PostgreSQL first, specialized search later if needed
ObjectStore     -> S3-compatible storage
ProfileProvider -> private candidate data store
PolicyEngine    -> deterministic policy implementation
WorkflowEngine  -> lightweight runtime first, durable orchestrator later
```

**Depend on capabilities, not vendors.**

## 7. Data architecture

### PostgreSQL as durable center

Use PostgreSQL for:

- canonical entities
- relationships
- state
- JSONB source payloads
- full-text search initially
- provenance
- audit trail
- versioning metadata

Do not introduce a graph database merely because the conceptual model is graph-like. Relational edge tables are sufficient until graph traversal becomes a demonstrated bottleneck.

### Facts, hypotheses, and conclusions are different objects

Store the chain:

```text
SOURCE
  -> OBSERVATION / FACT
  -> EVIDENCE
  -> HYPOTHESIS
  -> CONCLUSION
  -> POSITIONING
  -> ARTIFACT
```

Material objects should retain source, time, confidence, derivation, and supersession links.

## 8. Durable execution

The architecture should support long-running, retryable, resumable work.

Preferred long-term pattern: a durable workflow engine such as Temporal behind a `WorkflowEngine` abstraction.

Business state remains in PostgreSQL. The workflow engine coordinates execution and recovery.

During early development, do not require a managed orchestration subscription. Use a lightweight/local implementation until unattended reliability makes a managed service worthwhile.

## 9. Events

Start with a transactional outbox in PostgreSQL and an `EventBus` interface.

Example events:

```text
opportunity.discovered.v1
job_description.changed.v1
company_evidence.added.v1
hiring_manager.changed.v1
core_x.locked.v1
resume.qa_passed.v1
application.submitted.v1
```

A dedicated event platform can be introduced later without changing domain semantics.

## 10. AI as a replaceable provider

AI must be an adapter, not the architecture.

Each AI-backed capability should have four versioned assets:

1. input schema
2. reasoning / prompt contract
3. output schema
4. evaluation suite

Changing a model should be a controlled substitution, not a product rewrite.

Do not make an agent framework the system of record.

## 11. Intake adapters

Define a `JobSource` capability and implement provider-specific adapters.

Preferred resolution order:

```text
official API / feed
  -> stable structured endpoint
  -> HTML extraction
  -> browser automation as last resort
```

Intake should be cheap, deterministic, and observable.

## 12. Application execution

Use ATS-specific adapters rather than one universal autonomous browser agent.

Examples:

- WorkdayApplicationAdapter
- GreenhouseApplicationAdapter
- LeverApplicationAdapter
- iCIMSApplicationAdapter
- SmartRecruitersApplicationAdapter
- OracleApplicationAdapter

Each adapter should own known form behavior, checkpoints, parser quirks, recovery, and confirmation detection.

Playwright is a strong initial browser implementation behind `BrowserPort`.

## 13. Search

Start with conventional PostgreSQL search and indexed facets.

Required UX is a normal text search box plus filters, not natural-language search.

Only add a specialized search engine after a demonstrated need.

## 14. Private data boundary

The public repository holds product logic, contracts, schemas, tests, and placeholder templates.

Private runtime stores hold:

- candidate identity
- resume truth
- verified evidence
- application answers
- private relationships
- generated private artifacts

Secrets remain separately managed.

See [`../PRIVATE_DATA_INJECTION.md`](../PRIVATE_DATA_INJECTION.md).

## 15. Policy must be executable

Consequential decisions must not live only inside prompts.

Examples:

- may this opportunity auto-apply?
- may this outreach be sent?
- can this field be inferred?
- is this source sufficiently trusted?
- is a numeric salary answer allowed?
- is human approval required?

Start with versioned deterministic rules behind a `PolicyEngine` interface.

## 16. Document engine

Resume and cover-letter generation should separate:

```text
content planning
  -> document composition
  -> rendering
  -> semantic + visual + ATS QA
```

Every artifact should retain content version, template version, renderer version, positioning version, and source evidence IDs.

## 17. Observability

Every meaningful capability invocation should be traceable through a correlation ID.

Capture:

- opportunity ID
- capability and version
- inputs and outputs
- duration
- model and token cost when AI is used
- external calls
- retries
- policy decisions
- failures

OpenTelemetry is the preferred vendor-neutral telemetry contract.

## 18. Regression system

Every important lesson should become a regression case, not merely remembered guidance.

Examples:

- executive overview became too thin
- native candidate was not confronted
- Two-Notch-Up became merely one level of abstraction
- locked outreach close drifted
- thought leadership was generated for an unqualified opportunity

Maintain fixtures, golden outputs, evals, and policy tests.

## 19. Technology direction today

| Layer | Initial direction | Durable abstraction |
|---|---|---|
| Backend | Python | domain modules |
| API | FastAPI | OpenAPI / HTTP |
| Schemas | Pydantic + JSON Schema | JSON Schema |
| Primary DB | PostgreSQL | repository interfaces |
| Managed DB | Supabase initially | PostgreSQL |
| Frontend | React + TypeScript / Next.js | HTTP API |
| Workflow | local/lightweight first; Temporal-class later | WorkflowEngine |
| Events | PostgreSQL outbox initially | EventBus |
| Search | PostgreSQL FTS + facets | SearchPort |
| Browser | Playwright | BrowserPort |
| AI | provider adapters | ModelProvider |
| Policy | deterministic typed rules | PolicyEngine |
| Observability | OpenTelemetry | OTel |
| Containers | Docker / OCI | OCI |
| CI/CD | GitHub Actions | scripts + containers |
| Documents | DOCX / OOXML + deterministic rendering | DocumentPort |

## 20. Explicit anti-patterns

Do not start with:

- agent swarms as architecture
- microservices
- Kafka
- Kubernetes
- graph database
- vector database for ordinary search
- RAG for structured facts already in tables
- universal AI browser automation where adapters are possible
- provider-specific model logic throughout the codebase
- security or approval policy buried in prompts
- private candidate data in Git
- business rules hidden in ad hoc scripts

## 21. Central architectural bet

The 10-year durability thesis is:

1. PostgreSQL owns canonical truth.
2. Domain contracts own meaning.
3. Workflow orchestration owns durable execution, not business state.
4. Adapters isolate external systems.
5. AI produces typed, evaluated judgments, never infrastructure truth.
6. Every important learning becomes a contract, policy, fixture, or regression test.

That allows the product to replace models, ATS providers, browser infrastructure, hosting, search, and workflow tooling without redefining what YourNextAdventure fundamentally is.
