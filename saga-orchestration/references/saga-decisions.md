# Saga Decisions

## Choreography vs Orchestration Decision Matrix

| Factor | Choreography | Orchestration |
|--------|-------------|---------------|
| Coupling | Loose -- services only know about events | Tighter -- orchestrator knows all steps |
| Complexity | Grows with number of services (hard to trace) | Centralized (easier to understand flow) |
| Single point of failure | None | The orchestrator |
| Best for | Simple flows (2-3 steps), highly autonomous teams | Complex flows (4+ steps), strict ordering needs |
| Testing | Integration tests per service | Test the orchestrator + mock services |
| Monitoring | Distributed tracing required | Orchestrator provides natural audit log |

## Common Compensation Pitfalls

1. **Non-idempotent compensations** -- compensations may run more than once (network retries, duplicate events). Every compensation must be idempotent.
2. **Ordering assumptions** -- releasing inventory before confirming refund can create race conditions. Design compensations to be order-independent when possible, or enforce ordering explicitly.
3. **Partial compensation** -- if compensation itself fails, you need a strategy (retry queue, manual intervention, dead letter queue).
4. **Time-dependent data** -- compensating a price change after rates have moved requires snapshotting the original state.
5. **Side effects that can't be undone** -- emails sent, SMS delivered, webhooks fired. Use "pending" states and delay irreversible actions until the saga completes.

## Testing Strategies for Sagas

1. **Unit test each step's action and compensation independently** -- verify that each step produces the expected output and that its compensation reverses the effect.
2. **Test the orchestrator with mock services** -- verify step ordering and compensation triggering without real service dependencies.
3. **Chaos testing** -- inject failures at each step and verify compensation runs correctly for all preceding completed steps.
4. **Timeout testing** -- verify behavior when a step never responds, ensuring the saga transitions to compensating state.
5. **Idempotency testing** -- send duplicate completion/failure events and verify no double-processing occurs.
