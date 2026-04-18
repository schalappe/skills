# TypeScript / Node Logging

Wide-event implementation with `pino` and `AsyncLocalStorage`. Load when adding structured logging to a Node.js service.

## Pino with AsyncLocalStorage

`AsyncLocalStorage` carries the request context across `await` boundaries without threading it through every function signature.

```typescript
import { AsyncLocalStorage } from "async_hooks";
import pino from "pino";

const requestContext = new AsyncLocalStorage<Map<string, unknown>>();

const logger = pino({
  level: "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  mixin() {
    // Merge request context into every log line
    const ctx = requestContext.getStore();
    return ctx ? Object.fromEntries(ctx) : {};
  },
});

class RequestLogger {
  private startTime: number;
  public context: Map<string, unknown>;

  constructor(requestId: string, service: string) {
    this.startTime = Date.now();
    this.context = new Map<string, unknown>([
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
```

## Express middleware

Open the context on `req`, attach it for handlers to enrich, emit on `res.end`.

```typescript
import { NextFunction, Request, Response } from "express";
import { v4 as uuidv4 } from "uuid";

declare module "express-serve-static-core" {
  interface Request {
    logContext?: RequestLogger;
  }
}

export function wideEventMiddleware(req: Request, res: Response, next: NextFunction): void {
  const requestId = (req.headers["x-request-id"] as string) ?? uuidv4();
  const ctx = new RequestLogger(requestId, "my-service");

  ctx.add({
    endpoint: req.path,
    http_method: req.method,
    client_ip: req.ip,
  });

  req.logContext = ctx;

  const originalEnd = res.end.bind(res);
  res.end = function (...args: unknown[]) {
    ctx.add({ http_status: res.statusCode });
    ctx.emit();
    return originalEnd(...(args as Parameters<typeof originalEnd>));
  } as typeof res.end;

  requestContext.run(ctx.context, () => next());
}
```
