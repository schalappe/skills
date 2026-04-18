# Orchestration Pattern

A central orchestrator drives the saga: it stores state, dispatches each step as a command, and reacts to success/failure callbacks. Use when flows have 4+ steps, strict ordering, or when a visible audit trail matters.

## Orchestrator base class

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

class SagaState(Enum):
    STARTED = "started"
    PENDING = "pending"
    COMPENSATING = "compensating"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class SagaStep:
    name: str
    action: str
    compensation: str
    status: str = "pending"
    result: Optional[Dict] = None
    error: Optional[str] = None
    executed_at: Optional[datetime] = None
    compensated_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None  # set by TimeoutSagaOrchestrator

@dataclass
class Saga:
    saga_id: str
    saga_type: str
    state: SagaState
    data: Dict[str, Any]
    steps: List[SagaStep]
    current_step: int = 0
    compensation_index: int = -1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class SagaOrchestrator(ABC):
    def __init__(self, saga_store, event_publisher):
        self.saga_store = saga_store
        self.event_publisher = event_publisher

    @abstractmethod
    def define_steps(self, data: Dict) -> List[SagaStep]: ...

    @property
    @abstractmethod
    def saga_type(self) -> str: ...

    async def start(self, data: Dict) -> Saga:
        saga = Saga(
            saga_id=str(uuid.uuid4()),
            saga_type=self.saga_type,
            state=SagaState.STARTED,
            data=data,
            steps=self.define_steps(data),
        )
        await self.saga_store.save(saga)
        await self._execute_next_step(saga)
        return saga

    async def handle_step_completed(self, saga_id: str, step_name: str, result: Dict):
        saga = await self.saga_store.get(saga_id)
        for step in saga.steps:
            if step.name == step_name:
                step.status = "completed"
                step.result = result
                step.executed_at = datetime.now(timezone.utc)
                break

        saga.current_step += 1
        saga.updated_at = datetime.now(timezone.utc)

        if saga.current_step >= len(saga.steps):
            saga.state = SagaState.COMPLETED
            await self.saga_store.save(saga)
            await self._on_saga_completed(saga)
        else:
            saga.state = SagaState.PENDING
            await self.saga_store.save(saga)
            await self._execute_next_step(saga)

    async def handle_step_failed(self, saga_id: str, step_name: str, error: str):
        saga = await self.saga_store.get(saga_id)
        for step in saga.steps:
            if step.name == step_name:
                step.status = "failed"
                step.error = error
                break

        saga.state = SagaState.COMPENSATING
        saga.updated_at = datetime.now(timezone.utc)
        await self.saga_store.save(saga)
        await self._compensate(saga)

    async def _execute_next_step(self, saga: Saga):
        if saga.current_step >= len(saga.steps):
            return
        step = saga.steps[saga.current_step]
        step.status = "executing"
        await self.saga_store.save(saga)
        await self.event_publisher.publish(
            step.action,
            {"saga_id": saga.saga_id, "step_name": step.name, **saga.data},
        )

    async def _compensate(self, saga: Saga):
        # Compensations run sequentially — publish one, wait for ack, then next.
        for i in range(saga.current_step - 1, -1, -1):
            step = saga.steps[i]
            if step.status == "completed":
                step.status = "compensating"
                saga.compensation_index = i
                await self.saga_store.save(saga)
                await self.event_publisher.publish(
                    step.compensation,
                    {
                        "saga_id": saga.saga_id,
                        "step_name": step.name,
                        "original_result": step.result,
                        **saga.data,
                    },
                )
                return

    async def handle_compensation_completed(self, saga_id: str, step_name: str):
        saga = await self.saga_store.get(saga_id)
        for step in saga.steps:
            if step.name == step_name:
                step.status = "compensated"
                step.compensated_at = datetime.now(timezone.utc)
                break
        await self.saga_store.save(saga)
        await self._compensate(saga)

        all_handled = all(
            s.status in ("compensated", "pending", "failed") for s in saga.steps
        )
        if all_handled:
            saga.state = SagaState.FAILED
            await self.saga_store.save(saga)
            await self._on_saga_failed(saga)

    async def _on_saga_completed(self, saga: Saga):
        await self.event_publisher.publish(
            f"{self.saga_type}Completed",
            {"saga_id": saga.saga_id, **saga.data},
        )

    async def _on_saga_failed(self, saga: Saga):
        await self.event_publisher.publish(
            f"{self.saga_type}Failed",
            {"saga_id": saga.saga_id, "error": "Saga failed", **saga.data},
        )
```

## Concrete saga: order fulfillment

```python
class OrderFulfillmentSaga(SagaOrchestrator):
    @property
    def saga_type(self) -> str:
        return "OrderFulfillment"

    def define_steps(self, data: Dict) -> List[SagaStep]:
        return [
            SagaStep("reserve_inventory",
                     "InventoryService.ReserveItems",
                     "InventoryService.ReleaseReservation"),
            SagaStep("process_payment",
                     "PaymentService.ProcessPayment",
                     "PaymentService.RefundPayment"),
            SagaStep("create_shipment",
                     "ShippingService.CreateShipment",
                     "ShippingService.CancelShipment"),
            SagaStep("send_confirmation",
                     "NotificationService.SendOrderConfirmation",
                     "NotificationService.SendCancellationNotice"),
        ]

async def create_order(order_data: Dict):
    saga = OrderFulfillmentSaga(saga_store, event_publisher)
    return await saga.start({
        "order_id": order_data["order_id"],
        "customer_id": order_data["customer_id"],
        "items": order_data["items"],
        "payment_method": order_data["payment_method"],
        "shipping_address": order_data["shipping_address"],
    })
```

## Participant service handler

```python
class InventoryService:
    async def handle_reserve_items(self, command: Dict):
        try:
            reservation = await self.reserve(command["items"], command["order_id"])
            await self.event_publisher.publish(
                "SagaStepCompleted",
                {
                    "saga_id": command["saga_id"],
                    "step_name": "reserve_inventory",
                    "result": {"reservation_id": reservation.id},
                },
            )
        except InsufficientInventoryError as e:
            await self.event_publisher.publish(
                "SagaStepFailed",
                {
                    "saga_id": command["saga_id"],
                    "step_name": "reserve_inventory",
                    "error": str(e),
                },
            )

    async def handle_release_reservation(self, command: Dict):
        await self.release_reservation(command["original_result"]["reservation_id"])
        await self.event_publisher.publish(
            "SagaCompensationCompleted",
            {"saga_id": command["saga_id"], "step_name": "reserve_inventory"},
        )
```

## Design notes

- **Persist before publishing.** Save saga state *before* emitting the command — a crash between save and publish is recoverable (replay on restart), the reverse is not.
- **One step in flight at a time.** `current_step` is both the cursor and the lock; parallelism requires a different model (DAG-based saga engines like Temporal/Cadence).
- **Compensation is sequential.** `_compensate` publishes one compensation, returns, and waits for the ack to continue — prevents racing releases against each other.
- **Idempotency keys.** Include `saga_id + step_name` as an idempotency key in every command so participants can dedupe retries safely.
