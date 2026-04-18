---
name: microservices-patterns
description: Design and evolve service-oriented systems — decomposition, inter-service communication, data isolation, resilience, and observability. Use when splitting an application into services, decomposing a monolith, choosing sync vs async communication, implementing an API gateway or service mesh, handling distributed failures, designing event-driven flows, or working with service discovery — even if the user just says their app is "getting too big" or asks how to "handle failures between services."
---

# Microservices Patterns

Apply service-oriented patterns for decomposition, communication, data ownership, resilience, and observability in distributed systems.

## Decision guide

| Question                        | Choose                                  | Why                                         |
| ------------------------------- | --------------------------------------- | ------------------------------------------- |
| Start with monolith or services? | Monolith first, extract later          | Boundaries are hard to guess up front       |
| Sync or async call?              | Sync for queries, async for commands   | Match temporal coupling to caller need      |
| One DB for all services?         | No — DB per service                    | Shared DB is the #1 source of coupling      |
| Coordinate a multi-service txn?  | Saga (see `saga-orchestration` skill)  | Distributed 2PC is rarely worth the cost    |
| Cross-cutting resilience?        | Service mesh if on K8s, library otherwise | Mesh moves retries/mTLS out of app code  |

## Core patterns

Sketches below — full code lives in the references.

### Service decomposition

Align service boundaries with **business capabilities** or **DDD bounded contexts**. Extract from a monolith with the **strangler fig pattern** — proxy routes to old/new systems and migrate one capability at a time. See `references/decomposition.md`.

### API gateway and BFF

Single entry point that routes, aggregates, and applies cross-cutting policy (auth, rate limits, CORS). **Backend for Frontend (BFF)** is one gateway per client type (web, mobile, partner) so each stays tailored. See `references/decomposition.md`.

### Communication: sync vs async

- **Sync (REST, gRPC)** — caller blocks until response. Simple, but temporal coupling means a downstream outage blocks callers.
- **Async (events, queues)** — fire-and-forget via Kafka / RabbitMQ / SQS. Decouples in time, enables independent scaling.

Use gRPC for internal high-throughput calls, REST for public APIs, events for commands and notifications. See `references/communication-patterns.md`.

### Data ownership

Each service owns its database. No cross-service SQL joins. Replicate read models via events when another service needs the data. Publish events reliably with the **outbox pattern** — write the event to an outbox table in the same transaction as the business change, then a relay ships it to the broker. See `references/data-management.md`.

### Resilience

- **Timeout** on every remote call — missing timeouts are the top cause of cascade failures.
- **Retry with backoff + jitter** for transient failures only (5xx, timeouts — never 4xx).
- **Circuit breaker** to fail fast when a dependency is sustained-unhealthy.
- **Bulkhead** to isolate resource pools per downstream.
- **Idempotency keys** so retries don't duplicate side effects.

See `references/resilience-patterns.md`.

### Observability

Emit a **correlation ID** per request and propagate it through every hop (HTTP header, event metadata). Use OpenTelemetry for **distributed tracing** across services. Expose **liveness** (`/health/live`) and **readiness** (`/health/ready`) probes for orchestrators. Combine with **service discovery** (Kubernetes DNS, Consul, Eureka) so clients find healthy instances dynamically. See `references/observability.md`.

## Best practices

- **Start with a modular monolith** — only split when team or scaling pain is real.
- **One team per service** — Conway's law works with you or against you.
- **Contract-first APIs** — OpenAPI / Protobuf / AsyncAPI; version from day one.
- **Events as immutable facts** — include all data a consumer needs, not IDs to call back.
- **Idempotent consumers** — at-least-once delivery means duplicates will happen.
- **Automated pipelines** — per-service CI/CD, independent deploys.
- **Observability before scaling** — traces, metrics, logs, SLOs before adding services.

## Common pitfalls

| Pitfall                    | Fix                                                     |
| -------------------------- | ------------------------------------------------------- |
| Distributed monolith       | Services sync-call each other in long chains — use events instead |
| Shared database            | Replicate read models via events; keep writes isolated  |
| Chatty services            | Aggregate at the gateway, or merge services that co-change |
| No timeout on remote call  | Set explicit connect + read timeouts on every client    |
| Synchronous everywhere     | Use events for commands that don't need an immediate answer |
| No compensation logic      | Pair writes with a saga or outbox for reversibility     |
| Premature microservices    | Start as a modular monolith; extract on real evidence   |
| Ignoring network failures  | Assume every remote call can fail, hang, or duplicate   |

## References — load on demand

| File                                   | Load when                                                    |
| -------------------------------------- | ------------------------------------------------------------ |
| `references/decomposition.md`          | splitting a monolith, designing boundaries, API gateway, BFF, service mesh, sidecar |
| `references/communication-patterns.md` | choosing REST vs gRPC vs events, Kafka publish/consume, idempotent consumers, DLQ |
| `references/data-management.md`        | DB-per-service, outbox pattern, CQRS, event sourcing, read replicas |
| `references/resilience-patterns.md`    | circuit breaker, retry/backoff, bulkhead, timeouts, idempotency keys, health checks |
| `references/observability.md`          | distributed tracing, correlation IDs, service discovery, metrics, logging |

## Related skills

- `api-design-principles` — REST / GraphQL contract design for service APIs
- `saga-orchestration` — distributed transactions with compensating actions
- `error-handling-patterns` — exception shaping and retry/backoff/fallback internals
- `logging-standards` — structured logs that stay traceable across services
