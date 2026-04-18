---
name: saga-orchestration
description: Coordinate distributed transactions across services with compensating actions for partial-failure recovery. Use when building workflows that span multiple services, implementing order fulfillment or payment pipelines, handling rollbacks across service boundaries, or managing any long-running business process — even if the user just says "I need to coordinate multiple services" or "what happens if one step fails."
---

# Saga Orchestration

Coordinate a sequence of local transactions across services so that if any step fails, previously completed steps are compensated — keeping the system consistent without distributed 2PC.

## Decision guide

| Question                             | Choose                                | Why                                              |
| ------------------------------------ | ------------------------------------- | ------------------------------------------------ |
| 2–3 steps, autonomous teams?         | Choreography                          | No central coordinator — lowest coupling         |
| 4+ steps or strict ordering?         | Orchestration                         | Centralized flow is easier to reason about       |
| Need a visible audit trail?          | Orchestration                         | Orchestrator state is the audit log              |
| Flow spans days / needs human steps? | Orchestration + durable scheduler     | Timeouts and replay are non-negotiable           |
| Flow must be parallel / DAG-shaped?  | Workflow engine (Temporal, Cadence)   | Hand-rolled sagas are linear by design           |

## Core concepts

```text
Choreography                    Orchestration
Svc A ─event─► Svc B ─event─►   Orchestrator ──cmd──► Svc 1
                                     │       ◄─ack── Svc 2
                                     └────── cmd ──► Svc 3
```

**Saga states:** `STARTED` → `PENDING` → (`COMPLETED` | `COMPENSATING` → `FAILED`). Compensation runs completed steps in reverse order, sequentially.

## Patterns

### Orchestration

A central orchestrator persists saga state, dispatches each step as a command, and advances on ack. On failure it walks completed steps backwards, publishing each step's compensation command one at a time. Full implementation with base class, concrete saga, and participant handler in `references/orchestration-pattern.md`.

### Choreography

No coordinator. Each service subscribes to events it cares about and publishes the next event when done. Compensation paths are coded explicitly — `PaymentFailed` → `ReleaseInventory`, etc. Context (reservation IDs, payment IDs) must be carried forward in every event. See `references/choreography-pattern.md`.

### Timeouts and recovery

Production sagas need per-step deadlines, replay on orchestrator restart, and a dead-letter path when compensation itself fails. See `references/timeouts-and-recovery.md`.

## Best practices

- **Make every step idempotent.** Use `saga_id + step_name` as the dedupe key — at-least-once delivery guarantees duplicates.
- **Persist saga state before publishing commands.** A crash between save and publish is recoverable; the reverse leaves orphaned side effects.
- **Test the compensation path.** It is the part you will run rarely and need urgently — chaos-test each step's failure.
- **Snapshot time-sensitive data.** If compensating a price, store the original price in the step result; don't recompute it later.
- **Delay irreversible side effects.** Emails, SMS, webhooks — stage them until the saga commits, or design them as advisory.
- **Propagate correlation IDs.** `saga_id` in every command, event, and log line — non-negotiable for debugging.

## Common pitfalls

| Pitfall                            | Fix                                                               |
| ---------------------------------- | ----------------------------------------------------------------- |
| Non-idempotent compensation        | Make compensations safe to run N times — dedupe by saga_id+step   |
| No timeout on a step               | Every step needs a deadline plus a scheduler firing the timeout   |
| Compensation fires on 4xx retry    | Only compensate on business failure; retry network errors first   |
| Hidden cycle in choreography       | Draw the event DAG; verify no service's event triggers its own    |
| Silent compensation failure        | Route to DLQ + `NEEDS_INTERVENTION` state — never swallow         |
| Orchestrator crash loses in-flight | Resume from store on boot; `find_by_state(non_terminal)`          |
| Side effects before saga commits   | Stage email/webhook sends; commit them only when saga completes   |

## References — load on demand

| File                                     | Load when                                                         |
| ---------------------------------------- | ----------------------------------------------------------------- |
| `references/orchestration-pattern.md`    | building an orchestrator, writing the base class, wiring participant handlers, sequential compensation |
| `references/choreography-pattern.md`     | event-driven flow, no central coordinator, compensation events    |
| `references/timeouts-and-recovery.md`    | per-step timeouts, replay on restart, DLQ for failed compensation, monitoring signals |
| `references/saga-decisions.md`           | choreography-vs-orchestration matrix, compensation pitfalls, testing strategies |

## Related skills

- `microservices-patterns` — service architecture, communication patterns, outbox for reliable event publishing
- `api-design-principles` — designing the endpoints saga participants expose
- `error-handling-patterns` — retry, backoff, and failure classification inside each step
- `logging-standards` — structured logs that stay traceable across the saga

## Resources

- [Saga Pattern — microservices.io](https://microservices.io/patterns/data/saga.html)
- [Designing Data-Intensive Applications](https://dataintensive.net/)
