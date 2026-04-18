---
name: microservices-patterns
description: Use when splitting an application into services, decomposing a monolith, choosing communication patterns between services, implementing API gateways, handling distributed failures, designing event-driven architectures, or working with service discovery — even if the user just says their app is "getting too big" or asks about "handling failures between services."
---

# Microservices Patterns

Apply microservices architecture patterns for service decomposition, inter-service communication, data isolation, and resilience in distributed systems.

## Core Concepts

### 1. Service Decomposition Strategies

**By Business Capability**

- Organize services around business functions
- Each service owns its domain
- Example: OrderService, PaymentService, InventoryService

**By Subdomain (DDD)**

- Core domain, supporting subdomains
- Bounded contexts map to services
- Clear ownership and responsibility

**Strangler Fig Pattern**

- Gradually extract from monolith
- New functionality as microservices
- Proxy routes to old/new systems

### 2. Communication Patterns

**Synchronous (Request/Response)**

- REST APIs
- gRPC
- GraphQL

**Asynchronous (Events/Messages)**

- Event streaming (Kafka)
- Message queues (RabbitMQ, SQS)
- Pub/Sub patterns

### 3. Data Management

**Database Per Service**

- Each service owns its data
- No shared databases
- Loose coupling

**Saga Pattern**

- Distributed transactions
- Compensating actions
- Eventual consistency

### 4. Resilience Patterns

**Circuit Breaker**

- Fail fast on repeated errors
- Prevent cascade failures

**Retry with Backoff**

- Transient fault handling
- Exponential backoff

**Bulkhead**

- Isolate resources
- Limit impact of failures

## Service Decomposition Patterns

### Pattern 1: By Business Capability

```python
# E-commerce example

# Order Service
class OrderService:
    """Handles order lifecycle."""

    async def create_order(self, order_data: dict) -> Order:
        order = Order.create(order_data)

        # Publish event for other services
        await self.event_bus.publish(
            OrderCreatedEvent(
                order_id=order.id,
                customer_id=order.customer_id,
                items=order.items,
                total=order.total
            )
        )

        return order

# Payment Service (separate service)
class PaymentService:
    """Handles payment processing."""

    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        # Process payment
        result = await self.payment_gateway.charge(
            amount=payment_request.amount,
            customer=payment_request.customer_id
        )

        if result.success:
            await self.event_bus.publish(
                PaymentCompletedEvent(
                    order_id=payment_request.order_id,
                    transaction_id=result.transaction_id
                )
            )

        return result

# Inventory Service (separate service)
class InventoryService:
    """Handles inventory management."""

    async def reserve_items(self, order_id: str, items: List[OrderItem]) -> ReservationResult:
        # Check availability
        for item in items:
            available = await self.inventory_repo.get_available(item.product_id)
            if available < item.quantity:
                return ReservationResult(
                    success=False,
                    error=f"Insufficient inventory for {item.product_id}"
                )

        # Reserve items
        reservation = await self.create_reservation(order_id, items)

        await self.event_bus.publish(
            InventoryReservedEvent(
                order_id=order_id,
                reservation_id=reservation.id
            )
        )

        return ReservationResult(success=True, reservation=reservation)
```

### Pattern 2: API Gateway

