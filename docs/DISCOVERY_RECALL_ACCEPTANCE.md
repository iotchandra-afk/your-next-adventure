# Broad Discovery Recall Acceptance

**Status:** P0 product requirement
**Applies to:** Intake discovery, source coverage, external-signal reconciliation, and recall verification

## Problem

The current intake implementation proves that several ATS adapters work, but adapter-family health is not the same thing as broad market discovery.

A system that polls only a small static set of employer endpoints can be technically healthy while still missing highly relevant executive opportunities that are discoverable through web search, recruiter posts, job boards, LinkedIn, or other company career sites.

That violates the locked principle:

> **Discover broadly. Screen generously. Qualify demanding. Present narrowly.**

## Required architecture

Discovery MUST distinguish two independent layers:

1. **Direct-source polling**
   - official company career sites
   - Workday / Greenhouse / Lever / iCIMS / SmartRecruiters / Oracle / Taleo / other ATS feeds
   - high-quality structured endpoints

2. **Market discovery / signal capture**
   - web search
   - recruiter posts
   - job boards / aggregators
   - LinkedIn discovery where permitted
   - external signals produced by an authorized AI/live-scan workflow

Market discovery is allowed to be noisy because it is not the user-facing opportunity list. All signals still flow through normalization, canonicalization, deduplication, deterministic exclusions, mandate-aware triage, and deep qualification before surfacing.

## External signal ingestion

The system MUST provide a durable `DISCOVERY_SIGNAL` ingestion path so a role found outside a configured ATS poller can enter the same canonical opportunity universe.

At minimum the signal contract must support:

- company
- title
- location when known
- discovery URL
- official/company posting URL when known
- requisition ID when known
- posted/found timestamp
- source family
- source name
- raw snippet or structured metadata sufficient for later resolution
- provenance and confidence

A discovery signal MUST NOT bypass screening or create a duplicate canonical opportunity.

If an official company career posting can be resolved, the official URL becomes primary while the discovery URL remains provenance.

## Coverage requirement

`Broad intake works` MUST NOT be certified solely because N ATS/source families are operational.

Certification requires evidence that:

- the system discovers outside a small static employer list;
- at least one market-discovery channel is active and feeding canonical intake;
- externally discovered signals reconcile into canonical opportunities;
- direct ATS polling and market discovery deduplicate correctly;
- source links survive canonicalization;
- missing-source and stale-source conditions are observable;
- source coverage is measured separately from source health.

## Recall probes

Maintain a private runtime set of recently known relevant opportunities discovered independently of the intake engine. The set is a recall probe, not a permanent allow-list.

For each probe, the system must classify the miss as one of:

- `DISCOVERED_AND_SURFACED`
- `DISCOVERED_NOT_SURFACED` with screening/qualification reason
- `DISCOVERED_STALE_OR_CLOSED`
- `MISSED_SOURCE_COVERAGE`
- `MISSED_QUERY_COVERAGE`
- `CANONICALIZATION_FAILURE`
- `DEDUPLICATION_FAILURE`
- `INGESTION_FAILURE`
- `UNKNOWN_REQUIRES_INVESTIGATION`

A role known from an independent live scan that is absent from the canonical universe is a **recall defect**, not evidence that the role is irrelevant.

## Current defect exposed by review

The live runtime currently has a limited static source registry. Independent role scans have surfaced relevant executive opportunities at companies not represented by that registry. Therefore broad-market recall is not yet certified even though the configured ATS adapters are functioning.

## Acceptance tests

1. **Known-signal parity:** a bounded private sample of independently discovered relevant roles is reconciled against the canonical universe. All misses are explained and remediated where appropriate.
2. **External-signal path:** a discovery-only signal can be ingested, deduped, resolved to an official source when available, screened, and surfaced/held/rejected through the normal funnel.
3. **Static-list escape:** at least one qualifying role from a company not present in the original static source list is discovered autonomously and reaches canonical intake.
4. **Source provenance:** every canonical opportunity retains every meaningful discovery/source URL and identifies the primary official posting when resolved.
5. **No internet dump:** enabling broad discovery does not change the default cockpit rule. Only qualified/surfaced roles reach the primary human view; raw discovery remains below the glass.

## Go-live implication

CP2 cannot be considered fully PASS until this contract is satisfied. Adapter functionality may remain recorded as verified, but broad discovery recall is an open P0 gate.
