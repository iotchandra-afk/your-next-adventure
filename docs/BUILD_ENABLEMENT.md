# YourNextAdventure Build Enablement

**Status:** Active enablement checklist

This document records the minimum external access, secrets, and one-time user actions required to build and operate the first live YourNextAdventure system without repeatedly interrupting the user.

## Build principle

Use the minimum necessary infrastructure for the first live system. Keep GitHub as the source of truth. Keep private data and secrets outside the public repository. Prefer direct public ATS/company sources, deterministic processing, PostgreSQL, and GitHub-native execution before adding paid infrastructure.

## Already enabled

- GitHub repository `iotchandra-afk/your-next-adventure`
- GitHub write access for the connected integration
- Public repository with private-data boundary already defined
- Supabase connection is available
- Existing Supabase organization is visible
- Build authorization granted

## Required before unattended live operation

### 1. Fresh Supabase runtime project

Recommended: create a new `YourNextAdventure-dev` project rather than reusing the prior `YourNextMove-dev` project.

User must explicitly identify the Supabase organization in which the new project should be created. Cost confirmation must be obtained before project creation.

### 2. GitHub Pages

For the first live cockpit, use GitHub Pages as a zero-cost deployment target for the authenticated React application.

User action:
- Repository Settings -> Pages
- Source -> GitHub Actions

Expected initial URL:
`https://iotchandra-afk.github.io/your-next-adventure/`

### 3. GitHub Actions secrets

Never paste these values into chat or commit them to GitHub.

Create repository secrets under:
Repository Settings -> Secrets and variables -> Actions

Required secrets:
- `OPENAI_API_KEY`
- `SUPABASE_SECRET_KEY`

The Supabase project URL and publishable key are not secret and can be supplied to the public client safely when Row Level Security is correctly configured.

### 4. OpenAI API billing/key

A runtime API key with billing enabled is required for high-value reasoning capabilities. The first implementation should route deterministic work without model calls and use expensive reasoning only after qualification.

### 5. Private candidate truth

Do not place candidate identity, resume history, contact information, verified metrics, work authorization, compensation answers, or relationship notes in this public repository.

Before candidate-specific qualification and artifact generation are certified, provide one canonical private source bundle, ideally:
- current canonical resume
- application-answer truth sheet if one exists
- any verified evidence file not already represented in the resume

This can be uploaded privately to the conversation or injected into the private Supabase runtime after the data boundary is created.

### 6. Single-user authentication

The cockpit must not expose pursuit history publicly.

Initial approach:
- Supabase Auth
- one authenticated user
- Row Level Security on every user-facing table
- private `app_users` allowlist

After the first frontend deploy, the user signs in once. The resulting auth user ID is allowlisted in the private database. No standalone public data access is permitted.

## Not required for first live core

Do not block the initial release on:
- Temporal Cloud
- Browserbase
- Vercel
- Langfuse paid tier
- Kafka/NATS
- Meilisearch
- graph database
- vector database
- Gmail/Calendar OAuth
- ATS login credentials
- commercial job-data feeds
- contact-enrichment subscriptions

These are added only after a measured capability or reliability gap exists.

## Later enablement, before outbound/application automation

### Gmail / Calendar

When outbound automation is enabled, use OAuth rather than passwords. Store tokens in the private runtime/secrets layer. Until then, outreach remains generated and reviewable but not autonomously sent from the deployed app.

### ATS execution

Do not collect passwords in the repository or chat. Interactive sign-in/persistent browser sessions should be introduced only when official-career-site application execution is being certified.

### Commercial discovery or enrichment

Paid search/job/contact data is optional. Add only when direct official sources fail a measured recall or verification requirement.

## Initial production architecture

For the first live system:

- GitHub: canonical source and CI/CD
- GitHub Actions: scheduled intake, reconciliation, qualification, evals
- Supabase/PostgreSQL: canonical runtime state, Auth, RLS, realtime activity
- React + TypeScript: glass cockpit
- GitHub Pages: initial authenticated frontend hosting
- OpenAI provider adapter: high-value reasoning only
- Public ATS/company endpoints: intake before paid data sources
- Playwright: tests and later browser execution only where HTTP is insufficient

This is an implementation choice for the first live system, not a permanent constraint. External services remain behind adapters/contracts.

## User-interruption policy

Once the required enablement above is complete, build work should continue without asking the user for routine implementation decisions. Interrupt only for:
- a material paid-service commitment
- a security/privacy boundary change
- destructive production operation
- consequential factual ambiguity that cannot be safely resolved
- outbound communication or final application submission when the current autonomy policy requires approval
- a genuinely blocking external account action that cannot be performed through available tools
