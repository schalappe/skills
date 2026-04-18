# Data Management Patterns

Each service owns its data. This reference covers how to keep that ownership intact while still satisfying queries, transactions, and read-heavy access patterns.

---

## Database per Service

Each service has its own schema (and often its own database engine). No other service may connect to it. Cross-service data is obtained through the owning service's API or through events the owner publishes.

**Why the rule is strict:**

- A shared DB leaks implementation details — any service can couple to any column.
- Schema migrations become a cross-team coordination nightmare.
- You lose the freedom to pick the right storage per service (Postgres, DynamoDB, Elasticsearch, Redis).

**Choosing the right engine per service:**

| Workload                          | Fit                                   |
| --------------------------------- | ------------------------------------- |
| Transactional CRUD                | PostgreSQL, MySQL                     |
| Flexible document schemas         | MongoDB, DynamoDB                     |
| Full-text search                  | Elasticsearch, OpenSearch             |
| High-write time-series            | ClickHouse, TimescaleDB               |
| Cache / session / ephemeral       | Redis                                 |

---

## Transactional Outbox Pattern

The problem: after a write, you must publish an event. If the write succeeds but the broker call fails, the system is inconsistent. If you publish first, a DB rollback leaves a "ghost" event.

**Solution:** write the event to an `outbox` table in the same transaction as the business change. A separate relay reads the outbox and publishes to the broker, marking rows as sent.

```python
# Inside the same DB transaction
async def create_order(data: dict, conn):
    async with conn.transaction():
        order = await conn.fetchrow(
            "INSERT INTO orders (...) VALUES (...) RETURNING *", ...
        )
        await conn.execute(
            "INSERT INTO outbox (aggregate_id, event_type, payload) VALUES ($1, $2, $3)",
            order["id"], "OrderCreated", json.dumps(order_payload(order)),
        )
        return order

# Relay — runs as a background worker
async def relay_outbox(conn, producer):
    rows = await conn.fetch(
        "SELECT id, event_type, payload FROM outbox WHERE sent_at IS NULL ORDER BY id LIMIT 100"
    )
    for row in rows:
        await producer.send_and_wait(
            topic=row["event_type"],
            value=row["payload"].encode(),
        )
        await conn.execute(
            "UPDATE outbox SET sent_at = now() WHERE id = $1", row["id"]
        )
```

**Variants:**

- **Polling relay** (shown above) — simple, works on any DB.
- **CDC relay** — Debezium or similar streams the WAL / binlog directly to Kafka. Lower latency, no polling, but more infra.

**Key considerations:**

- Consumers must be idempotent — the relay can resend on crash.
- Preserve order per aggregate by using `aggregate_id` as the Kafka partition key.
- Purge `outbox` on a schedule to keep it small.

---

## CQRS (Command Query Responsibility Segregation)

Split writes and reads into separate models. Writes go to a normalized OLTP store optimized for integrity. Reads are served from denormalized projections optimized for query shape.

```text
┌──────────┐     commands      ┌──────────────┐
│  Client  │ ─────────────────▶│ Write model  │ (Postgres)
└──────────┘                   └──────┬───────┘
                                      │ events
                                      ▼
┌──────────┐     queries       ┌──────────────┐
│  Client  │ ─────────────────▶│  Read model  │ (Elasticsearch / Redis / denormalized tables)
└──────────┘                   └──────────────┘
```

**When to use:**

- Read and write shapes diverge significantly (e.g., writes are by aggregate, reads are by joined view).
- Read traffic is 10× or more write traffic.
- Different teams own reads and writes.

**When to skip:** plain CRUD where the read shape matches the write shape. CQRS doubles the moving parts.

---

## Event Sourcing

Store the **sequence of events** that led to current state, not the current state itself. Current state is derived by replaying events. Pairs naturally with CQRS — the event log is the write model, projections are the read model.

```text
Event log (append-only):
  OrderCreated   { order_id: 42, items: [...] }
  ItemAdded      { order_id: 42, sku: "X" }
  OrderShipped   { order_id: 42, tracking: "..." }

Projection:
  orders table with current status = "shipped"
```

**Benefits:**

- Full audit trail for free.
- Can rebuild any projection from history (useful when requirements change).
- Temporal queries: "what did this order look like on Tuesday?"

**Costs:**

- Schema evolution on events is hard — events are immutable, so you can't change them, only add new versions and upcast old ones.
- Eventual consistency between write log and read projections.
- Operational burden of event store + projection rebuilders.

**When to use:** domains where history matters intrinsically (finance, healthcare, compliance-heavy workflows). **When to skip:** CRUD apps — don't adopt event sourcing because it sounds cool.

---

## Read Replicas and Cached Projections

A lighter-weight version of CQRS. The owning service emits events; other services subscribe and maintain a local read-only copy of the data they need.

**Example:** Order Service owns orders. Reporting Service subscribes to `OrderCreated` / `OrderShipped` and maintains a denormalized `order_facts` table in its own DB.

**Key considerations:**

- Keep the replica minimal — only the fields this consumer needs.
- Accept eventual consistency; design UX around it (e.g., "your order is being processed").
- Include a full snapshot mechanism for new consumers or disaster recovery.

---

## Saga (cross-service transactions)

When a business process spans multiple services, use a **saga** — a sequence of local transactions, each with a compensating action that reverses it on failure. Two flavors: **orchestration** (a central coordinator sends commands) or **choreography** (services react to each other's events).

Full coverage including code lives in the `saga-orchestration` sibling skill — load that skill when designing any cross-service workflow that needs atomicity.

---

## Anti-patterns

| Anti-pattern                 | Why it bites                                     |
| ---------------------------- | ------------------------------------------------ |
| Shared database              | Any schema change coordinates all services       |
| Cross-service SQL join       | Couples data models, blocks independent deploys  |
| Synchronous read via owning service on every request | Makes every query a distributed query; fragile at scale |
| Two-phase commit across services | Locks held across network calls; rare good fits |
| Publish event, then DB write | Ghost events when the DB write fails — use outbox |
