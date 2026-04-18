# Resilience Patterns

Patterns for handling partial failures in distributed systems. The goal is to prevent a single failing dependency from taking down the entire system.

---

## Circuit Breaker

Tracks failures to a downstream service. After a threshold of consecutive failures, the circuit "opens" and calls fail immediately without attempting the request. After a recovery timeout, it enters a "half-open" state and allows a few test requests through.

**States:**

- **Closed** — Normal operation. Failures are counted.
- **Open** — Failing fast. No requests are sent to the downstream service.
- **Half-Open** — Testing recovery. A limited number of requests go through. If they succeed, the circuit closes. If they fail, it reopens.

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker for service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker."""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try again."""
        return (
            datetime.now() - self.opened_at
            > timedelta(seconds=self.recovery_timeout)
        )

# Usage
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

async def call_payment_service(payment_data: dict):
    return await breaker.call(
        payment_client.process_payment,
        payment_data
    )
```

---

## Timeouts

A remote call with no timeout is a resource leak waiting to happen. When the downstream hangs, every caller thread/connection blocks until the OS eventually tears it down — typically minutes. By that time the upstream is overloaded and the failure has cascaded.

**Always set two timeouts on an HTTP client:**

- **Connect timeout** — max time to open the TCP/TLS connection. 1–3 seconds is usually enough.
- **Read timeout** — max time to wait for bytes after the connection is open. Tune to the downstream's p99 latency × 2.

```python
import httpx

