# Logging Patterns Reference

Detailed patterns and language-specific examples for implementing wide event logging.

## Wide Event Patterns

### Python with structlog

```python
import structlog
from contextvars import ContextVar
from typing import Any

# Request context stored in context variable
_request_context: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})

def configure_structlog():
    """Configure structlog for wide event logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

class RequestContext:
    """Build wide event context throughout request lifecycle."""

    def __init__(self, request_id: str, service: str):
        self._start_time = time.monotonic()
        self._data = {
            "request_id": request_id,
            "service": service,
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
        _request_context.set(self._data)

    def add(self, **kwargs):
        """Add fields to request context."""
        self._data.update(kwargs)
        _request_context.set(self._data)

    def emit(self):
        """Emit wide event at request completion."""
        self._data["duration_ms"] = int((time.monotonic() - self._start_time) * 1000)
        log = structlog.get_logger()
        log.info("request_completed", **self._data)
```

### Python with standard logging

```python
import logging
import json
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

        # Merge extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)

# Configure handler
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logger = logging.getLogger("app")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### TypeScript/Node.js with Pino

```typescript
import pino from "pino";
import { AsyncLocalStorage } from "async_hooks";

// Request context storage
const requestContext = new AsyncLocalStorage<Map<string, unknown>>();

const logger = pino({
  level: "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  mixin() {
    // Merge request context into every log
    const ctx = requestContext.getStore();
    return ctx ? Object.fromEntries(ctx) : {};
  },
});

class RequestLogger {
  private startTime: number;
  private context: Map<string, unknown>;

  constructor(requestId: string, service: string) {
    this.startTime = Date.now();
    this.context = new Map([
      ["request_id", requestId],
      ["service", service],
      ["environment", process.env.NODE_ENV ?? "development"],
    ]);
  }

  add(fields: Record<string, unknown>): void {
    for (const [key, value] of Object.entries(fields)) {
      this.context.set(key, value);
    }
  }

  emit(): void {
    this.context.set("duration_ms", Date.now() - this.startTime);
    logger.info(Object.fromEntries(this.context), "request_completed");
  }
}

// Express middleware
function requestContextMiddleware(req, res, next) {
  const ctx = new RequestLogger(req.id, "my-service");
  requestContext.run(ctx.context, () => {
    res.on("finish", () => ctx.emit());
    next();
  });
}
```

### Go with zerolog

```go
package logging