```python
import asyncio
from fastapi import FastAPI, HTTPException, Depends
import httpx
from circuitbreaker import circuit

app = FastAPI()

class APIGateway:
    """Central entry point for all client requests."""

    def __init__(self):
        self.order_service_url = "http://order-service:8000"
        self.payment_service_url = "http://payment-service:8001"
        self.inventory_service_url = "http://inventory-service:8002"
        self.http_client = httpx.AsyncClient(timeout=5.0)

    @circuit(failure_threshold=5, recovery_timeout=30)
    async def call_order_service(self, path: str, method: str = "GET", **kwargs):
        """Call order service with circuit breaker."""
        response = await self.http_client.request(
            method,
            f"{self.order_service_url}{path}",
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    @circuit(failure_threshold=5, recovery_timeout=30)
    async def call_payment_service(self, path: str, method: str = "GET", **kwargs):
        """Call payment service with circuit breaker."""
        response = await self.http_client.request(
            method,
            f"{self.payment_service_url}{path}",
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    @circuit(failure_threshold=5, recovery_timeout=30)
    async def call_inventory_service(self, path: str, method: str = "GET", **kwargs):
        """Call inventory service with circuit breaker."""
        response = await self.http_client.request(
            method,
            f"{self.inventory_service_url}{path}",
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    async def create_order_aggregate(self, order_id: str) -> dict:
        """Aggregate data from multiple services."""
        # Parallel requests
        order, payment, inventory = await asyncio.gather(
            self.call_order_service(f"/orders/{order_id}"),
            self.call_payment_service(f"/payments/order/{order_id}"),
            self.call_inventory_service(f"/reservations/order/{order_id}"),
            return_exceptions=True
        )

        # Handle partial failures
        result = {"order": order}
        if not isinstance(payment, Exception):
            result["payment"] = payment
        if not isinstance(inventory, Exception):
            result["inventory"] = inventory

        return result

@app.post("/api/orders")
async def create_order(
    order_data: dict,
    gateway: APIGateway = Depends()
):
    """API Gateway endpoint."""
    try:
        # Route to order service
        order = await gateway.call_order_service(
            "/orders",
            method="POST",
            json=order_data
        )
        return {"order": order}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail="Order service unavailable")
```

## Communication Patterns

Services communicate through synchronous or asynchronous channels. The choice depends on coupling tolerance and latency requirements:

- **Synchronous (REST/gRPC)**: Direct request-response. Simple but creates temporal coupling — the caller blocks until the callee responds.
- **Asynchronous (Events/Messages)**: Publish events to a broker (Kafka, RabbitMQ). Decouples services in time and allows independent scaling.

**Rule of thumb**: Use synchronous for queries where the caller needs an immediate answer. Use asynchronous for commands where the caller just needs to know the work will eventually happen.

For implementation patterns with code examples (REST clients with retries, Kafka EventBus, gRPC), see `references/communication-patterns.md`.

## Resilience Patterns

Distributed systems fail partially. These patterns prevent cascading failures:

- **Circuit Breaker**: Track failures to a downstream service. After a threshold, "open" the circuit and fail fast instead of waiting for timeouts. Periodically test if the service recovered.
- **Retry with Backoff**: Retry transient failures with exponential delays (e.g., 1s, 2s, 4s). Cap retries to avoid overwhelming a struggling service.
- **Bulkhead**: Isolate resources per downstream service (e.g., separate connection pools). A failure in one dependency doesn't exhaust resources for others.

For implementations including a full CircuitBreaker class, retry patterns with tenacity, and bulkhead with asyncio.Semaphore, see `references/resilience-patterns.md`.

## Best Practices

1. **Service Boundaries**: Align with business capabilities
2. **Database Per Service**: No shared databases
3. **API Contracts**: Versioned, backward compatible
4. **Async When Possible**: Events over direct calls
5. **Circuit Breakers**: Fail fast on service failures
6. **Distributed Tracing**: Track requests across services
7. **Service Registry**: Dynamic service discovery
8. **Health Checks**: Liveness and readiness probes

## Common Pitfalls

- **Distributed Monolith**: Tightly coupled services
- **Chatty Services**: Too many inter-service calls
- **Shared Databases**: Tight coupling through data
- **No Circuit Breakers**: Cascade failures
- **Synchronous Everything**: Tight coupling, poor resilience
- **Premature Microservices**: Starting with microservices
- **Ignoring Network Failures**: Assuming reliable network
- **No Compensation Logic**: Can't undo failed transactions

## Related Skills

- **api-design-principles**: When designing the REST or GraphQL APIs that your microservices expose — covers resource modeling, pagination, error handling, and versioning
- **saga-orchestration**: When coordinating distributed transactions across services — covers both orchestration and choreography approaches with compensating actions
