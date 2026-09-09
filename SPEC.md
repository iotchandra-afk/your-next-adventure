# YourNextAdventure: Canonical Product and Operating Specification

**Version:** 0.1-reset  
**Status:** PLANNING ONLY  
**Implementation authorization:** NOT GRANTED  
**Audience:** Human product owner, AI coding/reasoning agents, engineers, reviewers  
**Normative source:** This document

---

## 0. How to read this specification

This document is deliberately written for both humans and AI systems.

### Normative language

- **MUST** = mandatory.
- **MUST NOT** = prohibited.
- **SHOULD** = expected unless there is a documented reason not to.
- **SHOULD NOT** = generally prohibited unless there is a documented reason.
- **MAY** = optional.
- **UNKNOWN** = not established. Do not silently convert UNKNOWN into an inferred fact.
- **VERIFIED** = supported by authoritative or sufficiently reliable evidence.
- **INFERRED** = reasoned conclusion supported by evidence but not directly verified.

### System principle

YourNextAdventure is **not a linear pipeline**.

The system contains components that work from a shared, versioned opportunity record. Components can operate concurrently when their dependencies are satisfied. New evidence can invalidate or update prior conclusions and propagate sideways or backward.

A user interface may show a backlog, cards, or lifecycle states for usability. Those are views over the system, not the architecture itself.

---


# 0A. Public repository / private runtime boundary

The public repository MUST NOT contain personal candidate data, credentials, secrets, private relationship intelligence, or private application answers.

The public repository MAY contain:
- schemas;
- placeholder templates;
- validation logic;
- decision rules;
- public examples;
- test fixtures using synthetic identities.

Private candidate context MUST be supplied at runtime through a private data provider.

## Runtime data contract

Public components SHOULD refer to candidate-specific data using stable logical paths:

```yaml
candidate:
  identity:
    first_name: "${CANDIDATE_FIRST_NAME}"
    full_name: "${CANDIDATE_FULL_NAME}"
    phone: "${CANDIDATE_PHONE}"
    email: "${CANDIDATE_EMAIL}"

  profile:
    source: "private_runtime_provider"

  resume:
    source: "private_runtime_provider"

  application_answers:
    source: "private_runtime_provider"

  relationships:
    source: "private_runtime_provider"
```

No component may require personal values to be hard-coded into the repository.

## Secret classes

```yaml
data_classes:
  public:
    examples:
      - product_rules
      - schemas
      - prompt_templates
      - public_company_research

  private_profile:
    examples:
      - identity
      - phone
      - email
      - address
      - resume_history
      - verified_metrics
      - work_authorization
      - compensation_policy
      - application_answers
      - relationship_notes

  secret:
    examples:
      - API_keys
      - OAuth_tokens
      - ATS_session_credentials
      - browser_session_secrets
      - encryption_keys
```

`private_profile` and `secret` values MUST NOT be committed to Git.


# 1. Product purpose

## 1.1 Objective

YourNextAdventure MUST optimize for the quality and convertibility of executive opportunities, not for application volume.

The system should help the candidate identify and pursue opportunities where:

1. the mandate is economically or strategically consequential;
2. the candidate has a credible path to win;
3. the role has sufficient authority, scope, access, and upside;
4. the company and hiring context are worth pursuing;
5. the candidate can be positioned as native, native-adjacent, outcomes-native, or clearly differentiated enough to beat a native candidate;
6. the pursuit can be grounded in verified evidence rather than manufactured fit.

## 1.2 Core objective statement

> Continuously improve the probability that the candidate lands one of the highest-value mandates available to him, while minimizing unnecessary intervention, preserving truth and accumulated intelligence, and spending AI reasoning only where it materially improves decisions or outcomes.

## 1.3 What the system is not

The system MUST NOT reduce itself to:

- a job tracker;
- an ATS keyword matcher;
- a resume tailoring engine;
- an application-volume bot;
- a rigid stage-by-stage agent pipeline;
- a generic "AI career assistant";
- a system that manufactures fit by rewriting the candidate's identity;
- a system that spends LLM tokens on deterministic ingestion, deduplication, form filling, or state changes.

---

# 2. Architectural model

## 2.1 Shared-state, event-driven architecture

The core primitive is:

```yaml
primitive:
  - entity
  - signal
  - state
  - relationship
  - hypothesis
  - evidence
  - action
  - outcome
  - time
  - confidence
```

Core entities include:

```yaml
entities:
  - candidate
  - company
  - role
  - latent_mandate
  - job_posting
  - hiring_manager
  - recruiter
  - stakeholder
  - relationship
  - business_problem
  - commercial_pressure
  - evidence
  - hypothesis
  - positioning
  - resume
  - cover_letter
  - outreach
  - thought_leadership_asset
  - application
  - interaction
  - outcome
```

## 2.2 Three classes of work

```yaml
work_classes:
  deterministic:
    examples:
      - source polling
      - ingestion
      - normalization
      - deduplication
      - canonical URL resolution
      - exact filtering
      - search indexing
      - form field mapping
      - status changes
      - file movement
      - known application answers
      - mechanical QA
    token_policy: "zero AI tokens wherever practical"

  high_value_reasoning:
    examples:
      - native_candidate_analysis
      - role_readiness
      - company_trajectory_interpretation
      - commercial_pressure
      - stakeholder_hypotheses
      - two_notch_up_lens
      - core_of_x
      - positioning
      - red_team
      - novel_application_question_reasoning
    token_policy: "spend deliberately"

  controlled_generation:
    examples:
      - resume
      - hiring_manager_outreach
      - cover_letter
      - optional_thought_leadership_asset
      - novel_free_text_application_answers
    token_policy: "generate only from locked evidence and positioning"
```

---

# 3. Canonical opportunity and candidate truth model

## 3.1 Opportunity Intelligence Record

Every opportunity MUST have one canonical, versioned record.

