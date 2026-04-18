---
name: error-handling-patterns
description: Design error handling and fault tolerance — exception hierarchies, Result/Option types, retries, circuit breakers, error aggregation, graceful degradation. Use when adding try/catch, shaping custom exceptions, hardening external calls, improving error messages, or reviewing error flows — even for a one-line try/catch question.
---

# Error Handling Patterns

Build resilient applications by choosing the right error-handling strategy, preserving context, and failing in ways that are observable and recoverable.

## Decision guide

| Approach      | Use when                                             | Shape                  |
| ------------- | ---------------------------------------------------- | ---------------------- |
| Exceptions    | Unexpected conditions that propagate up naturally    | `try` / `catch`        |
| Result types  | Expected failures that belong in the function's type | `Result<T, E>`         |
| Option/Maybe  | Absence is normal, not an error                      | `Option<T>` / nullable |
| Panic / abort | Unrecoverable programmer bugs, broken invariants     | `panic!`, `assert`     |

## Error categories

- **Recoverable** — network timeouts, missing files, bad user input, rate limits. Retry, validate, or fall back.
- **Unrecoverable** — OOM, stack overflow, invariant violations. Let the process die with a clear message.

## Core patterns

Sketches below — full code lives in the references.

### Custom exception hierarchy

One base exception per application; subclass per domain concern; attach `code`, `details`, and a timestamp so handlers branch on type instead of matching on message strings.

### Retry with exponential backoff

Retry only idempotent operations or well-known transient failures. Cap attempts, multiply delay (`backoff_factor ** attempt`), add jitter to avoid thundering herds. See `references/resilience.md`.

### Circuit breaker

Three states — CLOSED / OPEN / HALF_OPEN — short-circuit calls to a failing dependency and probe recovery on a timer. Wrap every external service call on a hot path. See `references/resilience.md`.

### Error aggregation

Collect failures across a batch (form fields, bulk operations) and raise a single `AggregateError` so callers see everything at once. See `references/resilience.md`.

### Graceful degradation

On failure, serve a reduced but useful response (cached copy, empty list, feature flag off). Log the degradation so silent fallback doesn't become permanent invisible behavior.

### Result type

Make failure part of the return type, not a control-flow side channel. Forces callers to handle the error branch. See `references/typescript.md` or `references/rust.md`.

## Best practices

- **Fail fast** at boundaries (user input, external APIs); trust internal callers.
- **Preserve context** — chain causes (`raise ... from e`, `%w`, `.cause`), include request/user IDs.
- **Catch narrowly** — specific exception types, never bare `except:` / `catch (e)`.
- **Handle at the right layer** — the layer that can actually do something about it.
- **Clean up** — context managers, `defer`, `try/finally`, RAII.
- **Log once** — either log or re-throw, not both.
- **Meaningful messages** — what happened, which input, what to try next.

## Common pitfalls

| Pitfall                       | Fix                                            |
| ----------------------------- | ---------------------------------------------- |
| `except Exception` catch-all  | Narrow to the exact types you expect          |
| Empty catch block             | Log, re-throw, or document why silence is safe |
| Log + re-throw at every frame | Log once at the boundary that renders the error |
| Swallowed async rejections    | `await`, `.catch()`, or `Promise.allSettled`  |
| Generic "An error occurred"   | Include operation, inputs, and next step       |
| Resource leaks on error path  | Context managers / defer / finally            |

## References — load on demand

| File                         | Load when                                                          |
| ---------------------------- | ------------------------------------------------------------------ |
| `references/resilience.md`   | implementing retry, circuit breaker, aggregation, or fallback      |
| `references/python.md`       | Python exception hierarchies, context managers, cause chaining     |
| `references/typescript.md`   | Result types, custom Error classes, async boundary handlers        |
| `references/rust.md`         | custom error enums, `thiserror`/`anyhow`, `?` and combinators      |
| `references/go.md`           | sentinel errors, `errors.Is/As`, `%w` wrapping, `errgroup`         |

## Related skills

- `debugging-strategies` — investigate errors that escape handling
- `logging-standards` — structured logging so errors stay traceable
- `microservices-patterns` — bulkheads, timeouts, resilience across services
