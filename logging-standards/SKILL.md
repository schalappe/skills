---
name: logging-standards
description: Use when adding logging, improving log quality, implementing structured logging, setting up observability, or designing log schemas — even if the user just says "add some logging" or "I need better logs". Covers wide events, canonical log lines, structured logging, sampling strategies, and query-first design.
---

# Logging Standards

This skill provides modern logging standards that transform logs from scattered debug statements into queryable production analytics. Apply these principles when adding or improving logging to make debugging fast and effective.

## Origins & Attribution

This methodology is based on the **"Logging Sucks"** manifesto by [loggingsucks.com](https://loggingsucks.com/).

The core insight: traditional logging optimizes for *writing* (developer convenience) rather than *reading* (production debugging). The solution is **Wide Events** - also known as **Canonical Log Lines** - a pattern popularized by observability practitioners at companies like Honeycomb, Stripe, and other high-scale distributed systems operators.

Key influences:

| Source | Contribution |
|--------|--------------|
| [loggingsucks.com](https://loggingsucks.com/) | Core philosophy, wide events pattern, query-first mindset |
| Honeycomb.io | High-cardinality observability, tail sampling strategies |
| Charity Majors | Advocacy for structured observability over traditional logging |
| Stripe Engineering | Canonical log lines pattern in production systems |

## Core Philosophy: Query-First Logging

**Stop optimizing logs for writing. Start optimizing for reading.**

Traditional logging fails because:

- Logs are scattered across services with no coherent context
- String-based search treats logs as character bags with no structure
- The same user ID appears in 47 different formats across services
- Developers emit convenient statements without considering searchability

The solution: **Wide Events** (Canonical Log Lines) - a single comprehensive log entry per request per service containing rich contextual fields.

## Key Concepts

### Wide Events vs Scattered Logs

| Approach | Description | Queryability |
|----------|-------------|--------------|
| Scattered Logs | Multiple `logger.info()` calls throughout request | Poor - requires grep archaeology |
| Wide Events | Single rich event emitted at request completion | Excellent - enables analytics queries |

### Structured Logging

Always use key-value pairs (JSON), never unstructured text:

```python
# Bad: Unstructured text
logger.info(f"User {user_id} checkout failed: {error}")

# Good: Structured with context
logger.info("checkout_failed", extra={
    "user_id": user_id,
    "error_code": error.code,
    "cart_total": cart.total,
    "item_count": len(cart.items)
})
```

### Cardinality Matters

**High-cardinality fields** (many unique values) are more useful for debugging:

| Cardinality | Examples | Debugging Value |
|-------------|----------|-----------------|
| High | user_id, request_id, order_id | Excellent - pinpoints specific issues |
| Medium | endpoint, error_code, region | Good - helps filter and group |
| Low | http_method, log_level, service | Limited - too broad for debugging |

Modern columnar databases (ClickHouse, BigQuery) handle high-cardinality data efficiently.

## Wide Event Structure

Build a single event object as the request progresses, then emit once at completion:

### Essential Fields

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "request_id": "req_abc123",
  "trace_id": "trace_xyz789",
  "service": "checkout-service",
  "environment": "production",

  "user_id": "usr_456",
  "user_tier": "premium",
  "user_ltv": 2500.00,

  "endpoint": "/api/v1/checkout",
  "http_method": "POST",
  "http_status": 500,

  "duration_ms": 1234,
  "db_queries": 5,
  "db_duration_ms": 456,
  "cache_hits": 3,
  "cache_misses": 1,

  "cart_total": 149.99,
  "item_count": 3,
  "coupon_code": "SAVE20",
  "payment_method": "stripe",

  "error_code": "PAYMENT_DECLINED",
  "error_message": "Card declined by issuer",
  "error_retry_count": 2
}
```

### Field Categories

| Category | Fields | Purpose |
|----------|--------|---------|
| Request Metadata | timestamp, request_id, trace_id, service | Identify and correlate |
| User Context | user_id, user_tier, user_ltv | Prioritize VIP issues |
| HTTP Details | endpoint, method, status | Route and status |
| Performance | duration_ms, db_duration_ms, cache_* | Performance analysis |
| Business Data | cart_total, item_count, coupon_code | Business context |
| Error Details | error_code, error_message, stack_trace | Debug failures |

## Implementation Pattern

### Request Context Builder

Build context incrementally throughout the request lifecycle:

```python
class RequestContext:
    def __init__(self, request_id: str):
        self._data = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": settings.SERVICE_NAME,
        }

    def add(self, **fields):
        """Add fields to the event context."""
        self._data.update(fields)

    def emit(self, level: str = "info"):
        """Emit the wide event at request completion."""
        self._data["duration_ms"] = self._calculate_duration()
        logger.log(level, "request_completed", extra=self._data)