```yaml
opportunity:
  identity:
    opportunity_id: required
    company_id: required
    role_id: required
    requisition_id: nullable
    canonical_company_career_url: required_before_application
    external_discovery_urls: []
    ATS: nullable
    role_title: required
    location: nullable
    compensation: nullable
    posted_date: nullable
    first_seen: required
    last_verified: required
    role_status: required

  job_description:
    raw: required
    hash: required
    version: required
    captured_at: required

  intelligence:
    qualification: nullable
    native_candidate_analysis: nullable
    role_readiness: nullable
    company_trajectory: nullable
    commercial_pressure: nullable
    stakeholder_map: nullable
    two_notch_up: nullable
    core_of_x: nullable
    positioning_lock: nullable
    evidence_map: nullable

  artifacts:
    resume: nullable
    cover_letter: nullable
    outreach_variants: []
    chosen_outreach: nullable
    thought_leadership_asset: nullable
    application_payload: nullable

  activity:
    events: []
    interactions: []
    outcomes: []
```

## 3.2 Candidate Truth Graph

Candidate truth MUST be separate from role-specific narrative.

```yaml
candidate_truth:
  immutable_or_verified:
    - legal_identity
    - employers
    - titles
    - employment_dates
    - education
    - credentials
    - verified_metrics
    - verified_scope
    - verified_team_scale
    - verified_budget_or_portfolio_scale
    - verified_AI_experience
    - verified_industry_experience
    - work_authorization
    - geography
    - canonical_application_answers

  versioned_narrative:
    - executive_overview
    - evidence_order
    - emphasis
    - terminology
    - role_specific_positioning
    - proof_selection

  prohibited_behavior:
    - inventing_scope
    - inventing_P_and_L
    - inventing_quota
    - inventing_product_ownership
    - inventing_engineering_depth
    - inventing_AI_production_claims
    - changing_dates_to_fit
    - changing_titles_to_fit
    - rewriting_identity_from_JD_keywords
```

### Tailoring rule

> Tailor by **employer problem -> verified evidence**, never by **keywords -> rewritten identity**.

---

# 4. Intake engine

## 4.1 Purpose

Discover potentially relevant opportunities broadly and continuously without spending AI tokens.

## 4.2 Sources

```yaml
intake_sources:
  preferred_direct:
    - company_career_sites
    - structured_company_job_feeds
    - Workday
    - Greenhouse
    - Lever
    - iCIMS
    - SmartRecruiters
    - Oracle
    - Taleo
    - other_company_ATS_sources

  discovery_only:
    - LinkedIn
    - job_boards
    - aggregators
    - recruiter_posts
    - web_search_results
```

A third-party source MAY create an opportunity signal.

A third-party source MUST NOT become the final application destination.

Every pursued opportunity MUST resolve to the company's official career site before application.

## 4.3 Zero-token operations

```yaml
zero_token_intake:
  - polling
  - ingestion
  - normalization
  - exact_title_rules
  - obvious_exclusion_rules
  - location_rules
  - structured_compensation_extraction
  - requisition_id_extraction
  - duplicate_detection
  - source_canonicalization
  - freshness_checks
  - company_allow_lists
  - company_block_lists
```

## 4.4 Deduplication

Preferred key:

```yaml
dedupe:
  preferred:
    - company
    - requisition_id
  fallback:
    - company
    - normalized_title
    - location
    - JD_hash
```

## 4.5 Intake state

Successful intake lands in:

```yaml
status: INTAKE_BACKLOG
```

---

# 5. Qualification engine and backlog filters

## 5.1 Purpose

Decide which opportunities deserve expensive analysis and the candidate attention.

Keyword similarity MUST NOT be the primary qualification mechanism.

## 5.2 Filterable criteria

Every field below SHOULD be available as a backlog filter when data exists.

```yaml
filters:

  identity:
    - company
    - company_type
    - industry
    - sub_industry
    - business_model
    - public_private_PE_backed
    - company_scale
    - location
    - remote_hybrid_onsite
    - ATS
    - posting_age
    - source
    - requisition_status

  role:
    - advertised_level
    - likely_real_level
    - mandate_altitude
    - scope_altitude
    - reporting_altitude
    - compensation_altitude
    - the candidate_relative_level
    - normalized_role_family
    - target_lane
    - mandate_archetype
    - enterprise_vs_function_scope
    - transformation_scope
    - AI_centrality
    - platform_centrality
    - operating_model_scope
    - customer_service_scope
    - product_scope
    - engineering_scope
    - sales_quota_requirement

  authority:
    - executive_sponsor_strength
    - direct_BU_or_C_suite_access
    - team_scope
    - matrix_scope
    - hiring_authority
    - budget_authority
    - P_and_L_exposure
    - business_outcome_ownership
    - decision_rights_strength

  economics:
    - compensation_plausibility
    - equity_upside
    - scope_to_compensation_fit
    - enterprise_value_creation_potential
    - career_optionality
    - two_year_trajectory
    - four_year_trajectory

  candidate_fit:
    - functional_fit
    - industry_fit
    - environment_fit
    - scale_fit
    - regulatory_fit
    - executive_altitude_fit
    - evidence_coverage
    - direct_experience_ratio
    - adjacent_experience_ratio
    - unsupported_requirements
    - claim_risk

  competitive:
    - native_candidate_class
    - native_candidate_risk
    - the candidate_differentiation
    - likely_competitor_profile
    - winability
    - conversation_credibility

  strategic:
    - commercial_pressure_strength
    - core_of_x_strength
    - two_notch_up_potential
    - mandate_expansion_potential
    - stakeholder_access_potential
    - warm_path_strength
    - company_trajectory

  execution:
    - overall_priority
    - pursue_status
    - next_best_action
    - application_status
    - outreach_status
    - resume_status
    - thought_leadership_status
    - confidence
```

## 5.3 Hard-reject or no-go patterns

```yaml
reject_patterns:
  - stale_or_closed
  - generic_PMO_without_operating_authority
  - transformation_without_authority
  - innovation_theater
  - pure_hunter_sales
  - pure_engineering_where_deep_production_engineering_is_mandatory_and_unsupported
  - specialist_domain_depth_that_cannot_be_truthfully_supported
  - materially_low_scope_relative_to_candidate
  - materially_inadequate_compensation_without_exception_logic
  - advisory_only_without_operating_authority
  - small_company_without_authority_sponsor_or_equity_logic
  - role_requires_factual_exaggeration_to_compete
```

## 5.4 Qualification outputs

```yaml
qualification_class:
  - TIER_1_DEEP_QUALIFY
  - TIER_2_WORTH_EXPLORING
  - TIER_3_MONITOR
  - REJECT
  - NEEDS_DATA
```

