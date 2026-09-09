# Cost Model Reference

**Status:** Planning reference, non-normative  
**Canonical product contract:** [`../SPEC.md`](../SPEC.md)  
**Pricing basis:** Planning assumptions as of 2026-09-09. Vendor prices will change and must be revalidated before purchase.

## Executive summary

The red-team conclusion is that the architecture can be serious and durable without carrying a large fixed monthly bill.

Current economic targets:

| Phase | Target incremental cash cost |
|---|---:|
| Build / development | **<$50/month** during normal build work |
| One-time development cash | **~$200-$1,500 total** expected range |
| Early live personal system | **~$40-$100/month** |
| Mature personal production | **~$50-$125/month** normal target |
| Reliability-heavy managed setup | **~$150-$300+ / month** only when justified |

The previous $250-$500/month baseline was too high for a single-user system because it assumed several managed services before they had earned their place.

## 1. One-time build economics

### Conventional engineering equivalent

A strong complete personal product would plausibly represent roughly:

**300-600 conventional engineering hours**, heavily dependent on the number and complexity of ATS adapters.

### AI-native build path

With strict contracts, mature open-source components, AI-assisted coding, and vertical-slice testing, a more useful planning range is:

**~120-250 hours of human-supervised work**.

This is not a commitment or a schedule. The largest uncertainty is the application-execution layer, especially external ATS reliability.

### Expected one-time incremental cash

Target:

**~$200-$1,500 total**

Likely uses:

- model/API testing
- temporary infrastructure
- browser automation experiments
- data/enrichment trials
- deployment experiments
- occasional paid development services

Do not pre-commit a large development budget without measured need.

## 2. Launch cost model

A disciplined initial production stack can remain small.

| Component | Launch assumption | Monthly planning range |
|---|---|---:|
| GitHub / CI | public repo, normal usage | $0 |
| PostgreSQL | managed production DB when needed | ~$25 |
| Frontend hosting | free tier initially | $0 |
| API / worker compute | small always-on or usage-based instance | ~$5-$20 |
| Workflow engine | local/lightweight or self-hosted initially | $0 incremental |
| Browser execution | Playwright on own worker initially | $0 incremental |
| AI reasoning | selective high-value use | ~$10-$50 |
| Observability | OpenTelemetry + free/basic tooling | $0 |
| Search | PostgreSQL full-text search / facets | $0 incremental |
| Object storage | low personal volume | ~$0-$5 |
| Job / research data | direct/free sources first | $0-$50 |
| Contact enrichment | only after opportunity qualification | usage-based / selective |

**Normal initial target: ~$50-$125/month.**

## 3. Paid services must earn their place

### Managed workflow orchestration

A managed durable workflow platform is architecturally attractive but not necessary at launch.

Use the abstraction from day one, but pay for managed orchestration only when unattended uptime, long-running recovery, or operational burden makes the fixed fee economically rational.

### Cloud browser infrastructure

A managed browser platform can improve reliability, remote sessions, proxies, or isolation. It is optional initially.

Default order:

```text
API / structured endpoint
  -> ATS-specific HTTP logic
  -> Playwright on own worker
  -> managed remote browser only when needed
```

### Paid observability

The glass cockpit requires strong product observability. That does not require an expensive observability subscription at launch.

Start with:

- product activity stream
- structured logs
- OpenTelemetry
- free/basic trace tooling

Upgrade only when retention, team use, or debugging volume requires it.

### Paid frontend hosting

A personal system does not need a premium frontend plan until operational or commercial requirements justify it.

## 4. AI cost model

AI should not dominate operating cost if the architecture is implemented correctly.

Spend AI primarily on:

- native-candidate analysis
- company trajectory interpretation
- commercial pressure
- stakeholder reasoning
- Two-Notch-Up
- Core of X
- positioning
- red-team work
- high-value writing
- genuinely novel application questions

Do not spend AI tokens primarily on:

- ingestion
- polling
- deduplication
- conventional search
- filters
- known form filling
- status transitions
- deterministic validation
- file movement

### Planning range