client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=2.0,   # fail fast if we can't dial in
        read=5.0,      # fail if no bytes for 5s
        write=5.0,
        pool=1.0,      # wait at most 1s for a free connection from the pool
    )
)
```

**Per-request override** when a specific call needs different limits:

```python
await client.post("/slow-report", json=data, timeout=30.0)
```

**gRPC** has no default deadline — you must set one on every call:

```python
stub.GetOrder(GetOrderRequest(order_id="42"), timeout=2.0)
```

**Key considerations:**

- A timeout shorter than the downstream's p99 will generate spurious failures. Measure before tuning.
- The total end-to-end budget is the **sum** of timeouts along the call chain — don't let a chain of 5s timeouts turn a 2s user expectation into a 25s hang.
- Combine with retries: total budget = `attempts × (connect + read)`. A 3-retry, 5s-timeout client can block for 15s.

---

## Retry with Exponential Backoff

Retries transient failures with increasing delays between attempts. Prevents overwhelming a struggling service with immediate retries.

**Strategy:** Wait `multiplier * 2^(attempt - 1)` seconds between retries, capped at a maximum delay.

| Attempt | Wait (multiplier=1) |
|---------|---------------------|
| 1       | 1s                  |
| 2       | 2s                  |
| 3       | 4s                  |
| 4       | 8s (capped at max)  |

```python
import asyncio
import random
from functools import wraps
from typing import Callable

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,)
):
    """Decorator for retry with exponential backoff and optional jitter."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        break

                    delay = min(base_delay * (2 ** attempt), max_delay)
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper
    return decorator

# Usage
@retry_with_backoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=(httpx.TimeoutException, httpx.HTTPStatusError)
)
async def fetch_order(order_id: str):
    response = await client.get(f"/orders/{order_id}")
    response.raise_for_status()
    return response.json()
```

**Using tenacity (library):**

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def call_service(path: str):
    response = await client.get(path)
    response.raise_for_status()
    return response.json()
```

**Key considerations:**

- Add jitter (randomized delay) to prevent thundering herd when multiple clients retry simultaneously
- Only retry on transient errors (timeouts, 503) — never on 4xx client errors
- Set a maximum number of retries to avoid infinite loops
- Log each retry attempt for observability

---

## Bulkhead

Isolates resources per downstream dependency so that a failure in one dependency does not exhaust resources shared by others. Named after ship bulkheads that contain flooding to one compartment.

**Example:** If Service A calls both Service B and Service C, a semaphore limits concurrent calls to each. If Service B hangs, only its semaphore fills up — calls to Service C continue normally.

```python
import asyncio
from typing import Callable, Any

class Bulkhead:
    """Limits concurrent calls to a downstream service."""

    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function within bulkhead limits."""
        try:
            await asyncio.wait_for(
                self.semaphore.acquire(),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            raise BulkheadFullError(
                f"Bulkhead '{self.name}' is full ({self.max_concurrent} concurrent calls)"
            )

        try:
            return await func(*args, **kwargs)
        finally:
            self.semaphore.release()

# Usage — one bulkhead per downstream service
payment_bulkhead = Bulkhead("payment-service", max_concurrent=20)
inventory_bulkhead = Bulkhead("inventory-service", max_concurrent=15)

async def get_payment_status(order_id: str):
    return await payment_bulkhead.call(
        payment_client.get, f"/payments/order/{order_id}"
    )

async def check_inventory(product_id: str):
    return await inventory_bulkhead.call(
        inventory_client.get, f"/inventory/{product_id}"
    )
```

**Key considerations:**

- Size each bulkhead based on the downstream service's capacity
- Combine with circuit breakers — the bulkhead limits concurrency, the circuit breaker detects sustained failures
- Use `asyncio.wait_for` with a timeout on semaphore acquisition to fail fast when the bulkhead is full
- Monitor bulkhead utilization to tune limits over time

---

## Idempotency Keys

Retries (network-level, library-level, or user-triggered) mean any write can be attempted more than once. Without protection, a duplicate `POST /payments` charges the customer twice.

**Pattern:** the client generates a unique **idempotency key** per logical operation and sends it as a header. The server records `(key, response)` on first success; subsequent requests with the same key return the stored response without re-executing.

```python
import hashlib
from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI()

@app.post("/payments")
async def create_payment(
    request: Request,
    payment: PaymentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    body_hash = hashlib.sha256(await request.body()).hexdigest()

    stored = await idempotency_store.get(idempotency_key)
    if stored:
        # Guard against key reuse with a different body
        if stored["body_hash"] != body_hash:
            raise HTTPException(status_code=422, detail="Idempotency key reused with different body")
        return stored["response"]

    # First-time execution
    result = await payment_service.charge(payment)
    await idempotency_store.put(
        idempotency_key,
        {"body_hash": body_hash, "response": result},
        ttl_seconds=24 * 3600,
    )
    return result
```

**Key considerations:**

- **Scope keys per endpoint or per user** — two different operations should never share a key.
- **Store the request hash alongside the response** so you can reject reuse with a different body (422, not 200).
- **TTL the store** — 24 hours is typical. Infinite retention wastes storage.
- **Atomic first-write** — use `INSERT ... ON CONFLICT DO NOTHING` (Postgres) or `SETNX` (Redis) so concurrent first attempts don't both execute.
- For event consumers, the equivalent is **deduplication on `event_id`** — maintain a "processed events" set and skip duplicates.

---

## Health Check

Exposes endpoints that load balancers and orchestrators use to determine if a service instance is alive and ready to serve traffic.

**Two types:**

- **Liveness** (`/health/live`): Is the process running? Returns 200 if the service is up, regardless of dependency status. Used by orchestrators to decide whether to restart the container.
- **Readiness** (`/health/ready`): Can the service handle requests? Checks dependencies (database, cache, downstream services). Used by load balancers to decide whether to route traffic.

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/health/live")
async def liveness():
    """Always returns 200 if the process is running."""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness(response: Response):
    """Checks all critical dependencies before reporting ready."""
    checks = {}

    # Check database connection
    try:
        await db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "failed"

    # Check cache connection
    try:
        await redis.ping()
        checks["cache"] = "ok"
    except Exception:
        checks["cache"] = "failed"

    all_healthy = all(v == "ok" for v in checks.values())

    if not all_healthy:
        response.status_code = 503

    return {"status": "ready" if all_healthy else "degraded", "checks": checks}
```

**Key considerations:**

- Keep liveness checks cheap — they run frequently and should never depend on external services
- Readiness checks should verify dependencies but avoid expensive operations
- Return structured responses so monitoring tools can identify which dependency is failing
- In Kubernetes, map liveness to `livenessProbe` and readiness to `readinessProbe`