---

# 6. Native-candidate and winability analysis

## 6.1 Core question

> If the hiring manager could choose the obvious native candidate, who would that person be? How far is the candidate from that profile? Does the candidate have a credible reason to beat that person?

## 6.2 Dimensions

```yaml
native_candidate_dimensions:
  - problem_similarity
  - function_similarity
  - industry_similarity
  - business_model_similarity
  - company_scale_similarity
  - operating_environment_similarity
  - regulatory_similarity
  - role_altitude_similarity
  - team_scope_similarity
  - budget_scope_similarity
  - transformation_ownership_similarity
  - technology_context_similarity
  - executive_stakeholder_similarity
  - measurable_outcome_similarity
```

## 6.3 Classification

```yaml
native_candidate_class:
  NATIVE:
    definition: "the candidate already looks like an obvious candidate from the role's world."

  NATIVE_ADJACENT:
    definition: "Different title or domain, but substantially the same mandate and environment."

  OUTCOMES_NATIVE:
    definition: "Less literal pedigree, but unusually direct evidence of solving the underlying business problem."

  COMPETING_AGAINST_NATIVE:
    definition: "The hiring manager can readily find candidates with more literal experience."

  NON_NATIVE_STRETCH:
    definition: "Too many simultaneous translations are required."
```

## 6.4 Required outputs

```yaml
native_candidate_output:
  native_candidate_archetype: required
  the candidate_advantages: []
  native_candidate_advantages: []
  fatal_gap: boolean
  win_thesis: required
  skepticism_to_overcome: []
  evidence_answering_skepticism: []
  confidence: required
  commentary: required
```

The system MUST NOT manufacture a pseudo-precise fit percentage when the evidence does not justify it.

The commentary MUST answer:

- Why can the candidate win?
- What must the hiring manager believe for him to win?
- What would a skeptical native-domain hiring manager question?
- What verified evidence answers that objection?
- Are we discovering a real fit or manufacturing one?

---

# 7. Role readiness and weighted mandate analysis

## 7.1 Purpose

Translate the job description into the actual likely hiring decision.

## 7.2 Output

Generate approximately 7 to 10 weighted decision criteria.

```yaml
criterion:
  name: required
  estimated_weight: required
  why_it_matters: required
  evidence_class:
    - DIRECT
    - ADJACENT
    - WEAK
    - UNSUPPORTED
  best_verified_evidence: required_or_unknown
  likely_objection: required
  claim_to_avoid: nullable
```

Special dimensions MUST include, when relevant:

- authority;
- economics;
- mandate ownership;
- scale;
- executive altitude;
- operating environment;
- domain depth;
- technical depth;
- people scope;
- business outcomes.

## 7.3 Readiness output

```yaml
readiness:
  - STRONG
  - COMPETITIVE_WITH_POSITIONING
  - HIGH_RISK
  - NO_GO
```

Also produce:

- biggest reasons to hire;
- biggest reasons not to hire;
- decisive interview questions.

---

# 8. Company health, trajectory, and pain points

## 8.1 Purpose

Understand the economic and strategic context around the hire. This is not a generic company profile.

## 8.2 Questions

The system MUST answer:

1. How is the company doing?
2. What does its trajectory look like?
3. What are the biggest pain points?
4. What is management trying to improve?
5. What has become harder?
6. Where is management under economic, operating, customer, technology, risk, or organizational pressure?
7. Why might this role matter now?

## 8.3 Evidence hierarchy

```yaml
company_sources:
  primary:
    - earnings
    - annual_reports
    - quarterly_reports
    - investor_presentations
    - investor_day_materials
    - earnings_transcripts
    - official_strategy_statements
    - leadership_communications
    - regulatory_filings
    - M_and_A
    - restructuring_announcements
    - capital_allocation

  secondary:
    - credible_analyst_commentary
    - credible_trade_press
    - leadership_interviews
    - hiring_patterns
    - technology_announcements
    - competitor_moves
```

## 8.4 Required outputs

```yaml
company_trajectory:
  current_health: required
  growth_trajectory: required_or_unknown
  margin_trajectory: required_or_unknown
  strategic_priorities: []
  operating_pressures: []
  technology_pressures: []
  organizational_pressures: []
  risk_pressures: []
  talent_pressures: []
  biggest_pain_points: []
  why_now_for_role: required
  contradictions_or_uncertainties: []
  evidence: []
```

No Wikipedia-style summary. Every material finding SHOULD connect to the pursuit thesis.

---

# 9. Hiring-manager commercial pressure

## 9.1 Purpose

Determine what becomes materially easier or harder for the hiring manager depending on whether this hire succeeds.

This component MUST NOT stop at describing the hiring manager's responsibilities.

## 9.2 Causal chain

```text
company economics
    -> executive priority
    -> hiring-manager accountability
    -> operating constraint
    -> role mandate
    -> consequence of success or failure
```

## 9.3 Required questions

- What number, outcome, or strategic commitment is this leader likely responsible for?
- What is consuming management capacity?
- What is not scaling?
- What risks are accumulating?
- What has leadership likely committed upstream?
- What is the role expected to remove from the hiring manager's plate?
- What makes the hiring manager look successful in 6, 12, and 18 months?
- What failure would materially hurt them?
- What would they need to believe about the candidate?

## 9.4 Output

```yaml
commercial_pressure:
  statement: required
  pressure_tree: []
  success_6_months: required_or_unknown
  success_12_months: required_or_unknown
  success_18_months: required_or_unknown
  likely_objections_to_the candidate: []
  what_HM_needs_to_believe: []
  confidence: required
```

---

# 10. Stakeholder roadmap

## 10.1 Purpose

Map the decision system around the role, not just collect names.

## 10.2 Stakeholders to identify

```yaml
stakeholder_roles:
  - exact_hiring_manager
  - likely_skip_level
  - executive_sponsor
  - recruiter
  - talent_partner
  - critical_peer
  - functional_influencers
  - technical_influencers
  - business_influencers
  - risk_and_control_influencers
  - internal_connectors
  - alumni_paths
  - prior_relationships
  - mutual_connections
```

## 10.3 Per-person record

