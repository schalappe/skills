# Webhooks & Async API Patterns

Patterns for server-initiated events (webhooks) and server-side long-running work (async APIs).

## When to Use Which

| Pattern | Use when |
|---------|----------|
| Synchronous (200 OK with body) | Operation completes in <1s; caller blocks for result |
| Async with polling (202 Accepted) | Long-running job; caller controls check frequency |
| Async with callback webhook | Long-running job; caller registers a URL for result |
| Webhook subscription | Event stream: state changes, business events |
| Server-Sent Events (SSE) | One-way server → client stream over HTTP |
| WebSockets | Bi-directional real-time (chat, collaboration) |

## Async API Pattern (202 Accepted)

Client submits work; server returns a handle; client polls for status.

### Request / Response Shape

```http
POST /api/reports
Content-Type: application/json

{ "type": "sales", "range": "2026-Q1" }
```

```http
HTTP/1.1 202 Accepted
Location: /api/jobs/job_abc123
Content-Type: application/json

{
  "job_id": "job_abc123",
  "status": "pending",
  "created_at": "2026-04-18T10:00:00Z",
  "status_url": "/api/jobs/job_abc123"
}
```

### Polling for Status

```http
GET /api/jobs/job_abc123

200 OK
{
  "job_id": "job_abc123",
  "status": "processing",           # pending | processing | completed | failed
  "progress": 0.42,                 # optional
  "created_at": "...",
  "updated_at": "...",
  "result_url": null,               # populated when completed
  "error": null                     # populated when failed
}
```

When complete:

```json
{
  "status": "completed",
  "result_url": "/api/reports/rep_xyz789"
}
```

### Polling Etiquette

- Return `Retry-After` header with suggested interval.
- Use ETags; return `304 Not Modified` when status unchanged.
- Consider exponential backoff on client side.

```python
@app.post("/api/reports", status_code=202)
async def create_report(req: ReportRequest, response: Response):
    job = await jobs.create(type=req.type, params=req.dict())
    response.headers["Location"] = f"/api/jobs/{job.id}"
    return {
        "job_id": job.id,
        "status": "pending",
        "status_url": f"/api/jobs/{job.id}",
    }

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, response: Response):
    job = await jobs.get(job_id)
    if job.status in ("pending", "processing"):
        response.headers["Retry-After"] = "5"
    return job
```

## Webhook Design

Server calls back client URL when events happen.

### Subscription Model

```http
POST /api/webhooks
{
  "url": "https://client.example.com/hooks/orders",
  "events": ["order.created", "order.shipped", "order.refunded"],
  "secret": "whsec_..."   # client-generated or server-generated
}

201 Created
{
  "id": "wh_abc123",
  "url": "https://client.example.com/hooks/orders",
  "events": [...],
  "created_at": "..."
}
```

### Event Delivery Shape

```http
POST https://client.example.com/hooks/orders
Content-Type: application/json
User-Agent: Example-Webhooks/1.0
X-Webhook-Id: evt_xyz789
X-Webhook-Event: order.shipped
X-Webhook-Timestamp: 1713456789
X-Webhook-Signature: sha256=3b4f...

{
  "id": "evt_xyz789",
  "type": "order.shipped",
  "created_at": "2026-04-18T10:00:00Z",
  "data": {
    "order_id": "ord_123",
    "tracking_number": "1Z999..."
  }
}
```

### Signing (HMAC)

Signs payload so receiver can verify authenticity and integrity.

```python
import hmac, hashlib, time

def sign_payload(secret: str, payload: bytes, timestamp: int) -> str:
    signed = f"{timestamp}.".encode() + payload
    return "sha256=" + hmac.new(
        secret.encode(), signed, hashlib.sha256
    ).hexdigest()
```

**Receiver verification:**

```python
def verify_webhook(secret: str, request) -> bool:
    timestamp = int(request.headers["X-Webhook-Timestamp"])
    if abs(time.time() - timestamp) > 300:   # reject if older than 5 min
        return False

    expected = sign_payload(secret, request.body, timestamp)
    signature = request.headers["X-Webhook-Signature"]
    return hmac.compare_digest(expected, signature)   # timing-safe
```

Include timestamp in signed content to prevent replay attacks.

### Retry Policy

Webhook receivers WILL fail. Retries are expected.

- Retry on: non-2xx response, connection timeout, connection refused.
- Don't retry on: 2xx responses, permanent errors (410 Gone).
- Backoff: exponential with jitter.
- Example schedule: 1m, 5m, 30m, 2h, 6h, 12h, 24h (give up after ~24h).
- Record delivery attempts; expose to client via `GET /api/webhooks/{id}/deliveries`.

