---
name: openapi-spec-generation
description: Generate and maintain OpenAPI 3.1 specs — design-first specs, code-first generation from FastAPI/tsoa/NestJS, validation with Spectral/Redocly, and SDK codegen. Use when creating API specs, designing API contracts, writing swagger files, generating SDK clients, validating API schemas, setting up API documentation portals, or when the user just says "document my API" or "give me a swagger file" — even without explicitly mentioning OpenAPI.
---

# OpenAPI Spec Generation

Treat the spec as the contract. Lint it, generate from it, and keep one source of truth.

## Decision guide

| Situation                          | Approach     | First action                                        |
| ---------------------------------- | ------------ | --------------------------------------------------- |
| No API code yet                    | Design-first | Write spec from `examples/complete-api-spec.yaml`, then generate stubs |
| Existing API, no spec              | Code-first   | Annotate handlers (FastAPI / tsoa / NestJS), emit spec at build |
| Existing API + spec, drift         | Hybrid       | Re-run codegen and diff; fix the side that's behind |
| Spec exists, no validation in CI   | Lint setup   | Add Spectral or Redocly — see `references/validation-config.md` |
| Need a TS or Python client         | SDK gen      | `openapi-generator-cli` — see `references/code-generation.md` |

## Quick orientation

Before writing or editing a spec:

1. **Glob** `**/openapi.{yaml,yml,json}` and `**/swagger.{yaml,yml,json}` — don't recreate what's already there.
2. **Identify the framework** from `package.json` / `pyproject.toml` — `fastapi`, `tsoa`, `@nestjs/swagger`, `springdoc-openapi` all change the approach.
3. **Find route definitions** (`@app.get`, `@Get`, `router.get`, `@Controller`) to understand the actual surface.
4. **Check for `.spectral.yaml` or `redocly.yaml`** — match the project's existing rules.

## Spec skeleton

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

| Section            | Purpose                              | Required |
| ------------------ | ------------------------------------ | -------- |
| `openapi`          | Spec version (use `3.1.0`)           | Yes      |
| `info`             | Title + version                      | Yes      |
| `servers`          | Base URLs per environment            | Yes      |
| `paths`            | Endpoint definitions                 | Yes      |
| `components`       | Reusable schemas, params, responses  | No       |
| `security`         | Default authentication               | No       |
| `tags`             | Endpoint grouping for docs           | No       |

## Best practices

- **Use `$ref`** — duplicating a schema in two endpoints guarantees they drift.
- **Document errors** — every endpoint needs `4xx` responses, not just `200`.
- **Add `examples`** — they appear in docs and feed contract tests.
- **Be explicit about null** — OpenAPI 3.1 uses `type: ["string", "null"]`, not the old `nullable: true`.
- **Pick one naming style** (camelCase or snake_case) and enforce with Spectral.
- **Bump `info.version`** on every breaking change.

## Common pitfalls

| Pitfall                          | Fix                                                      |
| -------------------------------- | -------------------------------------------------------- |
| No `operationId` on operations   | Required for code generators to name functions           |
| Generic `description` strings    | Be specific — these become the SDK's docstrings          |
| Hardcoded URLs                   | Use `servers` with variables                             |
| Missing security scheme          | Define in `components.securitySchemes`, apply globally   |
| Mixed naming styles              | Lint with Spectral's casing rules                        |
| Hand-editing generated code      | Re-run codegen instead; track the spec, not the output   |

## References — load on demand

| File                                  | Load when                                                              |
| ------------------------------------- | ---------------------------------------------------------------------- |
| `references/validation-config.md`     | Setting up Spectral/Redocly, CI lint, common rule violations           |
| `references/schema-composition.md`    | Reusable schemas, polymorphism (`oneOf`/`allOf`/`discriminator`), file upload bodies |
| `references/pagination.md`            | Designing list endpoints — offset vs cursor                            |
| `references/webhooks-and-async.md`    | Webhook events, batch operations, long-running 202+polling             |
| `references/auth-and-versioning.md`   | Security schemes (Bearer/API key/OAuth), URL/header versioning         |
| `references/code-generation.md`       | SDK generation, framework codegen tools, CI regen workflows            |

## Examples

| File                                | Use as                                                            |
| ----------------------------------- | ----------------------------------------------------------------- |
| `examples/complete-api-spec.yaml`   | Starting template for a design-first spec                         |
| `examples/fastapi-codegen.py`       | Code-first reference for Python / FastAPI                         |
| `examples/tsoa-codegen.ts`          | Code-first reference for TypeScript / Express + tsoa              |

## Related skills

- `api-design-principles` — REST contract design that informs what the spec should contain
- `microservices-patterns` — contract-first APIs across services
- `error-handling-patterns` — error response shapes referenced from the spec

## Further reading

- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [Swagger Editor](https://editor.swagger.io/)
- [Redocly](https://redocly.com/)
- [Spectral](https://stoplight.io/open-source/spectral)