```yaml
stakeholder:
  identity: required
  title: required
  location: nullable
  role_in_decision:
    - DECIDES
    - SPONSORS
    - INFLUENCES
    - VALIDATES
    - RECRUITS
    - CONNECTS
  likely_interest: required_or_unknown
  likely_objection: required_or_unknown
  relationship_to_role: required_or_unknown
  connection_path: nullable
  verification_status:
    - VERIFIED
    - HIGH_CONFIDENCE
    - PROBABLE
    - UNKNOWN
  evidence: []
```

## 10.4 Rules

- Never declare a hiring manager from title proximity alone.
- Separate VERIFIED from PROBABLE.
- Preserve alternate hypotheses.
- Never manufacture reporting relationships.

---

# 11. Two-Notch-Up / Aditya Lens

## 11.1 Purpose

The Two-Notch-Up Lens is not merely "find the problem above the JD."

It MUST envision how the **business model, operating model, product, channel, customer relationship, value chain, or economic architecture may evolve** if the underlying market or technology discontinuity plays out.

The lens exists to prevent the candidate from solving only today's stated job while missing what the business could become.

## 11.2 Core question

> If the underlying technological, customer, competitive, regulatory, or economic discontinuity fully plays out, what might this business, product, operating model, or customer relationship become, rather than merely how should the current mandate be executed better?

## 11.3 Required levels

```yaml
two_notch_up:

  level_0_stated_job:
    question: "What does the requisition literally ask for?"

  level_1_underlying_outcome:
    question: "What business outcome or constraint sits underneath the stated responsibilities?"

  level_2_game_changer:
    question: "What technological, customer, competitive, regulatory, or economic discontinuity could make today's framing obsolete?"

  future_business_or_operating_model:
    question: "If that discontinuity is taken seriously, what could the business, product, channel, organization, customer relationship, or value chain become?"

  economic_consequence:
    question: "How does that future change growth, cost-to-serve, cost-to-change, revenue, risk, capacity, differentiation, or strategic control?"

  role_reinterpretation:
    question: "What does that imply this hire should really build toward now?"

  the candidate_legitimacy:
    question: "Can the candidate credibly help cause that evolution rather than merely sound visionary?"

  overreach_boundary:
    question: "Where would the thesis become speculative, presumptuous, or unsupported?"
```

## 11.4 Schwab reference pattern

For a retail web mandate, the relevant question is not only:

> How do we modernize the website?

The stronger lens asks whether the future of the web is principally a "site" at all.

A possible evolution is:

```text
website
    -> digital financial experience
    -> trusted financial agency / interaction layer
```

In that future, the organizing construct can shift away from pages and navigation toward:

```text
client intent
+ context
+ permissions
+ capabilities
+ intelligence
+ execution
+ controls
+ human judgment
```

As AI makes intelligence, software creation, and execution more abundant, scarce assets may increasingly include trusted context, permissioned action, coherent architecture, human judgment, and ownership of customer intent.

The lesson is not that every opportunity needs this exact thesis. The lesson is the operating pattern:

> **See the inflection -> define the future state -> redesign the system -> mobilize the enterprise -> change the economics.**

## 11.5 Guardrail

The Two-Notch-Up Lens MUST inform positioning only when evidence supports it.

It MUST NOT become a futuristic essay inserted mechanically into every pursuit.

---

# 12. Core of X

## 12.1 Purpose

Core of X is the unmistakable reason the company is hiring.

No resume, cover letter, or outreach SHOULD lock before Core of X is sufficiently clear.

## 12.2 Required formulation

```text
They need X to [change an economically meaningful outcome]
by [specific operating mechanism]
while [protecting or overcoming the critical constraint].
```

## 12.3 Required questions

- Why does this role exist?
- Why now?
- What business problem is underneath the responsibilities?
- What must materially change because this person was hired?
- What does success look like?
- What does failure look like?
- Why does the hiring manager care?
- Why is this more than a paraphrase of the JD?
- What part of Core X is fact versus inference?

## 12.4 Bad Core X

Examples of insufficient formulations:

- drive innovation;
- lead strategy;
- accelerate AI;
- transform customer experience;
- modernize technology;
- improve operational efficiency.

These MAY appear as ingredients but MUST NOT be accepted as Core of X by themselves.

## 12.5 Red-team questions

- Could this Core X apply to ten unrelated companies?
- Does company evidence support it?
- Does the JD support it?
- Does hiring-manager pressure support it?
- Would a native candidate recognize it as the real job?
- Can the candidate credibly solve it?
- Is it too narrow?
- Is it too visionary?
- Does it capture the economic mechanism?

## 12.6 Output

```yaml
core_of_x:
  statement: required
  why_now: required
  success_definition: required
  failure_definition: required
  evidence_chain: []
  inference_chain: []
  confidence: required
```

---

# 13. Positioning lock

## 13.1 Purpose

Converge on exactly what the candidate represents for the opportunity before producing final artifacts.

## 13.2 Lock contents

```yaml
positioning_lock:
  identity_anchor: required
  positioning_thesis: required
  altitude: required
  why_the candidate: required
  dominant_proof_environment: required
  proof_1: required
  proof_2: required
  proof_3: nullable
  supporting_proofs: []
  evidence_to_compress: []
  evidence_to_omit: []
  claims_prohibited: []
  native_candidate_counterargument: required
  differentiating_edge: required
```

## 13.3 Required causal chain

```text
commercial pressure
    -> Core of X
    -> the candidate positioning
    -> verified evidence
    -> measurable value
```

## 13.4 Memory test

> If the hiring manager remembers only one thing about the candidate, what exactly should it be?

The answer MUST be specific to the opportunity.

---

# 14. Positioning red-team loop

## 14.1 Maximum iterations

Maximum: **3** meaningful iterations.

The system MUST NOT polish indefinitely.

## 14.2 Passes

```yaml
red_team:

  pass_1_native_candidate:
    questions:
      - "Why hire the candidate instead of the obvious native candidate?"
      - "Where is domain translation required?"
      - "Where does positioning overstate direct experience?"
      - "What would make a recruiter reject him immediately?"

  pass_2_hiring_manager:
    questions:
      - "Does this solve my actual pressure?"
      - "Is the candidate operating at the right altitude?"
      - "Is the evidence relevant or merely impressive?"
      - "Is the mandate connection obvious?"
      - "Would I invest 30 minutes?"

  pass_3_executive_truth:
    questions:
      - "Any unsupported claims?"
      - "Any generic consulting language?"
      - "Any AI theater?"
      - "Any JD mimicry?"
      - "Any decisive proof missing?"
      - "Are we underselling breadth?"
      - "Are we overselling adjacency?"
      - "Has the Two-Notch-Up Lens become overreach?"
```

