# Communication Patterns

Implementation patterns for inter-service communication in microservices architectures.

## Decision Matrix

| Factor | Synchronous (REST) | Synchronous (gRPC) | Asynchronous (Events) |
|---|---|---|---|
| **Coupling** | Temporal — caller blocks | Temporal — caller blocks | Decoupled in time |
| **Latency** | HTTP overhead, text-based | Low — binary protocol, HTTP/2 | Variable — depends on broker |
| **Use when** | Simple CRUD, public APIs, broad client support | Internal service-to-service, high throughput, streaming | Commands, notifications, data pipelines |
| **Avoid when** | High fan-out, long-running ops | Public-facing APIs, simple setups | Caller needs immediate response |
| **Schema** | OpenAPI / JSON Schema | Protobuf (strict contracts) | Event schema registry (Avro, JSON Schema) |
| **Error handling** | HTTP status codes | gRPC status codes | Dead letter queues, retry topics |

**Rule of thumb**: Use synchronous for queries where the caller needs an immediate answer. Use asynchronous for commands where the caller just needs to know the work will eventually happen. Use gRPC when you control both ends and need performance or streaming.

---

## Synchronous REST Communication

HTTP-based request-response with retries and connection management.

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class ServiceClient:
    """HTTP client with retries and timeout."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            limits=httpx.Limits(max_keepalive_connections=20)
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get(self, path: str, **kwargs):
        """GET with automatic retries."""
        response = await self.client.get(f"{self.base_url}{path}", **kwargs)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, **kwargs):
        """POST request."""
        response = await self.client.post(f"{self.base_url}{path}", **kwargs)
        response.raise_for_status()
        return response.json()

# Usage
payment_client = ServiceClient("http://payment-service:8001")
result = await payment_client.post("/payments", json=payment_data)
```

**Key considerations:**

- Set explicit timeouts (connect + read) to avoid hanging on unresponsive services
- Use connection pooling (`max_keepalive_connections`) to reduce handshake overhead
- Retry only on transient failures (5xx, timeouts) — never on 4xx client errors
- Add correlation IDs to headers for distributed tracing

---

## Asynchronous Event-Driven

Publish-subscribe communication through a message broker (Kafka). Services emit domain events and other services react independently.

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List

@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    occurred_at: datetime
    data: dict

class EventBus:
    """Event publishing and subscription."""

    def __init__(self, bootstrap_servers: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode()
        )
        await self.producer.start()

    async def publish(self, event: DomainEvent):
        """Publish event to Kafka topic."""
        topic = event.event_type
        await self.producer.send_and_wait(
            topic,
            value=asdict(event),
            key=event.aggregate_id.encode()
        )

    async def subscribe(self, topic: str, handler: callable):
        """Subscribe to events."""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode()),
            group_id="my-service"
        )
        await consumer.start()

        try:
            async for message in consumer:
                event_data = message.value
                await handler(event_data)
        finally:
            await consumer.stop()

# Order Service publishes event
async def create_order(order_data: dict):
    order = await save_order(order_data)

    event = DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type="OrderCreated",
        aggregate_id=order.id,
        occurred_at=datetime.now(),
        data={
            "order_id": order.id,
            "customer_id": order.customer_id,
            "total": order.total,
            "items": order.items
        }
    )

    await event_bus.publish(event)

# Inventory Service listens for OrderCreated
async def handle_order_created(event_data: dict):
    """React to order creation."""
    order_id = event_data["data"]["order_id"]
    items = event_data["data"]["items"]

    # Reserve inventory
    await reserve_inventory(order_id, items)
```

**Key considerations:**

- Use a schema registry to enforce event contracts and detect breaking changes
- Partition events by aggregate ID so related events are processed in order
- Design events as immutable facts — include all data the consumer needs (avoid callbacks)
- Implement idempotent consumers since messages can be delivered more than once
- Use dead letter queues for events that fail processing after retries

---

## gRPC Communication

Binary protocol over HTTP/2 with strongly typed contracts. Best for internal service-to-service calls where performance matters.

**When to use gRPC:**

- Internal communication between services you control
- High-throughput, low-latency requirements
- Streaming data (server-push, bidirectional)
- Polyglot environments — Protobuf generates clients in multiple languages

**When to avoid gRPC:**

- Public-facing APIs where browser support is needed (REST is simpler)
- Simple request-response where HTTP overhead is not a bottleneck
- Teams unfamiliar with Protobuf tooling

**How it works:**

1. Define service contracts in `.proto` files (Protobuf)
2. Generate client and server stubs from the proto definition
3. Clients call methods on the generated stub as if they were local functions
4. Data is serialized in compact binary format (smaller payloads than JSON)

```protobuf
// order_service.proto
syntax = "proto3";

service OrderService {
    rpc GetOrder (GetOrderRequest) returns (OrderResponse);
    rpc StreamOrderUpdates (GetOrderRequest) returns (stream OrderUpdate);
}

message GetOrderRequest {
    string order_id = 1;
}

message OrderResponse {
    string order_id = 1;
    string status = 2;
    double total = 3;
}

message OrderUpdate {
    string order_id = 1;
    string status = 2;
    string timestamp = 3;
}
```

**Key considerations:**

- Use Protobuf field numbers for backward-compatible schema evolution (never reuse numbers)
- Implement deadlines/timeouts on every call — gRPC does not have a default timeout
- Use gRPC health checking protocol for load balancer integration
- Consider gRPC-Web or an API gateway translation layer for browser clients
