# Decomposition and Topology Patterns

How to carve a monolith into services, shape the edge, and deploy cross-cutting concerns alongside each service.

---

## Strategy 1 — By Business Capability

Each service owns one business function end-to-end (orders, payments, inventory, shipping). The team aligned to that capability owns the service. Boundaries are stable because they follow how the business is organized.

```python
# Order Service — owns the order lifecycle
class OrderService:
    async def create_order(self, order_data: dict) -> Order:
        order = Order.create(order_data)
        await self.event_bus.publish(
            OrderCreatedEvent(
                order_id=order.id,
                customer_id=order.customer_id,
                items=order.items,
                total=order.total,
            )
        )
        return order

# Payment Service — owns payment processing, separate DB, separate deploy
class PaymentService:
    async def process_payment(self, req: PaymentRequest) -> PaymentResult:
        result = await self.payment_gateway.charge(req.amount, req.customer_id)
        if result.success:
            await self.event_bus.publish(
                PaymentCompletedEvent(order_id=req.order_id, transaction_id=result.transaction_id)
            )
        return result
```

**When to use:** you can name the business capabilities your org revolves around. This is the default for greenfield splits.

---

## Strategy 2 — By DDD Bounded Context

Start from a domain model, not an org chart. Identify **bounded contexts** where terms have one meaning (a `Customer` in Billing is not the same entity as a `Customer` in Support). Each bounded context becomes a service. Introduce an **anti-corruption layer** when two contexts must talk but use incompatible models.

**When to use:** complex domain where the same word means different things in different parts of the business. Do an Event Storming workshop before drawing service lines.

---

## Strategy 3 — Strangler Fig (extract from monolith)

Migrate incrementally. Route traffic through a proxy that directs some paths to the new service, the rest to the monolith. Extract one capability at a time until the monolith is empty.

```text
          ┌──────────────┐
Client ──▶│   Proxy /    │──▶ /orders/*       ──▶ New Order Service
          │  API Gateway │──▶ /payments/*     ──▶ New Payment Service
          │              │──▶ everything else ──▶ Legacy Monolith
          └──────────────┘
```

**Steps:**

1. Put a proxy in front of the monolith (no traffic change yet).
2. Build the new service alongside the monolith, using the monolith's DB read-only if needed.
3. Shift writes to the new service; shadow-read to verify parity.
4. Flip the proxy route; retire the corresponding monolith module.
5. Repeat.

**When to use:** any time you're migrating off a monolith. Big-bang rewrites fail.

---

## API Gateway

A single entry point that handles routing, request aggregation, and cross-cutting policy (auth, rate limits, CORS, request/response shaping). Hides the internal service topology from clients.

```python
from fastapi import FastAPI, HTTPException, Depends
import httpx, asyncio
from circuitbreaker import circuit

app = FastAPI()

class APIGateway:
    def __init__(self):
        self.order_url = "http://order-service:8000"
        self.payment_url = "http://payment-service:8001"
        self.inventory_url = "http://inventory-service:8002"
        self.http = httpx.AsyncClient(timeout=5.0)

    @circuit(failure_threshold=5, recovery_timeout=30)
    async def _call(self, url: str, path: str, method="GET", **kw):
        r = await self.http.request(method, f"{url}{path}", **kw)
        r.raise_for_status()
        return r.json()

    async def order_aggregate(self, order_id: str) -> dict:
        order, payment, inventory = await asyncio.gather(
            self._call(self.order_url, f"/orders/{order_id}"),
            self._call(self.payment_url, f"/payments/order/{order_id}"),
            self._call(self.inventory_url, f"/reservations/order/{order_id}"),
            return_exceptions=True,
        )
        result = {"order": order}
        if not isinstance(payment, Exception):
            result["payment"] = payment
        if not isinstance(inventory, Exception):
            result["inventory"] = inventory
        return result

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, gw: APIGateway = Depends()):
    try:
        return await gw.order_aggregate(order_id)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Upstream service unavailable")
```

**Responsibilities to put in the gateway:** auth verification, rate limiting, request shaping, response aggregation, protocol translation (gRPC ⇄ REST).

**Responsibilities to keep out:** business logic (belongs in services), caching of per-user data (belongs in services or a dedicated cache layer).

---

## Backend for Frontend (BFF)

One gateway per client type (web, iOS, Android, partner API). Each BFF tailors the response shape and bundles the calls its specific client needs. Avoids a single monster gateway that tries to please every client.

```text
Web ─────▶ Web BFF ─────┐
iOS ─────▶ iOS BFF ─────┼─▶ Order / Payment / Inventory / ... services
Partner ─▶ Partner BFF ─┘
```

**When to use:** different clients need substantially different response shapes, or different auth/permission rules. Don't add a BFF per page — that's overkill.

---

## Service Mesh and Sidecar

Run a proxy (Envoy, Linkerd-proxy) as a **sidecar container** next to each service pod. The mesh control plane (Istio, Linkerd, Consul) configures the proxies to handle:

- mTLS between services
- Retries, timeouts, circuit breaking
- Traffic shifting (canary, blue/green)
- Metrics and traces

The service code makes plain HTTP calls; the sidecar intercepts them and applies policy. **Application code stays free of resilience libraries.**

```text
┌─────────── Pod ───────────┐    ┌─────────── Pod ───────────┐
│  App ⇄  Sidecar (Envoy)   │◀──▶│  Sidecar (Envoy)  ⇄  App  │
└───────────────────────────┘    └───────────────────────────┘
                ▲                              ▲
                └───────── mTLS ───────────────┘
```

**When to use:**

- You're on Kubernetes and have 10+ services.
- Multiple languages — mesh gives uniform resilience without per-language libraries.
- Compliance requires mTLS between all services.

**When to avoid:**

- Small fleet (2–5 services) — the operational cost of running a mesh exceeds the benefit.
- Not on Kubernetes — sidecars are much harder to run on bare VMs.

---

## Key tradeoffs

| Pattern               | Cost                                    | Benefit                                |
| --------------------- | --------------------------------------- | -------------------------------------- |
| Strangler fig         | Slower than rewrite in the short term   | No big-bang risk, keeps business running |
| API gateway           | New single point of failure (mitigate with HA) | Clean client contract, central policy |
| BFF                   | One more service per client type        | Each client gets tailored API          |
| Service mesh          | Operational complexity, extra latency   | Uniform mTLS + resilience across langs |