## 14.3 Exit criteria

```yaml
red_team_exit:
  - core_of_x_intact
  - credible_native_candidate_answer
  - strongest_evidence_surfaced
  - unsupported_material_claims_zero
  - material_ambiguity_resolved_or_flagged
  - memorable_positioning
  - role_specific_positioning
  - resume_outreach_cover_letter_can_share_the_same_lock
```

---

# 15. Two-page executive resume generator

## 15.1 Absolute requirements

```yaml
resume:
  page_count: 2
  format: DOCX
  ATS_safe: true
  positioning_lock_required: true
  core_of_x_required: true
  candidate_truth_required: true
```

The resume MUST be exactly two pages unless the product owner explicitly changes the rule.

## 15.2 Content principles

The resume MUST:

- demonstrate why the candidate can solve Core of X;
- preserve career richness and breadth;
- preserve executive scale;
- preserve meaningful verified metrics;
- foreground 2 to 3 proof environments most relevant to the mandate;
- retain additional breadth when materially useful;
- use role language only where factually natural;
- remain compelling to a human executive while surviving ATS extraction.

The resume MUST NOT:

- become a JD rewrite;
- become an ATS keyword dump;
- flatten the candidate into the narrowest version of the role;
- shorten the executive overview merely to solve pagination;
- remove important evidence simply to manufacture whitespace;
- leave conspicuous unnecessary white space;
- invent facts, scope, metrics, titles, dates, or ownership.

## 15.3 Executive overview

The overview MUST be substantial enough to establish:

- executive identity;
- scale;
- operating pattern;
- business outcomes;
- relevance to locked positioning.

The overview MUST NOT collapse into a generic three-line summary or adjective stack.

## 15.4 Layout logic

Pagination SHOULD be solved in this order:

1. remove low-value redundancy;
2. tighten low-value wording;
3. optimize information architecture;
4. adjust proof ordering;
5. make conservative spacing/layout adjustments;
6. preserve high-value proof and overview substance as long as possible.

The system MUST NOT solve page count by progressively starving the document.

## 15.5 QA

```yaml
resume_QA:

  semantic:
    - core_of_x_visible
    - positioning_lock_preserved
    - proof_priorities_preserved
    - factual_claims_traceable
    - native_candidate_objection_addressed_indirectly_through_evidence

  visual:
    - exactly_two_pages
    - no_conspicuous_dead_space
    - balanced_page_density
    - executive_readability
    - no_orphaned_headings
    - no_accidental_overflow
    - no_malformed_bullets

  machine:
    - DOCX_opens
    - ATS_text_extracts
    - no_hidden_corruption
    - no_fact_drift_from_canonical_truth
```

The system MUST compare:

```text
canonical truth
    -> positioning lock
    -> generated DOCX
    -> rendered pages
    -> extracted ATS text
```

before finalizing.

---

# 16. Hiring-manager outreach

## 16.1 Canonical structure

The Harvey outreach example establishes the required skeleton.

```text
SUBJECT
[Company / mandate]: [commercial outcome]

Hey [First name],

1. ROLE RECOGNITION
"I see you're hiring..." + one-sentence interpretation of what the role must accomplish.

2. CREDIBILITY BRIDGE
"I've spent much of my career doing the same underlying job..."
The bridge is mandate matching, not title matching.

3. A FEW RELEVANT PROOFS
Exactly 2 to 3 concise bullets.
Only highly relevant evidence.

4. WHAT COMES NEXT
The differentiated paragraph.
Show understanding of where the mandate or business must evolve,
not merely what the JD says.

5. OPTIONAL THOUGHT-LEADERSHIP GIFT
Only if this opportunity has been explicitly qualified for a gift asset.

6. LOCKED CLOSE
"If this looks like a fit, then feel free to forward this to your recruiter
and I'll work with them to get a call scheduled."

Regards,

${CANDIDATE_FIRST_NAME}

${CANDIDATE_FULL_NAME} | ${CANDIDATE_PHONE}
```

## 16.2 Hard rules

The email MUST be:

- short;
- forwardable;
- high-absorption;
- specific;
- tied to the hiring manager's commercial pressure;
- tied to Core of X;
- evidence-backed.

The email MUST NOT contain:

- generic praise;
- a biography;
- a resume summary;
- generic enthusiasm;
- multiple competing asks;
- fake familiarity;
- unsupported internal diagnoses presented as fact;
- a mini cover letter;
- generic "AI transformation" language.

## 16.3 Variations

Generate **2 to 3 materially different** variations when appropriate.

Variations MUST differ in strategic emphasis, not adjective choice.

Possible strategic patterns include:

```yaml
outreach_variants:
  - economics_first
  - mandate_first
  - executive_pattern_or_insight_first
```

The red team MUST answer:

> Is this the best foot forward for this exact person, exact role, and exact commercial pressure?

## 16.4 Thought-leadership paragraph

The email MUST remain complete without a thought-leadership asset.

If an asset is included, the email SHOULD naturally arrive at the underlying business question before offering the asset as a gift.

---

# 17. Hiring-manager identity, exact email, local time, and send planning

## 17.1 Purpose

Resolve the right human and the right communication channel before execution.

## 17.2 Hiring-manager confidence

```yaml
HM_confidence:
  - VERIFIED
  - HIGH_CONFIDENCE
  - PROBABLE
  - UNKNOWN
```

A title-adjacent executive MUST NOT be labeled the hiring manager without sufficient evidence.

## 17.3 Email verification

Acceptable as exact:

- publicly verified exact address;
- exact address from a trusted contact source;
- exact address from prior correspondence.

Not acceptable as "verified exact":

- guessed corporate pattern;
- inferred first.last pattern;
- weak third-party enrichment.

If exact email is unavailable:

```yaml
email_status: UNVERIFIED
```

The system MUST NOT convert a guessed email into a fact.

## 17.4 Time zone and scheduling

Determine the hiring manager's working time zone from the best available evidence.