import (
    "context"
    "os"
    "time"

    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

type contextKey string

const requestContextKey contextKey = "request_context"

type RequestContext struct {
    fields    map[string]interface{}
    startTime time.Time
}

func NewRequestContext(requestID, service string) *RequestContext {
    return &RequestContext{
        fields: map[string]interface{}{
            "request_id":  requestID,
            "service":     service,
            "environment": os.Getenv("ENVIRONMENT"),
        },
        startTime: time.Now(),
    }
}

func (rc *RequestContext) Add(key string, value interface{}) {
    rc.fields[key] = value
}

func (rc *RequestContext) Emit() {
    rc.fields["duration_ms"] = time.Since(rc.startTime).Milliseconds()

    event := log.Info()
    for k, v := range rc.fields {
        event = event.Interface(k, v)
    }
    event.Msg("request_completed")
}

// Middleware for HTTP handlers
func WithRequestContext(ctx context.Context, rc *RequestContext) context.Context {
    return context.WithValue(ctx, requestContextKey, rc)
}

func GetRequestContext(ctx context.Context) *RequestContext {
    rc, _ := ctx.Value(requestContextKey).(*RequestContext)
    return rc
}
```

## Framework Integration Patterns

### FastAPI Middleware

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

app = FastAPI()

class WideEventMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        ctx = RequestContext(request_id, "my-service")

        ctx.add(
            endpoint=request.url.path,
            http_method=request.method,
            client_ip=request.client.host,
        )

        # Store in request state for handlers to access
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

app.add_middleware(WideEventMiddleware)
```

### Express.js Middleware

```typescript
import { Request, Response, NextFunction } from "express";
import { v4 as uuidv4 } from "uuid";

function wideEventMiddleware(req: Request, res: Response, next: NextFunction) {
  const requestId = req.headers["x-request-id"] as string ?? uuidv4();
  const ctx = new RequestLogger(requestId, "my-service");

  ctx.add({
    endpoint: req.path,
    http_method: req.method,
    client_ip: req.ip,
  });

  // Attach to request for handlers to access
  req.logContext = ctx;

  // Capture response status
  const originalEnd = res.end;
  res.end = function (...args) {
    ctx.add({ http_status: res.statusCode });
    ctx.emit();
    return originalEnd.apply(this, args);
  };

  next();
}
```

## Sampling Patterns

### Tail Sampling Implementation

```python
import random
from dataclasses import dataclass
from typing import Callable

@dataclass
class SamplingConfig:
    error_rate: float = 1.0       # Always keep errors
    slow_rate: float = 1.0        # Always keep slow requests
    vip_rate: float = 1.0         # Always keep VIP users
    baseline_rate: float = 0.05   # 5% random sample

    slow_threshold_ms: int = 1000  # P99 threshold
    vip_tiers: set = frozenset({"premium", "enterprise"})

def should_sample(ctx: RequestContext, config: SamplingConfig) -> bool:
    """Determine if this request should be logged."""

    # Always keep errors
    if ctx.get("http_status", 200) >= 400:
        return random.random() < config.error_rate

    # Always keep slow requests
    if ctx.get("duration_ms", 0) > config.slow_threshold_ms:
        return random.random() < config.slow_rate

    # Always keep VIP users
    if ctx.get("user_tier") in config.vip_tiers:
        return random.random() < config.vip_rate

    # Random sample baseline traffic
    return random.random() < config.baseline_rate
```

### Head Sampling vs Tail Sampling

| Type | Decision Point | Pros | Cons |
|------|----------------|------|------|
| Head | Request start | Consistent trace, simple | Loses interesting traffic |
| Tail | Request end | Keeps errors/slow | More complex, memory overhead |

**Always prefer tail sampling** - you cannot know at request start if it will fail or be slow.

## Error Enrichment Patterns

### Structured Error Context

```python
class LoggableError(Exception):
    """Base exception with structured logging context."""

    def __init__(self, message: str, code: str, **context):
        super().__init__(message)
        self.code = code
        self.context = context

    def to_log_dict(self) -> dict:
        return {
            "error_code": self.code,
            "error_message": str(self),
            **self.context
        }

class PaymentDeclinedError(LoggableError):
    def __init__(self, reason: str, card_last_four: str):
        super().__init__(
            message=f"Payment declined: {reason}",
            code="PAYMENT_DECLINED",
            decline_reason=reason,
            card_last_four=card_last_four,
        )
```

### Capturing Stack Traces

```python
import traceback

def add_exception_context(ctx: RequestContext, exc: Exception):
    """Add exception details to request context."""
    ctx.add(
        error_code=type(exc).__name__,
        error_message=str(exc),
        error_traceback=traceback.format_exception(type(exc), exc, exc.__traceback__),
    )

    # If it's a LoggableError, add structured context
    if isinstance(exc, LoggableError):
        ctx.add(**exc.to_log_dict())
```

## Performance Patterns

### Async Logging

Never block request handling on log I/O:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Dedicated thread pool for logging
_log_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="log-")

async def async_emit(ctx: RequestContext):
    """Emit log in background thread."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_log_executor, ctx._sync_emit)
```

### Buffered Logging

```python
from queue import Queue
from threading import Thread
import time

class BufferedLogger:
    """Buffer logs and flush periodically or on threshold."""

    def __init__(self, flush_interval: float = 1.0, buffer_size: int = 100):
        self._buffer = Queue()
        self._flush_interval = flush_interval
        self._buffer_size = buffer_size
        self._start_flusher()

    def log(self, event: dict):
        self._buffer.put(event)
        if self._buffer.qsize() >= self._buffer_size:
            self._flush()

    def _flush(self):
        events = []
        while not self._buffer.empty():
            events.append(self._buffer.get_nowait())
        if events:
            self._send_batch(events)

    def _send_batch(self, events: list):
        # Send to logging backend (e.g., write to file, send to API)
        pass

    def _start_flusher(self):
        def flusher():
            while True:
                time.sleep(self._flush_interval)
                self._flush()
        Thread(target=flusher, daemon=True).start()
```

## Sensitive Data Patterns

### Field Redaction

```python
SENSITIVE_FIELDS = {"password", "token", "api_key", "secret", "ssn", "credit_card"}

def redact_sensitive(data: dict) -> dict:
    """Redact sensitive fields from log data."""
    result = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_sensitive(value)
        else:
            result[key] = value
    return result
```

### PII Masking

```python
import hashlib

def mask_email(email: str) -> str:
    """Mask email while keeping some identifiability."""
    local, domain = email.split("@")
    return f"{local[0]}***@{domain}"

def hash_user_id(user_id: str, salt: str) -> str:
    """Hash user ID for privacy while maintaining correlation."""
    return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()[:16]
```