```python
BACKOFF_SCHEDULE = [60, 300, 1800, 7200, 21600, 43200, 86400]

async def deliver_with_retry(webhook, event):
    for attempt, delay in enumerate([0] + BACKOFF_SCHEDULE):
        if delay:
            await asyncio.sleep(delay)
        try:
            response = await http.post(webhook.url, json=event, timeout=10)
            if 200 <= response.status_code < 300:
                return
        except (httpx.TimeoutException, httpx.ConnectError):
            continue
    await mark_failed(webhook.id, event.id)
```

## Idempotency

Critical for both async and webhook patterns — retries will happen.

### Idempotency Keys (Client-Supplied)

Client sends a unique key; server returns cached response for duplicates.

```http
POST /api/orders
Idempotency-Key: a7f3e8c2-4b1d-4e2f-9c3d-5f6a7b8c9d0e

# First request → 201 Created, response stored keyed by idempotency key
# Duplicate request → same response returned, no duplicate order created
```

```python
async def with_idempotency(key: str, func, *args, ttl: int = 86400):
    cached = await redis.get(f"idem:{key}")
    if cached:
        return json.loads(cached)
    result = await func(*args)
    await redis.set(f"idem:{key}", json.dumps(result), ex=ttl)
    return result
```

- Keys scoped per endpoint + user; 24–48h TTL typical.
- Hash the request body and store with the key — if key reused with different body, return `422`.

### Idempotent Webhook Receivers

Receivers must deduplicate on `X-Webhook-Id`.

```python
@app.post("/hooks/orders")
async def handle_webhook(request: Request):
    event_id = request.headers["X-Webhook-Id"]

    if await redis.set(f"seen:{event_id}", "1", ex=86400, nx=True) is None:
        return {"status": "duplicate"}   # already processed

    event = await request.json()
    await process_event(event)
    return {"status": "ok"}
```

Use `SET NX` (set-if-not-exists) for atomicity. Return 200 on duplicate — don't error.

## Event Naming Conventions

- **Format**: `resource.action` (past tense) — `order.created`, `user.updated`, `payment.refunded`.
- Keep events at business-level, not CRUD-level when possible (`order.shipped` > `order.updated`).
- Version events at the type level: `order.created.v2` or in payload `"schema_version": 2`.

## Event Payload Design

Two patterns:

### Thin (Reference) Events

Event contains just IDs; receiver calls API for details.

```json
{ "type": "order.created", "data": { "order_id": "ord_123" } }
```

Pros: small, always fresh. Cons: extra fetch required, auth needed for fetch.

### Fat (Snapshot) Events

Event includes full resource state at the time.

```json
{
  "type": "order.created",
  "data": {
    "order_id": "ord_123",
    "user_id": "usr_456",
    "total": 9900,
    "items": [...]
  }
}
```

Pros: receiver can act without callback. Cons: larger payloads, data may be stale if processed late.

Fat events fit better when receivers are external systems that shouldn't callback.

## Server-Sent Events (SSE)

Simpler than WebSockets for one-way streams.

```python
from sse_starlette.sse import EventSourceResponse

@app.get("/api/jobs/{job_id}/stream")
async def job_stream(job_id: str):
    async def events():
        while True:
            job = await jobs.get(job_id)
            yield {"event": "status", "data": json.dumps(job.dict())}
            if job.status in ("completed", "failed"):
                break
            await asyncio.sleep(1)
    return EventSourceResponse(events())
```

Client:

```javascript
const es = new EventSource("/api/jobs/job_abc123/stream");
es.addEventListener("status", (e) => {
  const job = JSON.parse(e.data);
  if (job.status === "completed") es.close();
});
```

## Long-Running Jobs Over Synchronous Request

Sometimes you can't avoid a long request. Strategies:

- Stream a response body (HTTP chunked transfer) so the connection stays alive.
- Use HTTP/2 for better long-connection handling.
- Set explicit timeouts client-side; server provides keep-alive pings.

Still prefer 202 + poll/webhook for anything >30s.

## Testing Webhooks

- Provide a replay endpoint: `POST /api/webhooks/{id}/deliveries/{delivery_id}/replay`.
- Log all delivery attempts and expose them.
- Provide a test event: `POST /api/webhooks/{id}/test`.
- Development tools: ngrok, webhook.site, request bins.

## Common Pitfalls

- **Non-idempotent receivers**: duplicate side effects when webhooks retry. Always dedupe on event ID.
- **No signature verification**: attackers forge events. Always verify HMAC + timestamp.
- **Synchronous processing in handler**: slow receiver → timeouts → retries → thundering herd. Accept fast (200), enqueue for async processing.
- **Blocking on polling status endpoint**: server holds connections. Return immediately with current state.
- **Polling too frequently**: DoS your own status endpoint. Use `Retry-After`; return 304 when unchanged.
- **Unbounded retry**: retry forever, pile up deliveries. Always cap retries; expose failures.
- **Ignoring replay attacks**: reject events with old timestamps.
- **Leaking secrets in URLs**: webhook URL query strings end up in logs. Use headers for auth.
