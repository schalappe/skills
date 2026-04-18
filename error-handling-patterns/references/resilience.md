# Resilience Patterns

Cross-cutting patterns for transient failures and graceful fallback. Pick the flavor that matches the target stack.

## Retry with exponential backoff

Retry only idempotent operations or well-known transient failures (network errors, 5xx, 429). Cap attempts, multiply delay, and add jitter to avoid synchronized retry storms.

### Python

```python
import random
import time
from functools import wraps
from typing import Callable, Tuple, Type, TypeVar

T = TypeVar("T")

def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] | None = None,
):
    """Exponential backoff with jitter. Re-raises the last exception on exhaustion."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last = e
                    if on_retry:
                        on_retry(e, attempt + 1)
                    if attempt < max_attempts - 1:
                        delay = backoff_factor ** attempt
                        jitter = random.uniform(0, delay * 0.5)
                        time.sleep(delay + jitter)
            assert last is not None
            raise last
        return wrapper
    return decorator
```

### TypeScript

```typescript
export async function retry<T>(
  fn: () => Promise<T>,
  opts: { maxAttempts?: number; backoffMs?: number; factor?: number } = {},
): Promise<T> {
  const { maxAttempts = 3, backoffMs = 200, factor = 2 } = opts;
  let last: unknown;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      last = err;
      if (attempt < maxAttempts - 1) {
        const delay = backoffMs * factor ** attempt;
        const jitter = Math.random() * delay * 0.5;
        await new Promise((r) => setTimeout(r, delay + jitter));
      }
    }
  }
  throw last;
}
```

## Circuit breaker

Three states — **CLOSED** (normal), **OPEN** (short-circuit), **HALF_OPEN** (probe). Break on N consecutive failures, wait a recovery timeout, allow a single probe call, close again on success.

```python
from enum import Enum
from time import monotonic

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at: float | None = None

    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self.opened_at and monotonic() - self.opened_at >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("circuit is open")
        try:
            result = func(*args, **kwargs)
        except Exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def _on_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = monotonic()
```

## Error aggregation

Validate every field before raising so the caller sees every problem at once instead of one per round-trip.

```typescript
export class AggregateValidationError extends Error {
  constructor(public readonly errors: Error[]) {
    super(`${errors.length} validation error(s)`);
  }
}

class ErrorCollector {
  private errors: Error[] = [];
  add(err: Error) { this.errors.push(err); }
  hasErrors() { return this.errors.length > 0; }
  throwIfAny(): void {
    if (this.errors.length) throw new AggregateValidationError(this.errors);
  }
}

export function validateUser(data: Record<string, unknown>): User {
  const errs = new ErrorCollector();
  if (!data.email)                  errs.add(new Error("email required"));
  if (!data.name)                   errs.add(new Error("name required"));
  if (typeof data.age !== "number") errs.add(new Error("age must be a number"));
  errs.throwIfAny();
  return data as User;
}
```

## Graceful degradation

When the preferred path fails, serve a reduced but useful response. Log the fallback so silent degradation stays visible in dashboards.

```python
def with_fallback(primary, fallback, *, logger=None):
    try:
        return primary()
    except Exception as e:
        if logger is not None:
            logger.warning("primary failed; falling back: %s", e)
        return fallback()

def get_user_profile(user_id: str):
    return with_fallback(
        primary=lambda: fetch_from_cache(user_id),
        fallback=lambda: fetch_from_database(user_id),
    )
```

## Combining patterns

A robust external call stacks these in order: **timeout → retry → circuit breaker → fallback**. Tune each to the dependency's SLA, not a global default — a 200 ms database and a 30 s third-party API need different retry budgets.
