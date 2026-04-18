# Timeouts and Recovery

Real sagas run for seconds to days. Participants crash, networks partition, compensations themselves fail. This reference covers the operational pieces — timeouts, replay, and terminal failure handling — that turn a toy orchestrator into a production one.

## Timeouts per step

Extends the base orchestrator (see `orchestration-pattern.md`). Each step gets a deadline; a scheduler callback fails the step if no ack arrives in time.

```python
from datetime import datetime, timedelta, timezone

class TimeoutSagaOrchestrator(SagaOrchestrator):
    def __init__(self, saga_store, event_publisher, scheduler):
        super().__init__(saga_store, event_publisher)
        self.scheduler = scheduler

    async def _execute_next_step(self, saga: Saga):
        if saga.current_step >= len(saga.steps):
            return
        step = saga.steps[saga.current_step]
        step.status = "executing"
        step.timeout_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await self.saga_store.save(saga)

        await self.scheduler.schedule(
            f"saga_timeout_{saga.saga_id}_{step.name}",
            self._check_timeout,
            {"saga_id": saga.saga_id, "step_name": step.name},
            run_at=step.timeout_at,
        )
        await self.event_publisher.publish(
            step.action,
            {"saga_id": saga.saga_id, "step_name": step.name, **saga.data},
        )

    async def _check_timeout(self, data: Dict):
        saga = await self.saga_store.get(data["saga_id"])
        step = next(s for s in saga.steps if s.name == data["step_name"])
        if step.status == "executing":
            await self.handle_step_failed(
                data["saga_id"],
                data["step_name"],
                "Step timed out",
            )
```

### Choosing a timeout

| Step type                      | Typical budget  |
| ------------------------------ | --------------- |
| In-memory computation          | 100 ms – 1 s    |
| Internal service RPC           | 1 s – 10 s      |
| Payment gateway / third party  | 10 s – 60 s     |
| Human approval / manual review | hours – days    |

Set the budget to the 99th-percentile latency plus headroom. A timeout shorter than p99 guarantees false failures at peak load.

### Cancel the scheduled timeout on success

In `handle_step_completed`, cancel the outstanding timeout before advancing — otherwise a slow completion plus a slow timer can race and fail an already-done step.

```python
await self.scheduler.cancel(f"saga_timeout_{saga.saga_id}_{step_name}")
```

## Replay on restart

The orchestrator must be restartable without losing in-flight sagas. On boot, scan the store for sagas in non-terminal states and resume them:

```python
async def resume_in_flight(self):
    for saga in await self.saga_store.find_by_state(
        [SagaState.STARTED, SagaState.PENDING, SagaState.COMPENSATING]
    ):
        if saga.state == SagaState.COMPENSATING:
            await self._compensate(saga)
        else:
            await self._execute_next_step(saga)
```

Steps must be idempotent because replay will re-publish commands that the participant may already have processed. Use `saga_id + step_name` as the dedupe key.

## When compensation fails

Compensation must succeed — but it can't always. Strategies in order of preference:

1. **Retry with backoff.** Most failures (network blips, transient 5xx) resolve on retry. Cap attempts (3–5) before escalating.
2. **Dead-letter queue.** After retry exhaustion, park the failed compensation on a DLQ and transition the saga to a distinct `NEEDS_INTERVENTION` state — do *not* mark it `FAILED`, because side effects remain uncompensated.
3. **Human intervention.** Expose the DLQ via an admin UI with the saga ID, the failed step, the original payload, and the error. Operators replay or resolve manually.
4. **Forward recovery.** For a minority of cases (e.g. confirmation email failed to send), the correct response is to accept and move forward, not roll back. Mark the step `skipped` and continue.

Never silently swallow a compensation failure — that leaves the system in an inconsistent state that no automated process will ever detect.

## Monitoring signals

| Metric                              | Alert when                                   |
| ----------------------------------- | -------------------------------------------- |
| Saga duration p95 per `saga_type`   | Exceeds expected SLA by 2×                   |
| Compensation rate                   | Spikes above baseline — indicates a failing downstream |
| Sagas in `NEEDS_INTERVENTION`       | Any sustained count > 0                      |
| Orchestrator restart count          | > 1/hour — instability in the orchestrator itself |
| Scheduled timeouts firing           | High absolute count — timeouts set too tight or downstream degraded |
