# Authentication and Versioning

Security schemes and version-rollout strategies.

## Security schemes

Define every supported auth method in `components.securitySchemes`, then apply globally or per-operation.

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

    apiKey:
      type: apiKey
      in: header
      name: X-API-Key

    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          scopes:
            read:users: Read user data
            write:users: Create and update users
            delete:users: Delete users

# Top-level: accept JWT OR API key for every endpoint
security:
  - bearerAuth: []
  - apiKey: []

# Per-operation: require OAuth with a specific scope
paths:
  /admin/users:
    delete:
      security:
        - oauth2: [delete:users]
```

### Reading the `security` array

- **List of objects** = OR (any one satisfies the requirement)
- **Multiple keys inside one object** = AND (all required together)

```yaml
# OR — bearer OR apiKey works
security:
  - bearerAuth: []
  - apiKey: []

# AND — both required
security:
  - bearerAuth: []
    apiKey: []
```

## Versioning strategies

| Strategy        | Pros                                   | Cons                                       |
| --------------- | -------------------------------------- | ------------------------------------------ |
| **URL path**    | Visible, cacheable, easy to route      | Forces clients to change URLs on upgrade   |
| **Header**      | Stable URLs, finer-grained per-request | Invisible in logs, harder for caches/CDNs  |
| **Date-based**  | Encodes contract changes precisely     | Requires server-side dispatch table        |

### URL path versioning

```yaml
servers:
  - url: https://api.example.com/v1
    description: Version 1
  - url: https://api.example.com/v2
    description: Version 2

paths:
  /users:
    # v1 and v2 may have different schemas — keep them in separate spec files
```

### Header versioning

```yaml
paths:
  /users:
    get:
      parameters:
        - name: X-API-Version
          in: header
          required: false
          schema:
            type: string
            enum: ["2024-01-01", "2024-06-01"]
            default: "2024-01-01"
```

## Rules

- **Define every scheme in one place** — duplicating `securitySchemes` across paths is invalid.
- **Document scopes as full sentences** — they often surface in OAuth consent screens.
- **Bump `info.version` on every breaking change** — Spectral can fail CI when contract changes don't bump it.
- **Keep at least one prior version live** until usage drops below your sunset threshold; document the deprecation date in `description`.
