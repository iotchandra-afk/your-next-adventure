# Private Data Injection

**Purpose:** Keep the GitHub repository public while supplying private candidate data safely at runtime.

## Recommended model

Use three separate layers:

```text
PUBLIC GITHUB REPOSITORY
        |
        | references logical keys only
        v
PRIVATE PROFILE STORE
(candidate facts and private operating context)
        |
        v
SECRET STORE
(API keys, OAuth tokens, session credentials)
```

The public repository should never be the source of truth for personal candidate information.

## 1. Private profile store

This stores private but non-secret operating data, for example:

- name
- phone
- email
- address
- canonical resume data
- employment history
- verified metrics
- education
- work authorization
- compensation preferences
- canonical application answers
- private relationship notes

### Recommended production choices

Use one of:

1. **Private database with row-level access controls**, preferred for a real application.
2. **Encrypted local/private YAML or JSON file**, acceptable during local development.
3. **Private object storage**, useful for resumes and generated documents.

The application should expose a logical provider interface such as:

```text
candidate.profile.identity
candidate.profile.experience
candidate.profile.evidence
candidate.application.answers
candidate.relationships
```

Code should not care whether those values came from Supabase, a local encrypted file, or another secure provider.

## 2. Secret store

Secrets should be kept completely separate from profile data.

Examples:

- API keys
- OAuth refresh tokens
- browser automation credentials
- ATS session secrets
- encryption keys

Use environment variables or a managed secret store in deployment.

Never store real secrets in:
- source code
- JSON committed to Git
- YAML committed to Git
- GitHub issues
- test fixtures
- logs

## 3. Public configuration example

The repository may include a schema-only example:

```yaml
candidate:
  identity:
    first_name: "${CANDIDATE_FIRST_NAME}"
    full_name: "${CANDIDATE_FULL_NAME}"
    phone: "${CANDIDATE_PHONE}"
    email: "${CANDIDATE_EMAIL}"

  profile_provider:
    type: "private"

  application_answers_provider:
    type: "private"

  relationships_provider:
    type: "private"
```

No real values belong in the example.

## 4. Runtime resolution

Before a component runs:

```text
component requests logical field
        ->
private context loader resolves allowed value
        ->
policy layer checks whether component may access it
        ->
value is supplied in-memory
        ->
value is not written back to the public repository
```

For example, the public outreach template contains:

```text
Regards,

${CANDIDATE_FIRST_NAME}

${CANDIDATE_FULL_NAME} | ${CANDIDATE_PHONE}
```

At runtime, the template renderer obtains the real values from the private profile store.

## 5. Separation by sensitivity

Recommended classification:

| Class | Examples | Storage |
|---|---|---|
| Public | specs, schemas, rules, templates | Public GitHub |
| Private profile | resume, phone, address, application answers | Private DB / encrypted file |
| Secret | API keys, OAuth tokens, sessions | Secret manager / env |
| Generated private artifact | role-specific resume, application copy, private outreach | Private artifact store |

## 6. Local development

The public repository may include:

```text
config/candidate.example.yaml
.env.example
```

The developer creates locally:

```text
config/candidate.private.yaml
.env
```

Both real files must be listed in `.gitignore`.

## 7. Production

Preferred pattern:

```text
Application
   |
   +--> Candidate Profile Provider
   |       -> private database / secure object storage
   |
   +--> Secret Provider
   |       -> deployment secret manager
   |
   +--> Public Rules & Templates
           -> GitHub repository
```

This gives the product a public, inspectable architecture without exposing the candidate's personal operating data.
