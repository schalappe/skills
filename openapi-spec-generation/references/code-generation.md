# Code Generation

Generate clients and servers from a spec, or generate a spec from annotated code. Working framework examples live in `examples/fastapi-codegen.py` and `examples/tsoa-codegen.ts`.

## Spec → SDKs (design-first)

[`@openapitools/openapi-generator-cli`](https://openapi-generator.tech/) is the most language-coverage option.

```bash
# Install
npm install -g @openapitools/openapi-generator-cli

# TypeScript fetch client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-fetch \
  -o ./generated/typescript-client

# Python client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./generated/python-client

# Go client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g go \
  -o ./generated/go-client
```

### Common generator targets

| Generator              | Output                                       |
| ---------------------- | -------------------------------------------- |
| `typescript-fetch`     | TS client using browser/Node `fetch`         |
| `typescript-axios`     | TS client using axios                        |
| `python`               | Python client with `urllib3`                 |
| `python-pydantic-v1`   | Python client with Pydantic v1 models        |
| `go`                   | Go client                                    |
| `java`                 | Java client (multiple HTTP-lib variants)     |
| `spring`               | Spring Boot server stubs                     |
| `aspnetcore`           | ASP.NET Core server stubs                    |

### Tips

- **Pin the generator version** in CI — generators evolve and output churns silently.
- **Commit generated code** so reviewers see the diff when the spec changes.
- **`.openapi-generator-ignore`** — exclude files you've hand-edited from regeneration.

## Code → spec (code-first)

Annotate handlers; the framework emits the spec at build or runtime.

| Stack                 | Tool / library                                       | Output                          |
| --------------------- | ---------------------------------------------------- | ------------------------------- |
| Python / FastAPI      | Built-in (`/openapi.json`)                           | OpenAPI 3.1                     |
| Python / Flask        | `apispec`, `flask-smorest`                           | OpenAPI 3.x                     |
| Python / Django       | `drf-spectacular`                                    | OpenAPI 3.x                     |
| TypeScript / Express  | `tsoa`                                               | OpenAPI 3.x from TS decorators  |
| TypeScript / NestJS   | `@nestjs/swagger`                                    | OpenAPI 3.x                     |
| Go / net-http         | `swaggo/swag`                                        | OpenAPI 2.0 / 3.0               |
| Go / Gin              | `swaggo/gin-swagger`                                 | OpenAPI 2.0                     |
| Java / Spring Boot    | `springdoc-openapi`                                  | OpenAPI 3.x                     |
| .NET                  | `Swashbuckle.AspNetCore`                             | OpenAPI 3.x                     |

See `examples/fastapi-codegen.py` and `examples/tsoa-codegen.ts` for end-to-end examples.

## Hybrid: spec → server stubs

Generate stubs once, then implement the bodies. Re-generation is risky because it can stomp implementation; use `--skip-overwrite` or `.openapi-generator-ignore`.

```bash
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python-fastapi \
  -o ./server \
  --skip-overwrite
```

## CI integration

```yaml
# .github/workflows/sdk.yml
name: Regenerate SDK

on:
  push:
    paths: ["openapi.yaml"]

jobs:
  regen:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g @openapitools/openapi-generator-cli
      - run: openapi-generator-cli generate -i openapi.yaml -g typescript-fetch -o ./sdk/ts
      - uses: peter-evans/create-pull-request@v6
        with:
          title: "chore(sdk): regenerate from openapi.yaml"
          branch: sdk/regen
```

## Rules

- **One source of truth.** Pick design-first OR code-first per service — don't hand-edit generated code in either direction.
- **Lint before generating.** A spec that lints clean produces clean SDKs; a sloppy spec produces unusable ones.
- **Diff the SDK in PRs.** Reviewers catch contract regressions faster from generated-code diffs than from spec diffs.
