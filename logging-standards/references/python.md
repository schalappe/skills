# Python Logging

Wide-event implementations for Python, plus performance and error-enrichment helpers. Load when adding structured logging to a Python service.

## structlog — context-var based

Use `structlog` with a `ContextVar` so the wide event survives `async` handoffs without being threaded through every call.

```python
import logging
import os
import time
from contextvars import ContextVar
from typing import Any

import structlog

_request_context: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})

def configure_structlog() -> None:
    """Configure structlog for wide-event logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

class RequestContext:
    """Build wide-event context throughout the request lifecycle."""

    def __init__(self, request_id: str, service: str):
        self._start_time = time.monotonic()
        self._data: dict[str, Any] = {
            "request_id": request_id,
            "service": service,
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
        _request_context.set(self._data)

    def add(self, **kwargs: Any) -> None:
        self._data.update(kwargs)
        _request_context.set(self._data)

    def emit(self) -> None:
        self._data["duration_ms"] = int((time.monotonic() - self._start_time) * 1000)
        structlog.get_logger().info("request_completed", **self._data)
```

## Standard-library logging with JSON formatter

When pulling in `structlog` is overkill, a formatter on stdlib `logging` is enough.

```python
import json
import logging
from datetime import datetime, timezone

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "extra"):
            log_data.update(record.extra)  # type: ignore[attr-defined]
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logger = logging.getLogger("app")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## FastAPI middleware

Emit exactly one wide event per request, even on unhandled exceptions.

```python
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class WideEventMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        ctx = RequestContext(request_id, "my-service")

        ctx.add(
            endpoint=request.url.path,
            http_method=request.method,
            client_ip=request.client.host if request.client else None,
        )
        request.state.log_context = ctx

        try:
            response = await call_next(request)
            ctx.add(http_status=response.status_code)
            return response
        except Exception as e:
            ctx.add(
                http_status=500,
                error_code=type(e).__name__,
                error_message=str(e),
            )
            raise
        finally:
            ctx.emit()

app = FastAPI()
app.add_middleware(WideEventMiddleware)
```

## Error enrichment

Attach structured context to exceptions so the wide event captures the *why*, not just `"exception raised"`.

```python
import traceback

class LoggableError(Exception):
    """Base exception with structured logging context."""

    def __init__(self, message: str, code: str, **context: Any):
        super().__init__(message)
        self.code = code
        self.context = context

    def to_log_dict(self) -> dict:
        return {
            "error_code": self.code,
            "error_message": str(self),
            **self.context,
        }

class PaymentDeclinedError(LoggableError):
    def __init__(self, reason: str, card_last_four: str):
        super().__init__(
            message=f"Payment declined: {reason}",
            code="PAYMENT_DECLINED",
            decline_reason=reason,
            card_last_four=card_last_four,
        )

def add_exception_context(ctx: RequestContext, exc: Exception) -> None:
    """Add exception details to request context."""
    ctx.add(
        error_code=type(exc).__name__,
        error_message=str(exc),
        error_traceback=traceback.format_exception(type(exc), exc, exc.__traceback__),
    )
    if isinstance(exc, LoggableError):
        ctx.add(**exc.to_log_dict())
```

## Async and buffered emit

Never block request handling on log I/O — especially when shipping to a remote collector.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

_log_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="log-")

async def async_emit(ctx: RequestContext) -> None:
    """Emit the log on a background thread."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_log_executor, ctx.emit)
```

Buffer + periodic flush when per-log overhead dominates:

```python
import time
from queue import Queue
from threading import Thread

class BufferedLogger:
    """Buffer logs and flush periodically or on threshold."""

    def __init__(self, flush_interval: float = 1.0, buffer_size: int = 100):
        self._buffer: Queue = Queue()
        self._flush_interval = flush_interval
        self._buffer_size = buffer_size
        self._start_flusher()

    def log(self, event: dict) -> None:
        self._buffer.put(event)
        if self._buffer.qsize() >= self._buffer_size:
            self._flush()

    def _flush(self) -> None:
        events = []
        while not self._buffer.empty():
            events.append(self._buffer.get_nowait())
        if events:
            self._send_batch(events)

    def _send_batch(self, events: list) -> None:
        # Write to file, POST to collector, etc.
        pass

    def _start_flusher(self) -> None:
        def flusher() -> None:
            while True:
                time.sleep(self._flush_interval)
                self._flush()

        Thread(target=flusher, daemon=True).start()
```
