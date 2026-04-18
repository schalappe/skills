---
name: error-handling-patterns
description: Use when implementing error handling, designing fault-tolerant systems, adding retry or circuit breaker patterns, creating custom exceptions, or improving error messages — even for simple try-catch questions. Covers exception hierarchies, Result types, circuit breakers, graceful degradation, and error aggregation.
---

# Error Handling Patterns

Build resilient applications with robust error handling strategies that gracefully handle failures and provide excellent debugging experiences.

## When to Use This Skill

- Implementing error handling in new features
- Designing error-resilient APIs
- Improving application reliability
- Creating better error messages
- Implementing retry and circuit breaker patterns
- Handling async/concurrent errors

## Core Concepts

### Error Handling Philosophies

| Approach | Use Case | Example |
|----------|----------|---------|
| Exceptions | Unexpected errors, exceptional conditions | try-catch blocks |
| Result Types | Expected errors, validation failures | `Result<T, E>` |
| Option/Maybe | Nullable values, optional returns | `Option<T>` |
| Panics/Crashes | Unrecoverable errors, programming bugs | `panic!()` |

### Error Categories

**Recoverable Errors:**
- Network timeouts
- Missing files
- Invalid user input
- API rate limits

**Unrecoverable Errors:**
- Out of memory
- Stack overflow
- Programming bugs (null pointer, etc.)

## Quick Reference: Exception Hierarchy

```python
class ApplicationError(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

class ValidationError(ApplicationError):
    """Raised when validation fails."""
    pass

class NotFoundError(ApplicationError):
    """Raised when resource not found."""
    pass

class ExternalServiceError(ApplicationError):
    """Raised when external service fails."""
    pass
```

## Universal Patterns

### Pattern 1: Retry with Exponential Backoff

```python
def retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """Retry decorator with exponential backoff and jitter."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        delay = backoff_factor ** attempt
                        jitter = random.uniform(0, delay * 0.5)
                        time.sleep(delay + jitter)
                        continue
                    raise
        return wrapper
    return decorator
```

### Pattern 2: Circuit Breaker

Prevent cascading failures in distributed systems.

```python
class CircuitBreaker:
    """Three states: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)."""

    def call(self, func):
        if self.state == CircuitState.OPEN:
            if self._timeout_expired():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError()

        try:
            result = func()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise
```

### Pattern 3: Error Aggregation

Collect multiple errors instead of failing on first error.

```typescript
class ErrorCollector {
  private errors: Error[] = [];

  add(error: Error): void {
    this.errors.push(error);
  }

  hasErrors(): boolean {
    return this.errors.length > 0;
  }

  throw(): never {
    throw new AggregateError(this.errors, `${this.errors.length} errors`);
  }
}

// Usage: Validate all fields before failing
function validateUser(data: any): User {
  const errors = new ErrorCollector();
  if (!data.email) errors.add(new ValidationError("Email required"));
  if (!data.name) errors.add(new ValidationError("Name required"));
  if (errors.hasErrors()) errors.throw();
  return data as User;
}
```

### Pattern 4: Graceful Degradation

Provide fallback functionality when errors occur.

```python
def with_fallback(primary, fallback, log_error=True):
    """Try primary function, fall back on error."""
    try:
        return primary()
    except Exception as e:
        if log_error:
            logger.error(f"Primary failed: {e}")
        return fallback()

# Usage
def get_user_profile(user_id: str):
    return with_fallback(
        primary=lambda: fetch_from_cache(user_id),
        fallback=lambda: fetch_from_database(user_id)
    )
```

### Pattern 5: Result Type (TypeScript)

```typescript
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

function Ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function Err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

// Usage
function parseJSON<T>(json: string): Result<T, SyntaxError> {
  try {
    return Ok(JSON.parse(json) as T);
  } catch (error) {
    return Err(error as SyntaxError);
  }
}
```

## Best Practices

1. **Fail Fast**: Validate input early, fail quickly
2. **Preserve Context**: Include stack traces, metadata, timestamps
3. **Meaningful Messages**: Explain what happened and how to fix it
4. **Log Appropriately**: Error = log, expected failure = don't spam logs
5. **Handle at Right Level**: Catch where you can meaningfully handle
6. **Clean Up Resources**: Use try-finally, context managers, defer
7. **Don't Swallow Errors**: Log or re-throw, don't silently ignore
8. **Type-Safe Errors**: Use typed errors when possible

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Catching too broadly | `except Exception` hides bugs | Catch specific exceptions |
| Empty catch blocks | Silently swallowing errors | Log or re-throw |
| Logging and re-throwing | Duplicate log entries | Log at one level only |
| Not cleaning up | Resource leaks | Use context managers, defer |
| Poor error messages | "Error occurred" unhelpful | Include context and action |
| Ignoring async errors | Unhandled promise rejections | Use .catch() or try-catch |

## Implementation Checklist

When implementing error handling:

- [ ] Define custom exception hierarchy for application
- [ ] Use specific exception types, not generic Exception
- [ ] Include error codes for programmatic handling
- [ ] Add context (user_id, request_id, etc.) to errors
- [ ] Implement retry logic for transient failures
- [ ] Add circuit breakers for external services
- [ ] Provide graceful degradation where possible
- [ ] Validate at system boundaries (input, external APIs)
- [ ] Clean up resources in finally blocks
- [ ] Log errors with appropriate level and context

## Additional Resources

### Reference Files

For detailed language-specific patterns, consult:

- **`references/patterns-by-language.md`** - Python, TypeScript, Rust, and Go error handling patterns with full code examples
