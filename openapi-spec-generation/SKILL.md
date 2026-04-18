---
name: openapi-spec-generation
description: Use when creating API specs, designing API contracts, writing swagger files, generating SDK clients, validating API schemas, or setting up API documentation portals. Also applies when the user mentions REST API design, API-first development, or asks "how should I document my API?" — even if they don't explicitly mention OpenAPI.
---

# OpenAPI Spec Generation

Generate and maintain OpenAPI 3.1 specifications for RESTful APIs following industry best practices.

## When to Use

- Creating API documentation from scratch
- Generating OpenAPI specs from existing code
- Designing API contracts (design-first approach)
- Validating API implementations against specs
- Generating client SDKs from specs
- Setting up API documentation portals

## Agent Workflow

Follow these steps when invoked:

### Step 1: Assess the Situation

1. **Check for existing specs** — Glob for `**/openapi.{yaml,yml,json}`, `**/swagger.{yaml,yml,json}`
2. **Identify the framework** — Read `package.json` or `pyproject.toml` to determine if the project uses FastAPI, Express/tsoa, NestJS, or another framework with OpenAPI support
3. **Find API routes** — Grep for route definitions (`@app.get`, `@Get`, `router.get`, `@Controller`) to understand the API surface
4. **Check for existing validation tools** — Look for `.spectral.yaml`, `redocly.yaml`, or linting configs

### Step 2: Choose the Approach

| Situation | Approach | Action |
| --- | --- | --- |
| No API code yet | Design-first | Write OpenAPI spec, then generate stubs |
| Existing API, no spec | Code-first | Add annotations/decorators, generate spec |
| Existing API + spec | Hybrid | Update spec to match implementation |
| Spec validation needed | Linting | Set up Spectral/Redocly (see `references/validation-config.md`) |

### Step 3: Implement

1. Use `examples/complete-api-spec.yaml` as a starting template for design-first specs
2. For code-first, reference `examples/fastapi-codegen.py` (Python) or `examples/tsoa-codegen.ts` (TypeScript)
3. For advanced patterns (pagination, webhooks, polymorphism), consult `references/advanced-patterns.md`
4. Set up validation tooling using `references/validation-config.md`

### Step 4: Validate

1. Run `spectral lint openapi.yaml` or `redocly lint openapi.yaml` to check for issues
2. Verify all endpoints have operationIds, security definitions, and error responses
3. Preview documentation with `redocly preview-docs openapi.yaml`

## Core Concepts

### OpenAPI 3.1 Structure

```yaml
openapi: 3.1.0
info:
  title: API Title
  version: 1.0.0
servers:
  - url: https://api.example.com/v1
paths:
  /resources:
    get: ...
components:
  schemas: ...
  securitySchemes: ...
```

### Design Approaches

| Approach         | Description                  | Best For            |
| ---------------- | ---------------------------- | ------------------- |
| **Design-First** | Write spec before code       | New APIs, contracts |
| **Code-First**   | Generate spec from code      | Existing APIs       |
| **Hybrid**       | Annotate code, generate spec | Evolving APIs       |

## Quick Reference

### Essential Spec Sections

| Section        | Purpose                          | Required |
| -------------- | -------------------------------- | -------- |
| `openapi`      | Spec version (use 3.1.0)         | Yes      |
| `info`         | API metadata (title, version)    | Yes      |
| `servers`      | Base URLs for environments       | Yes      |
| `paths`        | Endpoint definitions             | Yes      |
| `components`   | Reusable schemas, params, etc.   | No       |
| `security`     | Default authentication           | No       |
| `tags`         | Endpoint grouping                | No       |

### Common Schema Patterns

```yaml
# String with validation
name:
  type: string
  minLength: 1
  maxLength: 100

# Enum
status:
  type: string
  enum: [active, inactive, pending]

# Reference
user:
  $ref: "#/components/schemas/User"

# Array
items:
  type: array
  items:
    $ref: "#/components/schemas/Item"

# Nullable (OpenAPI 3.1 uses JSON Schema syntax)
avatar:
  type: ["string", "null"]
```

### Response Patterns

```yaml
responses:
  "200":
    description: Success
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/User"
  "400":
    $ref: "#/components/responses/BadRequest"
  "401":
    $ref: "#/components/responses/Unauthorized"
  "404":
    $ref: "#/components/responses/NotFound"
```

## Implementation Steps

### Design-First Approach

1. Define API requirements and resources
2. Write OpenAPI spec with endpoints and schemas
3. Validate spec with linting tools
4. Generate server stubs and client SDKs
5. Implement server logic
6. Keep spec and implementation in sync

### Code-First Approach

1. Annotate code with OpenAPI decorators/comments
2. Generate spec from code
3. Validate generated spec
4. Publish documentation

## Validation and Linting

```bash
# Install tools
npm install -g @stoplight/spectral-cli
npm install -g @redocly/cli

# Lint spec
spectral lint openapi.yaml

# Bundle and validate
redocly lint openapi.yaml
redocly bundle openapi.yaml -o bundled.yaml

# Preview documentation
redocly preview-docs openapi.yaml
```

## SDK Generation

```bash
# Install generator
npm install -g @openapitools/openapi-generator-cli

# TypeScript client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-fetch \
  -o ./generated/typescript-client

# Python client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./generated/python-client
```

## Best Practices

### Do's

- **Use $ref** - Reuse schemas, parameters, responses
- **Add examples** - Real-world values help consumers
- **Document errors** - All possible error codes
- **Version API** - In URL or header
- **Use semantic versioning** - For spec changes

### Don'ts

- **Don't use generic descriptions** - Be specific
- **Don't skip security** - Define all schemes
- **Don't forget nullable** - Be explicit about null
- **Don't mix styles** - Consistent naming throughout
- **Don't hardcode URLs** - Use server variables

## Additional Resources

### Templates

- **`examples/complete-api-spec.yaml`** - Full API specification template
- **`examples/fastapi-codegen.py`** - Python/FastAPI code-first example
- **`examples/tsoa-codegen.ts`** - TypeScript/Express code-first example

### Reference Files

- **`references/validation-config.md`** - Spectral and Redocly configuration
- **`references/advanced-patterns.md`** - Pagination, webhooks, polymorphism

### External Resources

- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [Swagger Editor](https://editor.swagger.io/)
- [Redocly](https://redocly.com/)
- [Spectral](https://stoplight.io/open-source/spectral)
