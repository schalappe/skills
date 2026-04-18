# OpenAPI Validation Configuration

Configuration guides for Spectral and Redocly linting tools.

## Spectral Configuration

Create `.spectral.yaml` in project root:

```yaml
extends: ["spectral:oas", "spectral:asyncapi"]

rules:
  # Enforce operation IDs
  operation-operationId: error

  # Require descriptions
  operation-description: warn
  info-description: error

  # Naming conventions
  operation-operationId-valid-in-url: true

  # Security
  operation-security-defined: error

  # Response codes
  operation-success-response: error

  # Custom rules
  path-params-snake-case:
    description: Path parameters should be snake_case
    severity: warn
    given: "$.paths[*].parameters[?(@.in == 'path')].name"
    then:
      function: pattern
      functionOptions:
        match: "^[a-z][a-z0-9_]*$"

  schema-properties-camelCase:
    description: Schema properties should be camelCase
    severity: warn
    given: "$.components.schemas[*].properties[*]~"
    then:
      function: casing
      functionOptions:
        type: camel
```

### Running Spectral

```bash
# Install
npm install -g @stoplight/spectral-cli

# Lint single file
spectral lint openapi.yaml

# Lint with custom ruleset
spectral lint openapi.yaml --ruleset .spectral.yaml

# Output formats
spectral lint openapi.yaml --format json
spectral lint openapi.yaml --format stylish

# Fail on warnings
spectral lint openapi.yaml --fail-severity warn
```

## Redocly Configuration

Create `redocly.yaml` in project root:

```yaml
extends:
  - recommended

rules:
  no-invalid-media-type-examples: error
  no-invalid-schema-examples: error
  operation-4xx-response: warn
  request-mime-type:
    severity: error
    allowedValues:
      - application/json
  response-mime-type:
    severity: error
    allowedValues:
      - application/json
      - application/problem+json

theme:
  openapi:
    generateCodeSamples:
      languages:
        - lang: curl
        - lang: python
        - lang: javascript
```

### Running Redocly

```bash
# Install
npm install -g @redocly/cli

# Lint
redocly lint openapi.yaml

# Bundle multiple files
redocly bundle openapi.yaml -o bundled.yaml

# Preview documentation
redocly preview-docs openapi.yaml

# Build static docs
redocly build-docs openapi.yaml -o docs/index.html

# Split large spec into multiple files
redocly split openapi.yaml --outDir ./api-spec
```

## CI Integration

### GitHub Actions

```yaml
name: API Spec Validation

on:
  pull_request:
    paths:
      - "api/**"
      - "openapi.yaml"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install tools
        run: |
          npm install -g @stoplight/spectral-cli
          npm install -g @redocly/cli

      - name: Lint with Spectral
        run: spectral lint openapi.yaml --fail-severity warn

      - name: Lint with Redocly
        run: redocly lint openapi.yaml

      - name: Check for breaking changes
        run: |
          git fetch origin main
          redocly diff openapi.yaml --base origin/main:openapi.yaml
```

### Pre-commit Hook

```bash
#!/bin/bash
# .husky/pre-commit

# Find changed OpenAPI files
CHANGED_SPECS=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(yaml|yml)$' | xargs grep -l "openapi:" 2>/dev/null)

if [ -n "$CHANGED_SPECS" ]; then
  echo "Validating OpenAPI specifications..."
  for spec in $CHANGED_SPECS; do
    spectral lint "$spec" || exit 1
  done
fi
```

## Common Validation Issues

### Missing Operation IDs

```yaml
# Bad
paths:
  /users:
    get:
      summary: List users

# Good
paths:
  /users:
    get:
      operationId: listUsers
      summary: List users
```

### Missing Security Definition

```yaml
# Bad
paths:
  /users:
    get:
      operationId: listUsers

# Good
paths:
  /users:
    get:
      operationId: listUsers
      security:
        - bearerAuth: []
```

### Inconsistent Naming

```yaml
# Bad - mixed case styles
components:
  schemas:
    User:
      properties:
        user_name: ...      # snake_case
        emailAddress: ...   # camelCase

# Good - consistent camelCase
components:
  schemas:
    User:
      properties:
        userName: ...
        emailAddress: ...
```

### Missing Error Responses

```yaml
# Bad
responses:
  "200":
    description: Success

# Good
responses:
  "200":
    description: Success
  "400":
    $ref: "#/components/responses/BadRequest"
  "401":
    $ref: "#/components/responses/Unauthorized"
  "404":
    $ref: "#/components/responses/NotFound"
```
