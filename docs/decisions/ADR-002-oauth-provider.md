# ADR-002 — OAuth Provider: Google OAuth 2.0

**Status:** Accepted  
**Date:** 2026-05-25  
**Author:** Maria Imran  
**Phase:** 1 — Foundations

---

## Context

The AI-Doc platform requires user authentication. Users must be able to sign in and have their identity persisted in the `users` table so that their sessions, pipeline runs, documents, and chat history are associated with their account across all phases.

Three approaches were evaluated:

| Option | Approach | Notes |
|--------|----------|-------|
| A | Email + password | Requires password hashing, reset flows, email verification |
| B | Google OAuth 2.0 | Third-party identity provider, authorization code flow |
| C | GitHub OAuth | Third-party identity provider, developer-oriented |

The decision needed to account for ease of implementation, security, and the realistic user base of the platform.

---

## Decision

**Option B — Google OAuth 2.0** is adopted as the authentication provider.

The authorization code flow is implemented using `authlib`. The backend exposes two endpoints:

- `GET /auth/login` — builds the Google authorization URL and redirects the user
- `GET /auth/callback` — exchanges the authorization code for an access token, fetches the user's Google profile, upserts the record into the `users` table, creates a `sessions` record, and returns a signed JWT in an `httpOnly` cookie

The frontend never handles the OAuth token exchange — all credential handling stays in the backend.

---

## Reasoning

### Why not email and password

Email and password authentication requires implementing password hashing (bcrypt), secure reset flows, email verification, and brute-force protection. These are all solved problems, but implementing them correctly takes significant time and introduces attack surface that is not relevant to the AI-engineering focus of this programme. Delegating identity to Google removes this entire category of risk.

### Why Google over GitHub

GitHub OAuth is a natural fit for developer tools, but Google accounts are universal — every user has one, regardless of whether they use GitHub. Google's OAuth 2.0 implementation is stable, well-documented, and directly supported by `authlib`. The user profile response includes `email`, `name`, and `picture` (avatar), which maps cleanly onto the `users` table schema.

GitHub was not ruled out on technical grounds; it was ruled out because Google is the safer default for a platform that may be shown to non-technical stakeholders in Phase 5.

### Why `authlib` over `google-auth`

`authlib` is a general-purpose OAuth 2.0 and OpenID Connect library for Python. It integrates directly with `httpx` (the async HTTP client already in `requirements.txt`) and works without coupling the backend to any single provider. If a second provider is added in future, `authlib` handles both from the same code path. `google-auth` is a Google-specific library that provides less flexibility.

### Security: `httpOnly` cookie over `localStorage`

The JWT session token is returned in an `httpOnly` cookie, not in the JSON response body or `localStorage`. `httpOnly` cookies are not accessible to JavaScript, which eliminates the entire class of XSS-based token theft. This is the approach recommended by OWASP and is revisited in the Phase 5 security review.

---

## Consequences

**Setup required before running:**

- A Google Cloud project must be created at console.cloud.google.com
- OAuth 2.0 credentials (Client ID + Client Secret) must be generated
- `http://localhost:8000/auth/callback` must be added as an authorised redirect URI for local development
- `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` must be set in `.env` (never committed)

**Schema impact:**

The `users` table stores `provider='google'` and `provider_user_id` (the Google `sub` claim). The unique constraint on `(provider, provider_user_id)` ensures that a returning user always maps to the same row regardless of whether their email changes.

**Accepted costs:**

- Users without a Google account cannot sign in. This is acceptable for the current scope.
- The platform depends on Google's OAuth infrastructure being available. Downtime at Google would prevent sign-in.

---

## Alternatives considered and rejected

**Email + password** — rejected because implementing it correctly requires significant work (hashing, reset flows, verification) that is out of scope for a programme focused on AI engineering. The attack surface is also higher than delegating to a mature identity provider.

**GitHub OAuth** — rejected in favour of Google because GitHub accounts are not universal. Would be a valid addition in a future phase if the platform targets a developer-only audience.

---

## Review notes

This decision should be revisited if:

- The platform requires a second OAuth provider (GitHub, Microsoft) — `authlib` supports this without architectural change.
- The platform is opened to users who do not have Google accounts.

---

*ADR-002 — accepted — no further review required unless the conditions above are met.*