Output:

```yaml
send_plan:
  hiring_manager_timezone: required_or_unknown
  hiring_manager_local_time_at_planned_send: required
  recommended_send_date: required
  recommended_send_time_local: required
  converted_the candidate_time: required
  rationale: required
  subject: required
  final_message: required
  attachments: []
```

Outbound sending remains a controlled action unless a later explicit autonomy policy changes this.

---

# 18. Desired salary answer policy

## 18.1 Default free-text answer

Lock this default:

> **Open to a market-competitive package commensurate with the scope, mandate, and overall opportunity.**

## 18.2 Field behavior

```yaml
salary_question_policy:

  free_text:
    answer: "Open to a market-competitive package commensurate with the scope, mandate, and overall opportunity."

  dropdown_or_range:
    behavior: "select only under a pre-approved truthful range policy"

  mandatory_numeric:
    behavior: "do not invent a workaround or false number; invoke a pre-approved numeric-field policy"

  prohibited:
    - fabricated_salary
    - deceptive_placeholder_number
    - false_compensation_history
```

A separate numeric-field policy MUST be approved before fully autonomous application.

---

# 19. Core-of-X cover letter

## 19.1 Trigger

Generate only when:

- the company career site includes a clear cover-letter upload or text section; or
- the application explicitly requests one; or
- the candidate explicitly chooses to use one.

## 19.2 Purpose

The cover letter is not another candidate biography.

Its center of gravity is:

> **What could the hiring manager's and company's operating world look like if this hire succeeds, and how would the candidate help make that future credible?**

The letter SHOULD help the reader picture their own organization operating differently with the candidate in the seat.

## 19.3 Architecture

```yaml
cover_letter:

  section_1_possibility:
    purpose: "Describe what becomes possible if the mandate succeeds."

  section_2_shift:
    purpose: "Describe what must change in operating model, technology, organization, decisions, customer experience, or execution."

  section_3_way_there:
    purpose: "Provide the candidate's practical operating point of view on causing the shift."

  section_4_measured_warrants:
    purpose: "Pepper 2 to 3 pieces of highly relevant evidence into the argument as credibility, not biography."

  section_5_destination:
    purpose: "Return to what the company's or hiring manager's world looks like when the system is working."
```

## 19.4 First-order consequences test

A strong cover letter SHOULD make clear:

- what becomes easier;
- what becomes faster;
- what becomes more predictable;
- what management burden disappears;
- what becomes economically scalable;
- what leadership can decide more confidently;
- what customer, employee, or business outcome changes.

## 19.5 Evidence rule

Pattern:

```text
future-state assertion
    -> operating mechanism
    -> one measured analogous proof
    -> back to their business
```

The letter MUST NOT retread LinkedIn or the resume.

## 19.6 Guardrails

The letter MUST NOT:

- diagnose internal failures as facts without evidence;
- overpromise;
- become a chronological career summary;
- become generic "why I am excited" prose;
- flatter the company;
- repeat the JD;
- repeat the resume;
- use empty transformation rhetoric.

## 19.7 Test

> If the resume disappeared, would this still be worth reading?

If not, rewrite it.

---

# 20. Optional thought-leadership one-pager

## 20.1 Status

Default: **NONE**

This is a gift, not a throwaway workflow artifact.

The system MUST NOT generate one for every qualified role.

## 20.2 Qualification gate

A one-pager MAY be generated only when:

- the opportunity is important enough to justify the investment;
- Core of X is strong;
- the candidate has something genuinely distinctive and defensible to say;
- the asset is likely to improve engagement or market positioning;
- it can stand independently as quality thought leadership;
- the candidate or an explicitly approved policy qualifies the opportunity for this treatment.

## 20.3 Decision states

```yaml
thought_leadership_decision:
  GENERATE:
    meaning: "There is a genuinely original, defensible thesis and the opportunity merits the gift."

  REUSE_OR_ADAPT:
    meaning: "An existing the candidate thesis already addresses the problem and can be appropriately reused or lightly adapted."

  NONE:
    meaning: "Nothing sufficiently valuable should be manufactured."
```

## 20.4 Asset objective

The one-pager should resonate with the target company without being so company-owned that it has no independent value.

It MAY become a reusable asset for:

- LinkedIn;
- executive conversations;
- recruiters;
- conferences;
- adjacent opportunities;
- relationship building.

## 20.5 Harvey reference pattern

The Harvey example used the thesis:

> **Harvey's NRR Will Be Won Long Before Renewal**

The key idea was not generic Customer Success improvement.

The underlying argument was:

> NRR is an output. The management system sits upstream in workflow penetration, measurable outcomes, executive conviction, and the ability to scale the right intervention without relying on CSM heroics.

The lesson:

- move upstream from the visible metric;
- expose the management system beneath the metric;
- connect operational behavior to commercial outcomes;
- produce a thesis that is useful even beyond the immediate application.

## 20.6 Schwab reference pattern

The Schwab example is a business-evolution thesis.

The core question is whether "retail web" remains principally a website in an agentic future.

Possible conceptual evolution:

```text
website
    -> digital financial experience
    -> trusted financial agency / interaction layer
```

The lesson:

- ask whether the object named by the current role remains the correct object in the future;
- identify the market/technology inflection;
- describe the future business or operating architecture;
- connect that evolution to economics and strategic control.

## 20.7 Quality tests

### Hiring-manager test

> Did this person understand a problem I actually care about unusually well?

### Market test

> Would another sophisticated executive in this industry find this worth reading even without knowing which job triggered it?

If either test fails, do not produce or send the asset.

## 20.8 Anti-patterns

Never create:

- generic "5 ways to..." content;
- a company summary disguised as thought leadership;
- a resume in one-page visual form;
- AI-slop listicles;
- a forced asset because the workflow expects one;
- a thesis the candidate cannot defend in conversation.

---

# 21. Autonomous company-career-site application engine

## 21.1 Primary rule

Applications MUST occur only on the company's official career site.

Third-party sources MAY discover a role but MUST NOT be the application destination.

## 21.2 Inputs

```yaml
application_inputs:
  - locked_opportunity
  - latest_role_locked_resume_DOCX
  - canonical_candidate_profile
  - canonical_application_answers
  - optional_cover_letter
  - salary_policy
  - work_authorization_truth
  - location_preferences
```

