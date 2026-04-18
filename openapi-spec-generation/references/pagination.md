# Pagination Patterns

Choose the strategy first, then apply the right shape. Mixing styles inside one API forces every consumer to special-case endpoints.

| Strategy   | Use when                                            | Trade-off                                            |
| ---------- | --------------------------------------------------- | ---------------------------------------------------- |
| **Offset** | Bounded result sets, UI needs jump-to-page          | Slow on deep pages; drift if data mutates mid-scan   |
| **Cursor** | Streams, large/unbounded sets, append-only feeds    | No jump-to-page; cursor must be opaque to clients    |

## Offset-based

```yaml
paths:
  /users:
    get:
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: "#/components/schemas/User"
                  pagination:
                    type: object
                    properties:
                      page:
                        type: integer
                      limit:
                        type: integer
                      total:
                        type: integer
                      totalPages:
                        type: integer
                      hasNext:
                        type: boolean
                      hasPrev:
                        type: boolean
```

## Cursor-based

```yaml
paths:
  /events:
    get:
      parameters:
        - name: cursor
          in: query
          description: Opaque cursor returned by the previous response
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: "#/components/schemas/Event"
                  pagination:
                    type: object
                    properties:
                      nextCursor:
                        type: ["string", "null"]
                      hasMore:
                        type: boolean
```

## Rules

- **Always cap `limit`** with `maximum`. Unbounded `limit=10000` queries are a denial-of-service vector.
- **Always include both `data` and `pagination` envelopes** — clients then have one consistent shape across endpoints.
- **Cursors are opaque strings**, not encoded IDs the client can introspect or fabricate.
