# Observability Patterns

In a distributed system, you cannot debug by attaching a debugger to a single process. You have to reconstruct a request's path from the traces, metrics, and logs each service emits. This reference covers the patterns that make that reconstruction possible.

---

## The three signals

| Signal   | Question it answers                          | Typical tool                        |
| -------- | -------------------------------------------- | ----------------------------------- |
| Traces   | Where did this request spend its time?       | OpenTelemetry + Jaeger / Tempo      |
| Metrics  | How is the system behaving in aggregate?     | Prometheus + Grafana                |
| Logs     | What exactly happened for this event?        | Loki / Elasticsearch / CloudWatch   |

All three must share a **correlation ID** so you can jump between them.

---

## Correlation IDs

Generate a unique ID at the edge (API gateway or first service), attach it to an HTTP header (`X-Request-ID` or W3C `traceparent`), and propagate it through every downstream call — including async events.

```python
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["x-request-id"] = cid
        return response

# Downstream HTTP call — propagate the ID
async def call_payment(cid: str, data: dict):
    return await http.post(
        "http://payment-service/charge",
        json=data,
        headers={"x-request-id": cid},
    )

# Async event — embed the ID in the envelope
event = {
    "event_id": str(uuid.uuid4()),
    "correlation_id": cid,
    "event_type": "OrderCreated",
    "data": {...},
}
```

**Rule:** every log line, every metric label, every event envelope carries the correlation ID. Without it, you cannot correlate signals across services.

---

## Distributed Tracing with OpenTelemetry

OpenTelemetry (OTel) is the vendor-neutral standard for traces, metrics, and logs. It auto-instruments most frameworks (FastAPI, Flask, Express, Spring, gRPC clients) and propagates context through HTTP/gRPC/Kafka.

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)

FastAPIInstrumentor().instrument_app(app)
HTTPXClientInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

async def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        await reserve_inventory(order_id)   # child span auto-created
        await charge_payment(order_id)
        span.set_attribute("order.status", "complete")
```

**Key practices:**

- Propagate context via the W3C `traceparent` / `tracestate` headers — OTel does this automatically for instrumented clients.
- Use **semantic conventions** (`http.method`, `db.system`, `messaging.system`) so different backends can interpret spans uniformly.
- Sample aggressively in production (1–10%). Record **all** errors regardless of sample rate.
- Put the correlation ID on every span as an attribute so logs and traces can cross-reference.

---

## Metrics: the RED and USE methods

**RED** for request-driven services:

- **Rate** — requests per second
- **Errors** — failures per second
- **Duration** — latency histogram (p50, p95, p99)

**USE** for resources (queues, DBs, caches):

- **Utilization** — % of time the resource is busy
- **Saturation** — queue depth or backlog
- **Errors** — error count

```python
from prometheus_client import Counter, Histogram

requests_total = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "path", "status"],
)
request_duration = Histogram(
    "http_request_duration_seconds", "HTTP request duration",
    ["method", "path"],
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    with request_duration.labels(request.method, request.url.path).time():
        response = await call_next(request)
    requests_total.labels(request.method, request.url.path, response.status_code).inc()
    return response
```

**Alert on symptoms, not causes:** alert when user-facing SLOs break (error rate > 1%, p99 > 1s), not when CPU is high. A high-CPU box that serves traffic fine is not a problem.

---

## Structured logging

JSON log lines with consistent field names make logs queryable. See the `logging-standards` sibling skill for full guidance. Minimum fields for a microservices setup:

```json
{
  "timestamp": "2026-04-19T10:15:32.123Z",
  "level": "info",
  "service": "order-service",
  "correlation_id": "a1b2c3...",
  "trace_id": "4bf92f3577b34da6...",
  "user_id": "u_123",
  "event": "order.created",
  "order_id": "42"
}
```

**Rule:** never log an error without the correlation ID. A log line you can't trace is noise.

---

## Service Discovery

Clients need to find healthy instances of a service without hardcoding IPs. Three approaches:

### 1. Client-side discovery

Client queries a registry (Consul, Eureka, etcd) for the list of instances and load-balances itself.

- **Pros:** client controls the load-balancing strategy.
- **Cons:** every client language needs a discovery library.

### 2. Server-side discovery

Client calls a stable DNS name or load balancer; the LB queries the registry and forwards.

- **Pros:** clients stay simple (just DNS).
- **Cons:** extra hop; LB is a shared component.

### 3. Platform DNS (Kubernetes)

`http://payment-service.default.svc.cluster.local` resolves to any healthy pod behind the `payment-service` Service. Kubernetes handles registration and health-based removal automatically.

- **Pros:** no extra infrastructure, clients just use DNS.
- **Cons:** locked to Kubernetes.

**Default recommendation:** if you're on Kubernetes, use platform DNS. Otherwise Consul or cloud-provider service discovery.

---

## Health Checks

See `references/resilience-patterns.md` for the liveness vs readiness distinction and FastAPI implementation. Quick summary:

- `/health/live` — am I alive? Never depend on downstreams. Maps to Kubernetes `livenessProbe`.
- `/health/ready` — am I ready to serve? Check DB, cache, critical downstreams. Maps to `readinessProbe`.

---

## SLOs: turning metrics into decisions

A **Service Level Objective** is a target for a key metric (e.g., "99.9% of requests in < 500ms over a 30-day window"). Your **error budget** is the gap between 100% and the SLO — 0.1% in this example.

Decisions it drives:

- **Budget remaining:** ship features faster, experiment more.
- **Budget burning fast:** freeze risky changes, invest in reliability.
- **Budget exhausted:** no new features until the budget recovers.

SLOs make reliability discussions concrete instead of "the system feels slow."

---

## Key considerations

- **Instrument once, at the framework level** — per-endpoint manual instrumentation rots.
- **Cardinality matters** — high-cardinality metric labels (user ID, request ID) explode storage. Keep those in traces and logs.
- **Store traces and logs long enough to debug** — 7–30 days typical. Sampled traces can go longer at lower fidelity.
- **Practice the alert** — if nobody has walked through the dashboard during an incident, the observability doesn't exist yet.
