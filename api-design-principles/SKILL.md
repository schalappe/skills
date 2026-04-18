---
name: api-design-principles
description: Use when designing REST or GraphQL APIs, building API endpoints, structuring routes, designing request/response schemas, choosing between REST and GraphQL, implementing pagination or filtering, reviewing API specifications, or planning API versioning — even if the user doesn't explicitly say "API design."
---

# API Design Principles

Design intuitive, scalable REST and GraphQL APIs using resource-oriented patterns, proper HTTP semantics, and consistent error handling.

## Core Concepts

### 1. RESTful Design Principles

- Resources are nouns (users, orders, products), not verbs
- Use HTTP methods for actions: GET (retrieve, idempotent), POST (create), PUT (replace, idempotent), PATCH (partial update), DELETE (remove, idempotent)
- URLs represent resource hierarchies
- Consistent naming conventions (plural nouns for collections)

### 2. GraphQL Design Principles

- Types define your domain model (schema-first development)
- Queries for reading, mutations for modifying, subscriptions for real-time
- Clients request exactly what they need from a single endpoint
- Strongly typed schema with built-in introspection

### 3. API Versioning Strategies

**URL Versioning:**

```text
/api/v1/users
/api/v2/users
```

**Header Versioning:**

```text
Accept: application/vnd.api+json; version=1
```

**Query Parameter Versioning:**

```text
/api/users?version=1
```

## REST API Design Patterns

### Pattern 1: Resource Collection Design

```python
# Good: Resource-oriented endpoints
GET    /api/users              # List users (with pagination)
POST   /api/users              # Create user
GET    /api/users/{id}         # Get specific user
PUT    /api/users/{id}         # Replace user
PATCH  /api/users/{id}         # Update user fields
DELETE /api/users/{id}         # Delete user

# Nested resources
GET    /api/users/{id}/orders  # Get user's orders
POST   /api/users/{id}/orders  # Create order for user

# Bad: Action-oriented endpoints (avoid)
POST   /api/createUser
POST   /api/getUserById
POST   /api/deleteUser
```

### Pattern 2: Pagination and Filtering

Use offset-based pagination for simple cases and cursor-based pagination for large or real-time datasets.
Always enforce a default page size and a maximum page size.
See `references/rest-best-practices.md` for complete pagination patterns including offset-based, cursor-based, and Link header approaches.

### Pattern 3: Error Handling and Status Codes

```python
from fastapi import HTTPException, status
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str
    path: str

class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    value: Any

# Consistent error responses
STATUS_CODES = {
    "success": 200,
    "created": 201,
    "no_content": 204,
    "bad_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "unprocessable": 422,
    "internal_error": 500
}

def raise_not_found(resource: str, id: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "NotFound",
            "message": f"{resource} not found",
            "details": {"id": id}
        }
    )

def raise_validation_error(errors: List[ValidationErrorDetail]):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": {"errors": [e.dict() for e in errors]}
        }
    )

# Example usage
@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = await fetch_user(user_id)
    if not user:
        raise_not_found("User", user_id)
    return user
```

### Pattern 4: HATEOAS (Hypermedia as the Engine of Application State)

```python
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    _links: dict

    @classmethod
    def from_user(cls, user: User, base_url: str):
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            _links={
                "self": {"href": f"{base_url}/api/users/{user.id}"},
                "orders": {"href": f"{base_url}/api/users/{user.id}/orders"},
                "update": {
                    "href": f"{base_url}/api/users/{user.id}",
                    "method": "PATCH"
                },
                "delete": {
                    "href": f"{base_url}/api/users/{user.id}",
                    "method": "DELETE"
                }
            }
        )
```

## GraphQL Design Patterns

GraphQL APIs follow a schema-first approach where types define the domain model. Key patterns:

- **Schema design**: Define types, queries, mutations, and subscriptions. Use Relay-style cursor pagination for connections. See `references/graphql-schema-design.md` for complete schema patterns.
- **Resolver design**: Resolve fields with async functions. Use Input/Payload pattern for mutations (accept `CreateXInput`, return `CreateXPayload` with optional errors).
- **DataLoader**: Batch and cache data fetches to prevent the N+1 query problem. Every relationship field should use a DataLoader.

For resolver implementation, DataLoader setup, and complete schema examples, see `references/graphql-schema-design.md`.

## Best Practices

### REST APIs

1. **Consistent Naming**: Use plural nouns for collections (`/users`, not `/user`)
2. **Stateless**: Each request contains all necessary information
3. **Use HTTP Status Codes Correctly**: 2xx success, 4xx client errors, 5xx server errors
4. **Version Your API**: Plan for breaking changes from day one
5. **Pagination**: Always paginate large collections
6. **Rate Limiting**: Protect your API with rate limits
7. **Documentation**: Use OpenAPI/Swagger for interactive docs

### GraphQL APIs

1. **Schema First**: Design schema before writing resolvers
2. **Avoid N+1**: Use DataLoaders for efficient data fetching
3. **Input Validation**: Validate at schema and resolver levels
4. **Error Handling**: Return structured errors in mutation payloads
5. **Pagination**: Use cursor-based pagination (Relay spec)
6. **Deprecation**: Use `@deprecated` directive for gradual migration
7. **Monitoring**: Track query complexity and execution time

## Common Pitfalls

- **Over-fetching/Under-fetching (REST)**: Fixed in GraphQL but requires DataLoaders
- **Breaking Changes**: Version APIs or use deprecation strategies
- **Inconsistent Error Formats**: Standardize error responses
- **Missing Rate Limits**: APIs without limits are vulnerable to abuse
- **Poor Documentation**: Undocumented APIs frustrate developers
- **Ignoring HTTP Semantics**: POST for idempotent operations breaks expectations
- **Tight Coupling**: API structure shouldn't mirror database schema

## Resources

- **`references/rest-best-practices.md`**: Comprehensive REST API design guide
- **`references/graphql-schema-design.md`**: GraphQL schema patterns and anti-patterns
- **`assets/rest-api-template.py`**: FastAPI REST API template
- **`assets/api-design-checklist.md`**: Pre-implementation review checklist

## Related Skills

- **microservices-patterns**: When your API serves a microservices architecture — covers service decomposition, inter-service communication, and resilience patterns
- **saga-orchestration**: When your API triggers distributed transactions across multiple services — covers orchestration and choreography patterns with compensating actions
