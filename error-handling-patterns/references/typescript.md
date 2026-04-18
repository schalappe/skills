# TypeScript Error Handling

## Result type

Make failure part of the return type instead of a thrown exception. The discriminated union forces exhaustive handling at call sites.

```typescript
export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export const Ok  = <T>(value: T): Result<T, never> => ({ ok: true,  value });
export const Err = <E>(error: E): Result<never, E> => ({ ok: false, error });

export function parseJSON<T>(json: string): Result<T, SyntaxError> {
  try {
    return Ok(JSON.parse(json) as T);
  } catch (error) {
    return Err(error as SyntaxError);
  }
}

// Chaining
export function chain<T, U, E>(
  r: Result<T, E>,
  fn: (value: T) => Result<U, E>,
): Result<U, E> {
  return r.ok ? fn(r.value) : r;
}

export function map<T, U, E>(
  r: Result<T, E>,
  fn: (value: T) => U,
): Result<U, E> {
  return r.ok ? Ok(fn(r.value)) : r;
}
```

## Custom Error classes

Subclass `Error`, set `name`, capture the stack, and implement `toJSON` so structured logs survive serialization across service boundaries.

```typescript
export class ApplicationError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace?.(this, this.constructor);
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      details: this.details,
    };
  }
}

export class ValidationError extends ApplicationError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, "VALIDATION_ERROR", 400, details);
  }
}

export class NotFoundError extends ApplicationError {
  constructor(resource: string, id: string) {
    super(`${resource} not found`, "NOT_FOUND", 404, { resource, id });
  }
}

export class UnauthorizedError extends ApplicationError {
  constructor(message = "Unauthorized") {
    super(message, "UNAUTHORIZED", 401);
  }
}
```

## Async boundary handler

Wrap async entry points so unexpected throws are coerced into a typed `ApplicationError`, and use `Promise.allSettled` for fan-out with partial success.

```typescript
export function asyncHandler<T extends unknown[], R>(
  fn: (...args: T) => Promise<R>,
): (...args: T) => Promise<R> {
  return async (...args: T): Promise<R> => {
    try {
      return await fn(...args);
    } catch (error) {
      if (error instanceof ApplicationError) throw error;
      throw new ApplicationError(
        error instanceof Error ? error.message : "Unknown error",
        "INTERNAL_ERROR",
      );
    }
  };
}

export async function fetchAllUsers(ids: string[]): Promise<User[]> {
  const results = await Promise.allSettled(ids.map(fetchUser));
  const users: User[] = [];
  const errors: unknown[] = [];
  for (const r of results) {
    r.status === "fulfilled" ? users.push(r.value) : errors.push(r.reason);
  }
  if (errors.length) console.error(`${errors.length} fetches failed`, errors);
  return users;
}
```

## See also

- `references/resilience.md` — retry, circuit breaker, aggregation in TS
