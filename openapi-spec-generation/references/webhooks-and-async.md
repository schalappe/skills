# Webhooks, Batch, and Long-Running Operations

Patterns for work that doesn't fit the synchronous request/response shape.

## Webhooks (OpenAPI 3.1)

`webhooks` is a top-level keyword introduced in 3.1. Each entry describes a request your server **sends** to the consumer, not one it receives.

```yaml
webhooks:
  userCreated:
    post:
      summary: User created event
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserCreatedEvent"
      responses:
        "200":
          description: Webhook processed successfully

  userUpdated:
    post:
      summary: User updated event
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserUpdatedEvent"
      responses:
        "200":
          description: Webhook processed successfully

components:
  schemas:
    WebhookEvent:
      type: object
      required: [id, type, timestamp, data]
      properties:
        id:
          type: string
          format: uuid
        type:
          type: string
        timestamp:
          type: string
          format: date-time
        data:
          type: object

    UserCreatedEvent:
      allOf:
        - $ref: "#/components/schemas/WebhookEvent"
        - type: object
          properties:
            type:
              const: user.created
            data:
              $ref: "#/components/schemas/User"
```

### Signature header

Document signing so consumers can verify authenticity:

```yaml
components:
  headers:
    X-Webhook-Signature:
      description: HMAC-SHA256 signature of the request body
      schema:
        type: string
      example: "sha256=abc123..."
```

## Batch operations

Limit batch sizes — `maxItems` prevents one caller from monopolizing a worker.

```yaml
paths:
  /users/batch:
    post:
      operationId: batchCreateUsers
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [users]
              properties:
                users:
                  type: array
                  items:
                    $ref: "#/components/schemas/CreateUserRequest"
                  minItems: 1
                  maxItems: 100
      responses:
        "200":
          description: Batch results — partial success is allowed
          content:
            application/json:
              schema:
                type: object
                properties:
                  successful:
                    type: array
                    items:
                      $ref: "#/components/schemas/User"
                  failed:
                    type: array
                    items:
                      type: object
                      properties:
                        index:
                          type: integer
                        error:
                          $ref: "#/components/schemas/Error"
```

Return **207-style envelopes** with `successful` + `failed` arrays. Don't fail the whole batch on one bad row unless the contract explicitly says so.

## Long-running operations

Return `202 Accepted` with a `Location` header pointing to a polling endpoint.

```yaml
paths:
  /reports:
    post:
      operationId: generateReport
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ReportRequest"
      responses:
        "202":
          description: Report generation started
          headers:
            Location:
              description: URL to poll for status
              schema:
                type: string
                format: uri
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AsyncOperation"

  /operations/{operationId}:
    get:
      operationId: getOperationStatus
      parameters:
        - name: operationId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          description: Operation status
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AsyncOperation"

components:
  schemas:
    AsyncOperation:
      type: object
      required: [id, status, createdAt]
      properties:
        id:
          type: string
          format: uuid
        status:
          type: string
          enum: [pending, processing, completed, failed]
        progress:
          type: integer
          minimum: 0
          maximum: 100
        result:
          oneOf:
            - type: object
            - type: "null"
        error:
          oneOf:
            - $ref: "#/components/schemas/Error"
            - type: "null"
        createdAt:
          type: string
          format: date-time
        completedAt:
          type: ["string", "null"]
          format: date-time
```

## Rules

- **Async = idempotency keys.** Network retries on POST will duplicate work without them.
- **Webhooks need retries with backoff** — document the schedule in `description` so consumers know what to expect.
- **Status enums should be closed sets** (`enum:`) — never free-form strings.
