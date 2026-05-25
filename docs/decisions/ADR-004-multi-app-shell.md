# ADR-004 — Multi-Application Shell Architecture

**Status:** Accepted  
**Date:** 2026-05-25  
**Author:** Maria Imran  
**Phase:** 1 — Foundations

---

## Context

The AI-Doc platform is not a single application — it is a shell that hosts multiple distinct applications under one authenticated session. Phase 1 registers Home and Docs. Phase 2 adds Chat. Phase 3 adds Agents. Phase 4 adds Knowledge. Each application has its own sub-navigation, its own routes, and its own UI, but they all share the same top-level navigation bar, the same authentication state, and the same user session.

A structural decision is needed for how these applications are registered, rendered, and navigated between — before any application-specific UI is built.

Two approaches were evaluated:

| Option | Approach |
|--------|----------|
| A | Each application is an independent React app with its own entry point, composed at the routing layer |
| B | A single React app with a central app registry; each registered app is a route within the same application |

---

## Decision

**Option B — a single React app with a central app registry** is adopted.

A registry is defined as a plain TypeScript array. Each entry describes one application:

```ts
type AppEntry = {
  name: string;      // display name in the top nav
  path: string;      // base route path, e.g. "/chat"
  icon: string;      // icon name or component reference
  component: React.LazyExoticComponent<any>;  // lazily-loaded root component
};
```

The top-level `App.tsx` renders:
1. An `AuthGuard` — redirects unauthenticated users to `/login`
2. A `TopNav` — generated from the registry array, so adding an app to the registry automatically adds it to the nav
3. A `Routes` block — each registry entry maps to a `<Route path="{entry.path}/*" element={<entry.component />} />`

Each application component owns its own sub-routes (using nested `<Routes>`) and its own sub-navigation.

---

## Reasoning

### Why a registry over independent entry points

Independent React apps (Option A) would require a reverse proxy to route `/`, `/chat`, `/docs` etc. to different build outputs, separate `npm build` steps, and no shared state between apps. Sharing the authenticated user object across app boundaries would require either duplicating the auth check in every app or using cookies alone — neither of which is clean.

The registry pattern keeps the shell thin and the apps decoupled. The shell knows only the name, path, and entry component of each app. The apps know nothing about each other. Adding a Phase 3 app means adding one object to the registry array — no routing config changes, no proxy rules, no build pipeline changes.

### Why lazy loading

Each application component is loaded with `React.lazy()`. This means the JavaScript for Chat, Agents, and Knowledge is not downloaded until the user navigates to those routes. In Phase 1 this does not matter — the apps are stubs. By Phase 4, the Knowledge application will have a document upload interface and a RAG chat component that should not be bundled with the Phase 1 Home page. Lazy loading is the correct default from the start.

### Why the top nav generates from the registry

Hardcoding nav links creates a maintenance liability: every time a new app is registered, the nav must be updated separately. Generating the nav from the same array as the routes means a new app appears in the nav automatically. It also means the nav is always consistent with the registered routes — no orphaned links or missing entries.

### Auth at the shell level

Authentication is enforced by `AuthGuard` at the shell level, wrapping all registered app routes. Individual apps do not implement their own auth checks. This ensures that:
- There is exactly one place where the auth redirect logic lives.
- A new app added to the registry is automatically protected without any per-app work.
- The authenticated user object is available to all apps via a shared React context.

---

## Consequences

**Shell responsibilities (stay in `App.tsx` / `TopNav`):**
- Reading the app registry
- Rendering the top navigation
- Enforcing authentication before rendering any app
- Providing the user context to all child routes

**Application responsibilities (each app's root component):**
- Rendering its own sub-navigation (e.g. Conversation / History / Settings for Chat)
- Defining its own nested routes with `<Routes>`
- Fetching its own data from the API

**Accepted costs:**
- All apps are bundled into the same Vite project. A very large Phase 4 Knowledge component could affect initial build time, mitigated by lazy loading.
- The registry is defined in code, not in a config file or database. Adding an app requires a code change and a deployment. This is the correct tradeoff at this scale — a database-driven registry would be overengineering for five known apps.

**Phase 1 registered apps:**

| Name | Path | Phase introduced |
|------|------|-----------------|
| Home | `/` | 1 |
| Docs | `/docs` | 1 |
| Chat | `/chat` | 2 (stub in Phase 1) |
| Agents | `/agents` | 3 (stub in Phase 1) |
| Knowledge | `/knowledge` | 4 (stub in Phase 1) |

All five apps are registered as stubs from Phase 1 so the nav reflects the full platform shape from day one. Stub routes render a placeholder "Coming in Phase N" message.

---

## Alternatives considered and rejected

**Independent React apps with a reverse proxy** — rejected because it requires separate build pipelines, a proxy routing layer, and duplicated auth logic in every app. Cross-app state sharing (user object, notifications) is also significantly harder.

**Next.js app router with route groups** — rejected per ADR-001 (the full-stack Next.js option was already ruled out). The app router's layout system would handle this pattern well, but the decision to use React + FastAPI is already fixed.

---

## Review notes

This decision should be revisited if:

- A registered application grows large enough that bundling it with the shell causes meaningful performance problems. At that point, a micro-frontend approach (Module Federation) could be applied to that specific app without changing the registry pattern.
- The number of registered apps grows beyond ten, at which point a database-driven registry and dynamic routing might be worth the complexity.

Neither condition is expected within the five-phase programme scope.

---

*ADR-004 — accepted — no further review required unless the conditions above are met.*
