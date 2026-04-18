# Choreography Pattern

No central coordinator. Each service listens for events that concern it and publishes the next event when its work is done. Use for short flows (2–3 steps) with highly autonomous teams where no single service should "own" the workflow.

## Event-driven saga

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SagaContext:
    saga_id: str
    step: int
    data: Dict[str, Any]
    completed_steps: list

class OrderChoreographySaga:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._register_handlers()

    def _register_handlers(self):
        self.event_bus.subscribe("OrderCreated", self._on_order_created)
        self.event_bus.subscribe("InventoryReserved", self._on_inventory_reserved)
        self.event_bus.subscribe("PaymentProcessed", self._on_payment_processed)
        self.event_bus.subscribe("ShipmentCreated", self._on_shipment_created)

        # Compensation handlers
        self.event_bus.subscribe("PaymentFailed", self._on_payment_failed)
        self.event_bus.subscribe("ShipmentFailed", self._on_shipment_failed)

    async def _on_order_created(self, event: Dict):
        await self.event_bus.publish("ReserveInventory", {
            "saga_id": event["order_id"],
            "order_id": event["order_id"],
            "items": event["items"],
        })

    async def _on_inventory_reserved(self, event: Dict):
        await self.event_bus.publish("ProcessPayment", {
            "saga_id": event["saga_id"],
            "order_id": event["order_id"],
            "amount": event["total_amount"],
            "reservation_id": event["reservation_id"],  # carry forward for compensation
        })

    async def _on_payment_processed(self, event: Dict):
        await self.event_bus.publish("CreateShipment", {
            "saga_id": event["saga_id"],
            "order_id": event["order_id"],
            "payment_id": event["payment_id"],
            "reservation_id": event["reservation_id"],
        })

    async def _on_shipment_created(self, event: Dict):
        await self.event_bus.publish("OrderFulfilled", {
            "saga_id": event["saga_id"],
            "order_id": event["order_id"],
            "tracking_number": event["tracking_number"],
            "payment_id": event["payment_id"],
            "reservation_id": event["reservation_id"],
        })

    # Compensation handlers
    async def _on_payment_failed(self, event: Dict):
        await self.event_bus.publish("ReleaseInventory", {
            "saga_id": event["saga_id"],
            "reservation_id": event["reservation_id"],
        })
        await self.event_bus.publish("OrderFailed", {
            "order_id": event["order_id"],
            "reason": "Payment failed",
        })

    async def _on_shipment_failed(self, event: Dict):
        await self.event_bus.publish("RefundPayment", {
            "saga_id": event["saga_id"],
            "payment_id": event["payment_id"],
        })
        await self.event_bus.publish("ReleaseInventory", {
            "saga_id": event["saga_id"],
            "reservation_id": event["reservation_id"],
        })
```

## Design notes

- **Carry context forward in every event.** Because there is no orchestrator holding state, each event must contain all data required by downstream steps *and* by any future compensation (e.g. `reservation_id` stays in the payload long after inventory has acked).
- **Name events as facts, not commands.** `InventoryReserved` (past-tense fact) is publishable by anyone who observed it; `ReserveInventory` (imperative) implies a single addressed recipient. Mixing the two is fine — facts drive the flow, commands target a specific service.
- **Distributed tracing is mandatory.** With no central log, a missing correlation ID means the only way to debug is to cross-reference logs across all services. Propagate `saga_id` through every event.
- **Beware hidden cycles.** Two services subscribing to each other's events can form loops. Draw the event graph once per flow and verify it is a DAG.
- **Compensation events need explicit handlers.** Unlike orchestration, there is no built-in reverse traversal — each failure path must be coded (`PaymentFailed` → release inventory; `ShipmentFailed` → refund + release). This grows combinatorially with the number of steps, which is why orchestration wins past ~4 steps.
