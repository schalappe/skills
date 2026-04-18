---
name: api-design-principles
description: Guides the design of REST and GraphQL APIs including resource modeling, pagination, error handling, authentication, webhooks, and async patterns. Use when designing endpoints, structuring routes, shaping request/response schemas, choosing REST vs GraphQL, implementing pagination or filtering, planning versioning, adding authentication, designing webhooks or async APIs, or reviewing an API specification — even if the user doesn't explicitly say "API design."
---

# API Design Principles

Design intuitive, scalable REST and GraphQL APIs using resource-oriented patterns, proper HTTP semantics, consistent error handling, and secure authentication.

## Quick start

REST resource shape — nouns, plural, method-driven:

```text
GET    /api/users          # List (paginated)
POST   /api/users          # Create
GET    /api/users/{id}     # Read
PATCH  /api/users/{id}     # Partial update
DELETE /api/users/{id}     # Remove
```

GraphQL mutation shape — Input/Payload pattern:

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
}
```

## Core concepts

- **REST**: resources are nouns, HTTP methods drive actions, URLs model hierarchies, responses stateless.
- **GraphQL**: schema-first; queries, mutations, subscriptions over a single endpoint; strongly typed; clients request exactly what they need.
- **Versioning**: URL (`/v1/`), header (`Accept: ...; version=1`), or query (`?version=1`). Pick one and commit.

## Decision guide

| Need | Pattern |
|------|---------|
| CRUD over discrete resources | REST |
| Complex graph traversal, many clients | GraphQL |
| Fire-and-forget event delivery | Webhooks |
| Long-running jobs | Async (202 Accepted + polling or callback) |
| Bandwidth-sensitive clients | GraphQL or REST sparse fieldsets |

## Patterns at a glance

- **Collection design**: plural nouns, shallow nesting (max 2 levels), consistent casing.
- **Pagination**: offset for simple; cursor for large/real-time. Enforce default and max page size.
- **Errors**: structured JSON with `code`, `message`, `details`, `path`, `timestamp`. See `references/rest-best-practices.md`.
- **Status codes**: 2xx success, 4xx client, 5xx server. Use 401 vs 403 correctly; 422 for validation.
- **HATEOAS**: embed `_links` for discoverability. See `references/rest-best-practices.md`.
- **Authentication**: Bearer tokens (JWT) or API keys; enforce object-level auth. See `references/auth-and-security.md`.
- **Webhooks & async**: signed deliveries, idempotent receivers, exponential retry, 202 Accepted for long jobs. See `references/webhooks-and-async.md`.

## Best practices

- **REST**: plural nouns, stateless, correct status codes, versioned, paginated, rate-limited, OpenAPI-documented.
- **GraphQL**: schema-first, DataLoader for every relationship, Input/Payload for mutations, cursor pagination (Relay), `@deprecated` for evolution.
- **Security**: validate at boundaries, enforce object-level authorization, HTTPS only, no secrets in URLs, rate-limit per principal, rotate keys.

## Common pitfalls

- Action-oriented URLs (`/createUser`) — use resources instead.
- Inconsistent error formats across endpoints.
- Missing rate limits → abuse vector.
- N+1 queries in GraphQL without DataLoader.
- Breaking changes without versioning or deprecation.
- Mirroring DB schema in API → tight coupling.
- Webhook receivers that aren't idempotent → duplicated side effects on retry.
- Authorization checked at controller but not object level (IDOR).

## Resources

- `references/rest-best-practices.md` — URLs, pagination, error format, caching, bulk operations
- `references/graphql-schema-design.md` — schemas, resolvers, DataLoader, error unions
- `references/auth-and-security.md` — OAuth2/JWT, API keys, RBAC, OWASP API Top 10
- `references/webhooks-and-async.md` — webhook signing, 202 Accepted, idempotency, retries
- `assets/rest-api-template.py` — FastAPI template with auth, pagination, middleware
- `assets/api-design-checklist.md` — pre-implementation review checklist

## Related skills

- **microservices-patterns**: service decomposition, inter-service communication, resilience
- **saga-orchestration**: distributed transactions with compensating actions