Normal personal-production target:

**~$10-$50/month initially**, with higher spend during unusually intensive pursuit periods.

### Cost-control mechanism

Reuse intelligence aggressively:

- company research should compound across roles
- candidate evidence should be structured once
- stable sources should be cached
- low-cost models should handle low-consequence reasoning
- highest-capability models should be reserved for consequential judgment

## 5. The real cost wildcards

### A. Job data

Commercial job feeds, historical hiring datasets, executive-movement data, or LinkedIn-scale discovery can become expensive.

Policy:

> Do not buy commercial job data until direct/free sources demonstrate a measurable recall gap that matters to outcomes.

### B. People and contact intelligence

Exact hiring-manager identity, org intelligence, email verification, and contact enrichment can cost more than hosting and AI combined.

Policy:

> Use paid people/contact enrichment only after an opportunity survives qualification.

### C. ATS maintenance

External forms and ATS behavior will change.

This is the largest likely maintenance burden.

Cost-control architecture:

- provider-specific adapters
- health checks
- replayable fixtures
- deterministic checkpoints
- failure telemetry
- regression suites
- AI-assisted remediation

A change to one ATS should not destabilize qualification, research, Core of X, resume generation, or the rest of the platform.

## 6. Maintenance economics

### Poor architecture

A brittle scraper/browser-agent system could consume **20-40+ human hours/month** in maintenance.

### Target architecture

With adapter isolation, fixtures, health checks, regression testing, and automated diagnostics, normal maintenance should aim toward:

**~2-8 engineering hours/month**, with occasional spikes when external providers make material changes.

This is an architectural target, not a guaranteed outcome.

## 7. Cost stages

### Stage 1: Build

```text
GitHub                 $0
Database free tier     $0
Frontend               $0
Playwright             $0
Workflow runtime       $0
Observability          $0
Search                 $0
AI                     usage only
```

Target: **<$50/month**.

### Stage 2: Live personal production

```text
Managed PostgreSQL     ~$25
Compute                ~$5-$20
AI                     ~$10-$50
Browser                $0-$20
Storage                ~$0-$5
Observability          $0
Search                 $0
Workflow platform      $0
Selective data         $0-$50
```

Target: **~$50-$125/month**.

### Stage 3: Reliability upgrades

Possible additions only when justified:

```text
Managed workflow       ~+$100 class fixed fee
Managed browser        ~+$20 class entry plan
Premium frontend       ~+$20 class plan
Paid observability     ~+$25-$30 class plan
Commercial data        variable
Contact enrichment     variable
```

Target: **~$150-$300+ only because specific bottlenecks justified the spend.**

## 8. Cost policy

Cost should be an explicit architectural constraint.

```yaml
cost_policy:
  development_monthly_target_usd: 50
  personal_production_target_usd: 100
  soft_alert_usd: 150
  architecture_review_required_above_usd: 250

  rules:
    - no_paid_service_without_measured_need
    - prefer_open_protocols
    - prefer_usage_based_over_fixed_fee
    - reuse_company_research
    - cache_stable_evidence
    - cheap_model_before_expensive_model
    - browser_only_when_HTTP_is_insufficient
    - enrichment_only_after_opportunity_qualification
    - managed_service_only_when_it_removes_a_measured_bottleneck
```

These are planning guardrails, not procurement authorization.

## 9. Glass-cockpit cost visibility

The product should eventually expose enough cost data to prevent silent drift.

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

Useful metrics may include:

- total monthly cost
- AI cost by capability
- cost per discovered opportunity
- cost per deep-qualified opportunity
- browser cost per application
- contact-enrichment cost per pursued opportunity
- failed-run cost
- cost saved through cached/reused intelligence

## 10. Economic design principle

> **Spend once to make the Lego bricks reliable. Keep the runtime boring and cheap.**

The system should not optimize for the smallest possible cloud bill at the expense of reliability, but recurring services should earn their place through measured value.

A healthy single-user target is approximately **$50-$125/month in normal personal production**, excluding exceptional commercial datasets or unusually heavy use.
