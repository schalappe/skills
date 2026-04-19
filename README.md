# Agent Skills

A collection of agent skills that extend capabilities across planning, architecture, development, and release engineering.

## Planning & Design

These skills help you think through problems before writing code.

- **writing-plans** — Turn a spec or requirements into a bite-sized, TDD-friendly implementation plan before touching code.

  ```text
  npx skills@latest add schalappe/skills/writing-plans
  ```

- **product-planning** — Produce aligned mission, roadmap, and tech-stack documents for a new product before shipping code.

  ```text
  npx skills@latest add schalappe/skills/product-planning
  ```

- **api-design-principles** — Design REST and GraphQL APIs with resource modeling, pagination, error handling, auth, webhooks, and async patterns.

  ```text
  npx skills@latest add schalappe/skills/api-design-principles
  ```

- **openapi-spec-generation** — Generate and maintain OpenAPI 3.1 specs — design-first, code-first, validation with Spectral/Redocly, and SDK codegen.

  ```text
  npx skills@latest add schalappe/skills/openapi-spec-generation
  ```

## Architecture Patterns

These skills guide structural decisions in service-oriented and distributed systems.

- **microservices-patterns** — Decomposition, inter-service communication, data isolation, resilience, and observability for service-oriented systems.

  ```text
  npx skills@latest add schalappe/skills/microservices-patterns
  ```

- **saga-orchestration** — Coordinate distributed transactions across services with compensating actions for partial-failure recovery.

  ```text
  npx skills@latest add schalappe/skills/saga-orchestration
  ```

- **error-handling-patterns** — Exception hierarchies, Result/Option types, retries, circuit breakers, and graceful degradation.

  ```text
  npx skills@latest add schalappe/skills/error-handling-patterns
  ```

## Development Workflow

These skills help you execute, verify, and close out work.

- **executing-plans** — Load a written plan, review it critically, execute all tasks, and report when complete — with review checkpoints.

  ```text
  npx skills@latest add schalappe/skills/executing-plans
  ```

- **verification-before-completion** — Run verification commands and confirm output before claiming work is done, fixed, or passing.

  ```text
  npx skills@latest add schalappe/skills/verification-before-completion
  ```

- **finishing-a-development-branch** — Decide how to integrate completed work — merge, PR, or cleanup — with structured options.

  ```text
  npx skills@latest add schalappe/skills/finishing-a-development-branch
  ```

- **debugging-strategies** — Scientific method, binary search, differential debugging, language-specific debuggers, profilers, and safe production investigation.

  ```text
  npx skills@latest add schalappe/skills/debugging-strategies
  ```

## Documentation & Release

These skills cover docs, observability, and release hygiene.

- **codebase-documenter** — Produce READMEs, architecture guides, API references, ADRs, runbooks, onboarding material, and CONTRIBUTING guides.

  ```text
  npx skills@latest add schalappe/skills/codebase-documenter
  ```

- **changelog-automation** — Automate changelogs, conventional commits, release notes, and semantic versioning workflows.

  ```text
  npx skills@latest add schalappe/skills/changelog-automation
  ```

- **logging-standards** — Structured, queryable production logs — wide events, canonical log lines, high-cardinality fields, tail sampling, and PII redaction.

  ```text
  npx skills@latest add schalappe/skills/logging-standards
  ```