## 21.3 Candidate profile vault

Structured reusable information SHOULD include:

```yaml
candidate_profile_vault:
  - legal_name
  - preferred_name
  - contact_information
  - address
  - work_authorization
  - sponsorship
  - employment_history
  - education
  - certifications
  - skills
  - compensation_answers
  - location
  - relocation
  - travel
  - optional_demographic_answers
  - LinkedIn
  - website
  - other_repeated_fields
```

## 21.4 ATS adapters

The system SHOULD support explicit adapters for common ATS platforms rather than one brittle universal script.

```yaml
ATS_adapters:
  - Workday
  - Greenhouse
  - Lever
  - iCIMS
  - SmartRecruiters
  - Oracle
  - Taleo
  - custom_company_career_site
```

## 21.5 Execution pattern

```text
resolve official career-site role
    -> detect ATS
    -> authenticate
    -> create or reuse candidate profile
    -> upload latest role-locked resume
    -> parse
    -> compare parsed data against canonical truth
    -> correct fields
    -> answer known questions
    -> handle novel questions under policy
    -> attach cover letter only if required/selected
    -> pre-submit validation
    -> submit
    -> capture confirmation
    -> update opportunity record
```

## 21.6 Deterministic-first principle

Known form fields and repeated answers MUST come from canonical structured data without AI generation.

AI MAY be used only for:

- genuinely novel free-text questions;
- ambiguous questions requiring judgment;
- role-specific written responses.

AI MUST NOT invent candidate facts.

## 21.7 Pre-submit validation

```yaml
pre_submit:
  - correct_company
  - correct_role
  - correct_requisition
  - correct_official_career_site
  - correct_resume_version
  - correct_cover_letter_version_if_any
  - required_fields_complete
  - canonical_facts_preserved
  - no_duplicate_application
  - salary_answer_complies_with_policy
  - no_accidental_third_party_submission
```

## 21.8 Blocked states

```yaml
application_blockers:
  - CAPTCHA
  - MFA_requiring_human_interaction
  - site_malfunction
  - novel_legal_attestation
  - novel_factual_question_without_canonical_answer
  - ambiguous_voluntary_disclosure
  - duplicate_account_conflict
  - numeric_salary_field_without_approved_policy
```

The engine MUST checkpoint and resume. It MUST NOT blindly restart and risk duplicate submission.

## 21.9 Post-submit record

Capture:

- timestamp;
- confirmation number;
- confirmation page or receipt;
- exact resume version;
- exact cover-letter version;
- submitted answers;
- application status.

---

# 22. Opportunity search and faceted browsing

## 22.1 Purpose

The user needs a conventional, fast way to work across the opportunity corpus.

This is not a natural-language chat interface.

## 22.2 Search box

Provide a standard text search input.

Example:

```text
[ Search opportunities... ]
```

Search SHOULD index, where available:

```yaml
search_index:
  - company
  - role_title
  - requisition_id
  - industry
  - sub_industry
  - location
  - hiring_manager
  - recruiter
  - stakeholder_names
  - core_of_x
  - mandate
  - commercial_pressure
  - notes
  - role_family
```

## 22.3 Search behavior

Search SHOULD be:

- instantaneous;
- case-insensitive;
- partial-word tolerant;
- typo tolerant;
- capable of quoted exact phrase matching;
- capable of highlighting matches;
- ranked so exact company/title/requisition matches surface first.

No LLM call is required.

## 22.4 Facets

In addition to the full qualification filters, the UI MUST make these especially easy to work with:

```yaml
key_facets:
  - advertised_level
  - likely_real_level
  - mandate_altitude
  - scope_altitude
  - reporting_altitude
  - compensation_altitude
  - the candidate_relative_level
  - industry
  - sub_industry
  - location
  - remote_hybrid_onsite
  - company_scale
  - public_private_PE_backed
  - role_family
  - mandate_archetype
  - native_candidate_class
  - winability
  - company_trajectory
  - core_of_x_strength
  - hiring_manager_pressure
  - stakeholder_access
  - warm_path
  - posting_age
  - application_status
  - overall_priority
```

---

# 23. Opportunity command surface

## 23.1 Default view

Default view: **Intake Backlog**

## 23.2 Role card

A role card SHOULD show enough signal to make triage easy:

```yaml
role_card:
  - company
  - title
  - advertised_level
  - likely_real_level
  - location
  - compensation
  - freshness
  - qualification_class
  - native_candidate_class
  - winability
  - core_of_x_summary
  - company_trajectory
  - hiring_manager_identity
  - hiring_manager_pressure
  - stakeholder_access
  - positioning_status
  - resume_status
  - outreach_status
  - application_status
  - thought_leadership_status
```

## 23.3 Role workspace

Suggested sections:

```yaml
role_workspace:
  - Role
  - Qualification
  - Company
  - Native_Candidate
  - Commercial_Pressure
  - Stakeholders
  - Two_Notch_Up
  - Core_of_X
  - Positioning
  - Resume
  - Outreach
  - Cover_Letter
  - Thought_Leadership
  - Application
  - Activity
  - Evidence
```

A board view MAY exist for usability, but it MUST NOT dictate the underlying architecture.

---

# 24. Dependency, invalidation, and concurrency controller

## 24.1 Purpose

Avoid linear workflow assumptions and prevent stale artifacts.

## 24.2 Parallel work after qualification

When a role merits deep qualification, these analyses MAY run concurrently:

```yaml
parallel_after_qualification:
  - company_trajectory
  - native_candidate_analysis
  - role_readiness
  - stakeholder_discovery
```

## 24.3 Invalidation examples

```yaml
invalidation:

  when_company_trajectory_changes:
    reconsider:
      - commercial_pressure
      - core_of_x
      - two_notch_up
      - opportunity_priority

  when_hiring_manager_changes:
    invalidate:
      - commercial_pressure
      - outreach
      - contact_email
      - timezone
      - send_schedule

  when_JD_changes:
    compare_versions: true
    selectively_invalidate:
      - weighted_criteria
      - native_candidate_analysis
      - core_of_x
      - positioning_lock
      - resume
      - outreach
      - cover_letter
      - application_payload

  when_new_candidate_evidence_is_verified:
    reconsider:
      - evidence_map
      - native_candidate_analysis
      - positioning
      - affected_resumes
      - affected_outreach

  when_core_of_x_changes:
    mandatory_invalidate:
      - positioning_lock
      - resume
      - outreach
      - cover_letter
      - thought_leadership_if_based_on_prior_core
```

