---
name: logging-standards
description: Design structured logs that are queryable in production — wide events / canonical log lines, high-cardinality fields, tail sampling, PII redaction, log levels. Use when adding, reviewing, or improving logging, designing log schemas, setting up observability, or when the user just says "add some logging" or "I need better logs."
---

# Logging Standards

Turn logs from scattered debug strings into production analytics. Optimize for **reading** (querying during incidents), not writing.

Based on the [Logging Sucks](https://loggingsucks.com/) manifesto and canonical-log-line patterns from Stripe and Honeycomb.

## Core insight: wide events

One rich structured event per request, emitted once at completion — not many `logger.info()` calls scattered through the handler.

| Approach       | How it reads                       |
| -------------- | ---------------------------------- |
| Scattered logs | grep archaeology across N lines    |
| Wide events    | one row per request; SQL-queryable |

## Decision guide

- **Structured, not strings** — key-value JSON. A field is queryable; a `%s` message is not.
- **High cardinality, always** — `user_id`, `request_id`, `order_id`. Columnar stores (ClickHouse, BigQuery) handle it fine.
- **Build context through the request; emit once at the end** — middleware opens it, handlers add fields, a `finally` emits.
- **Tail-sample, never head-sample** — you don't know at request start if it will fail or be slow.
- **Levels**: `ERROR` for failures needing attention, `WARN` for degraded-but-recovered, `INFO` for the wide event itself. Never `DEBUG` in production.

## Essential fields

Group into these buckets — don't ship a new service missing a bucket:

| Bucket      | Fields                                                          |
| ----------- | --------------------------------------------------------------- |
| Correlation | `timestamp`, `request_id`, `trace_id`, `service`, `environment` |
| User        | `user_id`, `user_tier`, `user_ltv`                              |
| HTTP        | `endpoint`, `http_method`, `http_status`                        |
| Performance | `duration_ms`, `db_queries`, `db_duration_ms`, `cache_hits`     |
| Business    | Domain-specific: `cart_total`, `item_count`, `coupon_code`      |
| Error       | `error_code`, `error_message`, `error_retry_count`              |

## Sampling rules

Tail-sample — decide at the end when the outcome is known.

| Keep 100%                      | Sample 1–5%                    |
| ------------------------------ | ------------------------------ |
| Any non-2xx response           | Successful requests under p99  |
| Duration above p99             | Non-VIP users on fast paths    |
| Premium / enterprise users     | Standard background jobs       |
| Security & feature-flag events | —                              |

See `references/sampling.md` for implementation and head-vs-tail trade-offs.

## Sensitive data — never log

Passwords, API keys, tokens, full PAN / credit cards, SSN, unencrypted PII. Redact by key-name allowlist; hash identifiers with a salt when correlation matters. See `references/redaction.md`.

## Anti-patterns

| Pitfall                               | Fix                                        |
| ------------------------------------- | ------------------------------------------ |
| `logger.info(f"user {id} ...")`       | structured fields: `extra={"user_id": id}` |
| Scattered logs per request            | one wide event at the end                  |
| `DEBUG` enabled in production         | `INFO` minimum                             |
| Low-cardinality only (level, service) | add `user_id`, `request_id`, `trace_id`    |
| Synchronous HTTP log shipping         | async / buffered emit                      |
| Logging raw PII                       | redact / hash                              |

## Query examples

Design fields so these queries work:

```sql
-- Premium-user failures this hour
SELECT * FROM logs
WHERE error_code IS NOT NULL
  AND user_tier = 'premium'
  AND timestamp > NOW() - INTERVAL '1 hour';

-- P99 by endpoint
SELECT endpoint, percentile_cont(0.99) WITHIN GROUP (ORDER BY duration_ms)
FROM logs GROUP BY endpoint;
```

If a needed query can't be written against the schema, a field is missing.

## References — load on demand

| File                       | Load when                                               |
| -------------------------- | ------------------------------------------------------- |
| `references/python.md`     | Python logging — `structlog`, stdlib, FastAPI, async    |
| `references/typescript.md` | Node logging — `pino`, Express middleware               |
| `references/go.md`         | Go logging — `zerolog`, context propagation             |
| `references/sampling.md`   | Tail-sampling implementation, head-vs-tail trade-offs   |
| `references/redaction.md`  | PII masking, field allowlists, ID hashing               |

## Related skills

- `error-handling-patterns` — so errors carry structured context into logs
- `debugging-strategies` — using logs to investigate incidents
- `microservices-patterns` — trace propagation across services

## Further reading

- [loggingsucks.com](https://loggingsucks.com/) — the manifesto
- [Canonical log lines at Stripe](https://stripe.com/blog/canonical-log-lines)
- [Observability Engineering (O'Reilly)](https://www.oreilly.com/library/view/observability-engineering/9781492076438/)
