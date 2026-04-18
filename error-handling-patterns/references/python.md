# Python Error Handling

## Custom exception hierarchy

One base class per application; subclass per domain. Attach `code`, `details`, and `timestamp` so handlers can branch on type and structured logs carry full context.

```python
from datetime import datetime
from typing import Optional

class ApplicationError(Exception):
    """Base for every application-raised error."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class ValidationError(ApplicationError):
    def __init__(self, message: str, field: str | None = None, **kwargs):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
        self.field = field

class NotFoundError(ApplicationError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            f"{resource} not found",
            code="NOT_FOUND",
            details={"resource": resource, "id": resource_id},
        )

class ExternalServiceError(ApplicationError):
    def __init__(self, message: str, service: str, **kwargs):
        super().__init__(message, code="EXTERNAL_SERVICE_ERROR", **kwargs)
        self.service = service
```

## Context managers for cleanup

Use `@contextmanager` for transactional scopes and for attaching extra context to any exception raised inside the `with` block.

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def database_transaction(session) -> Generator:
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def error_context(context: str) -> Generator:
    """Re-raise with a prefix while preserving the original cause."""
    try:
        yield
    except Exception as e:
        raise type(e)(f"{context}: {e}") from e
```

## Chaining causes

Always use `raise ... from e` (or `from None` when intentionally masking) so `__cause__` is populated and tracebacks show the root cause.

```python
try:
    user = repo.get(user_id)
except repo.NotFound as e:
    raise NotFoundError("User", user_id) from e
```

## See also

- `references/resilience.md` — retry decorator, circuit breaker, graceful degradation