```

### Usage in Request Handler

```python
async def checkout_handler(request):
    ctx = RequestContext(request.id)
    ctx.add(user_id=request.user.id, user_tier=request.user.tier)

    try:
        cart = await get_cart(request.user.id)
        ctx.add(cart_total=cart.total, item_count=len(cart.items))

        result = await process_payment(cart)
        ctx.add(payment_method=result.method, http_status=200)

    except PaymentError as e:
        ctx.add(
            http_status=500,
            error_code=e.code,
            error_message=str(e)
        )
        raise

    finally:
        ctx.emit()  # Always emit, even on error
```

## Log Levels

Use levels strategically:

| Level | When to Use | Example |
|-------|-------------|---------|
| ERROR | Unexpected failures requiring attention | Payment processing failed |
| WARN | Degraded operation, recoverable issues | Cache miss, retry succeeded |
| INFO | Normal operations, request completion | Wide event at request end |
| DEBUG | Development-only, detailed tracing | Query parameters, internal state |

**In production**: INFO and above only. Never DEBUG.

## Sampling Strategy

Not all traffic needs full logging. Use **tail sampling**:

### Always Preserve (100%)

- Errors (any non-2xx response)
- Slow requests (above p99 latency)
- VIP users (premium tier, high LTV)
- Feature flag changes
- Security events

### Random Sample (1-5%)

- Successful requests within normal latency
- Non-VIP users
- Standard operations

```python
def should_sample(ctx: RequestContext) -> bool:
    # Always keep errors and slow requests
    if ctx.http_status >= 400:
        return True
    if ctx.duration_ms > P99_THRESHOLD:
        return True
    if ctx.user_tier == "premium":
        return True

    # Random sample the rest
    return random.random() < 0.05  # 5%
```

## Anti-Patterns to Avoid

### Never Do This

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Unstructured strings | Cannot query fields | Use structured JSON |
| Scattered logs | No coherent context | Use wide events |
| Debug in production | Noise, performance | INFO+ only |
| Low-cardinality only | Cannot pinpoint issues | Include user_id, request_id |
| Logging sensitive data | Security/compliance risk | Redact PII, secrets |
| Synchronous remote logging | Blocks requests | Async/buffered logging |

### Sensitive Data Handling

NEVER log:

- Passwords, API keys, tokens
- Full credit card numbers
- Social security numbers
- Unencrypted PII

ALWAYS:

- Mask or hash sensitive fields
- Use allowlists for loggable fields
- Audit log schemas regularly

## Query Examples

Design logs to answer these questions:

```sql
-- All checkout failures for premium users this hour
SELECT * FROM logs
WHERE error_code IS NOT NULL
  AND user_tier = 'premium'
  AND timestamp > NOW() - INTERVAL 1 HOUR;

-- P99 latency by endpoint
SELECT endpoint, PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms)
FROM logs
GROUP BY endpoint;

-- Users affected by payment errors
SELECT DISTINCT user_id, COUNT(*) as failures
FROM logs
WHERE error_code LIKE 'PAYMENT_%'
GROUP BY user_id
ORDER BY failures DESC;
```

## Implementation Checklist

When adding or improving logging:

1. **Structure** - Use JSON key-value pairs, never plain strings
2. **Context** - Include request_id, user_id, and business data
3. **Wide Events** - Build context throughout request, emit once at end
4. **Levels** - Use appropriate levels (INFO for normal, ERROR for failures)
5. **Sampling** - Preserve errors/VIPs, sample successful traffic
6. **Security** - Never log passwords, tokens, or PII
7. **Performance** - Use async logging, avoid blocking
8. **Queryability** - Design for SQL-style queries, not grep

## Related Skills

- **testing-standards** - Testing log output and observability

## Additional Resources

### Reference Files

For detailed patterns and examples, consult:

- **`references/patterns.md`** - Wide event patterns, logging library configurations, and language-specific examples

### Further Reading

External resources for deeper understanding:

| Resource | Description |
|----------|-------------|
| [loggingsucks.com](https://loggingsucks.com/) | Original manifesto on why traditional logging fails |
| [Observability Engineering (O'Reilly)](https://www.oreilly.com/library/view/observability-engineering/9781492076438/) | Comprehensive book on modern observability |
| [Canonical Log Lines at Stripe](https://stripe.com/blog/canonical-log-lines) | Stripe's implementation of wide events |
| [Honeycomb Blog](https://www.honeycomb.io/blog) | Practical observability patterns and case studies |
