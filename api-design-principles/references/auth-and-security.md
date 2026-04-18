# API Authentication & Security

Covers authentication schemes, authorization models, token lifecycle, and the OWASP API Top 10 pitfalls every API designer must handle.

## Authentication Schemes

### Bearer Tokens (JWT)

Most common for modern APIs. Stateless — token itself carries claims.

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

bearer = HTTPBearer()
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

async def current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return payload

@app.get("/api/me")
async def me(user: dict = Depends(current_user)):
    return user
```

JWT claims to include:

- `sub`: subject (user ID)
- `iss`: issuer
- `aud`: audience (which API)
- `exp`: expiration (short — 5–15 min for access tokens)
- `iat`: issued at
- `scope` or `permissions`: what the token authorizes

### API Keys

For server-to-server or simple partner integrations.

```http
X-API-Key: sk_live_abc123...
```

- Generate keys with high entropy (32+ bytes random).
- Store hashed (SHA-256 or bcrypt), never plain.
- Support key rotation and revocation.
- Scope keys to specific operations.

### OAuth 2.0 Flows

| Flow | Use case |
|------|----------|
| Authorization Code + PKCE | Web/mobile apps with user login |
| Client Credentials | Server-to-server, no user context |
| Device Code | CLIs, TVs, constrained devices |
| Refresh Token | Long-lived session without re-auth |

Prefer Authorization Code + PKCE over Implicit (deprecated). Never use Resource Owner Password Credentials for new designs.

### Session Cookies

For same-origin browser apps. Require: `HttpOnly`, `Secure`, `SameSite=Lax` (or `Strict`), CSRF protection.

## Authorization Models

### Scopes

Token carries scopes; each endpoint requires specific scopes.

```python
def require_scope(scope: str):
    async def checker(user: dict = Depends(current_user)):
        if scope not in user.get("scope", "").split():
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing scope: {scope}")
        return user
    return checker

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, user=Depends(require_scope("users:delete"))):
    ...
```

### RBAC (Role-Based Access Control)

Users have roles; roles grant permissions. Simple, coarse-grained.

```python
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

def require_role(*roles: Role):
    async def checker(user: dict = Depends(current_user)):
        if user.get("role") not in [r.value for r in roles]:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        return user
    return checker
```

### ABAC (Attribute-Based Access Control)

Evaluate policy against attributes of user, resource, and environment. Fine-grained, more complex.

```python
async def can_edit_post(user: dict, post: Post) -> bool:
    if user["role"] == "admin":
        return True
    if post.author_id == user["sub"]:
        return True
    if user["role"] == "editor" and post.status == "draft":
        return True
    return False
```

### Object-Level Authorization (Critical)

OWASP #1. Always verify the authenticated user is allowed to access the *specific* resource, not just the endpoint.

```python
# WRONG — only checks authentication
@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, user=Depends(current_user)):
    return await db.orders.find_one({"id": order_id})  # IDOR vulnerability

# RIGHT — checks ownership
@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, user=Depends(current_user)):
    order = await db.orders.find_one({"id": order_id})
    if not order or order["user_id"] != user["sub"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND)  # 404 not 403 to avoid leaking existence
    return order
```

## Token Lifecycle

### Expiration Strategy

- **Access tokens**: short-lived (5–15 minutes). Contains full claims.
- **Refresh tokens**: long-lived (days/weeks). Opaque, stored in DB, single-use (rotate on use).
- **Revocation**: maintain a denylist of revoked token IDs (`jti` claim), checked on each request. Or keep tokens short enough that revocation delay is acceptable.

### Refresh Flow

```text
POST /api/auth/refresh
Body: { "refresh_token": "..." }

Response:
{
  "access_token": "...",    // new short-lived token
  "refresh_token": "...",   // new refresh token (rotation)
  "expires_in": 900
}
```

Always rotate refresh tokens on use — detects theft when the old one is reused.

## GraphQL-Specific Auth

### Field-Level Authorization

```graphql
type User {
  id: ID!
  name: String!
  email: String!          # visible to anyone
  ssn: String @auth(role: OWNER)  # field-level
  salary: Int @auth(role: ADMIN)
}
```

```python
# Resolver approach
async def resolve_ssn(user, info):
    requester = info.context["user"]
    if requester["sub"] != user["id"]:
        return None  # or raise ForbiddenError
    return user["ssn"]
```

### Query Complexity as Security

Limit query depth and complexity to prevent expensive queries used for DoS.

## OWASP API Top 10 — Quick Reference

| # | Risk | Mitigation |
|---|------|------------|
| 1 | Broken Object-Level Authorization (BOLA) | Check ownership for every resource access |
| 2 | Broken Authentication | Strong auth; short-lived tokens; rate-limit login |
| 3 | Broken Object Property Level Auth | Whitelist writable fields; filter readable fields |
| 4 | Unrestricted Resource Consumption | Rate limits, pagination caps, timeouts, payload size limits |
| 5 | Broken Function-Level Authorization | Separate admin endpoints; role checks per endpoint |
| 6 | Unrestricted Access to Sensitive Flows | Rate-limit registration, password reset, checkout |
| 7 | Server-Side Request Forgery | Validate and allowlist outbound URLs |
| 8 | Security Misconfiguration | No debug in prod; least-privilege CORS; security headers |
| 9 | Improper Inventory Management | Track versions; retire old APIs; document all endpoints |
| 10 | Unsafe Consumption of APIs | Treat upstream APIs as untrusted; validate their responses |

## Rate Limiting as Security

Limits should be per-principal (user, API key, IP), not just global.

```python
# Per-endpoint tighter limits for sensitive flows
@app.post("/api/auth/login", dependencies=[Depends(rate_limit(5, per=60))])
@app.post("/api/auth/reset-password", dependencies=[Depends(rate_limit(3, per=300))])
```

Return `429 Too Many Requests` with `Retry-After` header.

## Transport Security

- HTTPS only. Redirect HTTP → HTTPS. HSTS header on all responses.
- TLS 1.2+ minimum; prefer TLS 1.3.
- Strong cipher suites; no export-grade ciphers.

## Security Headers

```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    return response
```

## CORS

Be restrictive. Default to allowlist.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],   # never "*" with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)
```

## Secrets Handling

- Never in URLs (logged everywhere). Use headers or body.
- Never in API responses, logs, or error messages.
- Use a secret manager (AWS Secrets Manager, Vault) — not env vars baked into images.
- Rotate regularly and support rotation without downtime (accept old + new during transition).

## Input Validation

- Validate at the boundary (request schema); never trust client input downstream.
- Use allowlist validation (enum, regex) over blocklist.
- Reject unknown fields or ignore them — never blindly pass through.
- Limit string lengths, numeric ranges, array sizes.

## Common Pitfalls

- **IDOR**: endpoint checks auth but not ownership.
- **Mass assignment**: PATCH body includes `is_admin: true` that silently updates.
- **Timing attacks**: string-compare credentials with `hmac.compare_digest`, not `==`.
- **JWT `none` algorithm**: always pin `algorithms=[...]` on decode.
- **Privilege escalation through refresh**: new access token must re-check current user permissions, not just trust the old claims.
- **Leaky errors**: 404 vs 403 can reveal whether a resource exists. For unauthorized access to existing resources, return 404.
- **Missing auth on new endpoints**: default to requiring auth; opt-in to public.