Recompute only dependencies that are stale. Do not regenerate everything blindly.

## 24.4 State model

```yaml
component_state:
  - READY
  - RUNNING
  - BLOCKED
  - STALE
  - INVALIDATED
  - LOCKED
  - QA_PASSED
  - REJECTED
```

---

# 25. Reliability contract

## 25.1 Truth

Candidate facts originate only from canonical verified sources or explicit user-provided corrections.

## 25.2 Provenance

Every material company, role, person, and candidate assertion SHOULD retain:

- source;
- retrieval/capture time;
- confidence;
- classification as VERIFIED / INFERRED / UNKNOWN.

## 25.3 No drift

Locked positioning MUST NOT silently change downstream.

## 25.4 Fail closed

The system MUST stop rather than guess when:

- hiring-manager identity is materially uncertain and exact identity is required;
- role is closed;
- requisition mismatches;
- consequential candidate fact is unavailable;
- Core of X is unresolved;
- resume QA fails;
- application requires misrepresentation;
- salary field requires an unapproved numeric policy;
- official company career-site destination cannot be verified.

## 25.5 Token economics

Spend AI tokens primarily on:

- native-candidate reasoning;
- weighted role analysis;
- company pressure interpretation;
- hiring-manager commercial pressure;
- stakeholder inference;
- Two-Notch-Up / Aditya Lens;
- Core of X;
- positioning;
- red-team work;
- high-value writing;
- genuinely novel application questions.

Do not spend AI tokens primarily on:

- ingestion;
- polling;
- deduplication;
- search;
- filtering;
- known form filling;
- status changes;
- deterministic validation;
- file movement.

## 25.6 Auditability

For every pursued opportunity, the system MUST be able to answer:

1. Why did we ingest it?
2. Why did we pursue it?
3. What is the likely real level versus advertised level?
4. Who is the native candidate?
5. Why can the candidate win or not win?
6. How is the company doing?
7. What is changing in the company's trajectory?
8. What are the material pain points?
9. What is the hiring manager's commercial pressure?
10. Who actually decides and influences the hire?
11. What is the Two-Notch-Up future-state thesis?
12. What is Core of X?
13. What evidence supports the positioning?
14. Why was this resume produced?
15. Why was this outreach version chosen?
16. Was a thought-leadership gift justified?
17. Exactly what was submitted?
18. What changed from the prior version?
19. Which conclusions are verified versus inferred?
20. What is the next best action?

---

# 26. Non-goals and anti-patterns

The system MUST NOT:

- make application count the primary success metric;
- treat every opportunity equally;
- force a thought-leadership asset into every pursuit;
- turn the Two-Notch-Up Lens into generic futurism;
- infer exact hiring-manager identity from org-chart proximity;
- invent email addresses and label them verified;
- tailor by rewriting facts;
- create generic cover letters;
- generate generic "AI slop" thought leadership;
- repeatedly redesign a proven outreach format;
- compress the executive resume until breadth disappears;
- leave large avoidable whitespace to satisfy a two-page constraint;
- turn the UI lifecycle into the architecture;
- rerun every component when one field changes;
- spend AI tokens on work that can be deterministic;
- silently progress through unresolved high-consequence unknowns.

---

# 27. Approval boundaries for this reset

This repository currently represents **planning only**.

No implementation is authorized by this specification alone.

Before build begins, the product owner should explicitly approve at least:

```yaml
approval_needed_before_build:
  - canonical_system_boundary
  - component_scope
  - candidate_truth_source_of_record
  - intake_source_strategy
  - qualification_rules
  - autonomy_policy_for_applications
  - numeric_salary_field_policy
  - outbound_email_send_policy
  - data_storage_and_privacy_model
  - technical_architecture
  - deployment_model
```

---

# 28. Definition of done for the specification phase

The specification phase is complete when:

- the user agrees the system is not being modeled as linear;
- intake and qualification criteria are complete enough for backlog filtering;
- native-candidate analysis reflects the Resume Maker lessons;
- company trajectory, commercial pressure, stakeholder roadmap, Two-Notch-Up Lens, Core of X, positioning lock, and red-team rules are explicit;
- two-page resume requirements are unambiguous;
- outreach structure and exact close/signature are locked;
- salary default is locked;
- cover-letter philosophy is future-state oriented and non-redundant;
- thought leadership is explicitly optional and treated as a gift;
- application execution is limited to official company career sites;
- conventional text search and faceted filtering are specified;
- truth, provenance, invalidation, and fail-closed behavior are explicit;
- implementation has not begun without approval.

---

# 29. Locked wording and contracts

## 29.1 Hiring-manager close

The public repository stores only the template:

```text
If this looks like a fit, then feel free to forward this to your recruiter and I'll work with them to get a call scheduled.

Regards,

${CANDIDATE_FIRST_NAME}

${CANDIDATE_FULL_NAME} | ${CANDIDATE_PHONE}
```

The actual values MUST be resolved from the private runtime provider immediately before artifact generation or sending.

## 29.2 Desired salary, free text

```text
Open to a market-competitive package commensurate with the scope, mandate, and overall opportunity.
```

## 29.3 Resume

```yaml
page_count: 2
format: DOCX
overview: "must retain substance"
breadth: "must remain visible"
white_space: "no conspicuous unnecessary white space"
truth: "no drift"
```

## 29.4 Thought leadership

```yaml
default: NONE
principle: "gift, not throwaway collateral"
generation: "only for explicitly qualified opportunities"
```

---

# 30. Final product principle

The system should spend its intelligence where judgment changes the outcome.

Broad discovery should be cheap.
Qualification should be ruthless.
Truth should be stable.
Core of X should be unmistakable.
The Two-Notch-Up Lens should reveal what the business may become, not merely what the current job should do.
Positioning should survive a native-candidate challenge.
Artifacts should be consequences of the thesis, not independent writing exercises.
Thought leadership should be a gift.
Applications should execute reliably on official company career sites.
And every important conclusion should be explainable, traceable, and revisable when new evidence arrives.
