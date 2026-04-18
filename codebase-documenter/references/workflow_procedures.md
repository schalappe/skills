# Documentation Workflow Procedures

This reference provides detailed procedures, advanced patterns, and concrete examples for creating codebase documentation.

## Codebase Analysis Procedures

### Identifying Entry Points

To find the main entry points in a codebase:

**JavaScript/TypeScript projects:**
1. Check `package.json` for `main`, `module`, or `bin` fields
2. Look for `index.js`, `index.ts`, `main.js`, `app.js`, or `server.js`
3. Check `scripts` in `package.json` for start commands
4. Search for framework-specific files: `next.config.js`, `vite.config.ts`, etc.

**Python projects:**
1. Check `setup.py`, `pyproject.toml`, or `setup.cfg` for entry points
2. Look for `__main__.py`, `main.py`, `app.py`, or `cli.py`
3. Check for `if __name__ == "__main__":` blocks
4. Review `Makefile` or `scripts/` directory

**General patterns:**
```bash
# Find main files
ls -la *.{js,ts,py} 2>/dev/null
ls -la src/*.{js,ts,py} 2>/dev/null

# Find config files
ls -la *.config.* *.json *.yaml *.toml 2>/dev/null

# Check for common entry points
find . -name "index.*" -o -name "main.*" -o -name "app.*" | head -20
```

### Mapping Module Dependencies

To understand how modules connect:

1. **Import analysis:**
   ```bash
   # JavaScript/TypeScript imports
   grep -r "^import" src/ --include="*.{js,ts,tsx}"
   grep -r "^from" src/ --include="*.{js,ts,tsx}"

   # Python imports
   grep -r "^import\|^from" . --include="*.py"
   ```

2. **Dependency graph creation:**
   - Start from entry points
   - Follow imports recursively
   - Note circular dependencies
   - Identify shared utilities

3. **Layer identification:**
   ```text
   Presentation (UI/Views)
        ↓
   Application (Services/Controllers)
        ↓
   Domain (Business Logic/Models)
        ↓
   Infrastructure (Database/External APIs)
   ```

### Finding Core Concepts

To identify key abstractions:

1. Look for classes with many imports/usages
2. Find files with descriptive names matching domain terms
3. Check for abstract classes, interfaces, or base types
4. Review naming patterns for domain-specific vocabulary

```bash
# Find most imported modules
grep -rho "from ['\"].*['\"]" src/ | sort | uniq -c | sort -rn | head -20

# Find interface/type definitions
grep -r "^interface\|^type\|^class" src/ --include="*.ts" | head -30
```

## README Documentation Procedure

### Step-by-Step Process

**Step 1: Gather information**
```markdown
Checklist:
[ ] Project name and one-line description
[ ] Technology stack
[ ] Prerequisites (Node version, Python version, etc.)
[ ] Environment variables needed
[ ] Installation commands
[ ] How to run the project
[ ] How to run tests
[ ] Common commands/tasks
[ ] Known issues or gotchas
```

**Step 2: Write the "What This Does" section**

Good examples:
```markdown
## What This Does

A task management API that helps teams track project progress through
a REST interface. Supports real-time updates via WebSockets and
integrates with Slack for notifications.
```

Bad examples:
```markdown
## What This Does

This is a Node.js project that uses Express and PostgreSQL.  # Too technical
This project does stuff with tasks.  # Too vague
```

**Step 3: Create the Quick Start**

Essential elements:
```markdown
## Quick Start

### Prerequisites
- Node.js 18+ (`node --version` to check)
- PostgreSQL 14+ running locally
- Redis (for caching)

### Setup
```bash
# Clone and install
git clone https://github.com/org/project.git
cd project
npm install

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
npm run db:migrate
npm run db:seed

# Start development server
npm run dev
```

### Verify It's Working
Open http://localhost:3000/health - you should see:
```json
{"status": "ok", "version": "1.0.0"}
```

**Step 4: Document project structure**

Include purpose for each directory:
```text
project/
├── src/
│   ├── api/              # REST endpoints and route handlers
│   │   ├── routes/       # Express route definitions
│   │   └── middleware/   # Auth, validation, error handling
│   ├── domain/           # Business logic (framework-agnostic)
│   │   ├── entities/     # Core domain objects
│   │   └── services/     # Business operations
│   ├── infrastructure/   # External integrations
│   │   ├── database/     # PostgreSQL repositories
│   │   └── cache/        # Redis integration
│   └── config/           # Environment and app configuration
├── tests/                # Test files mirroring src/ structure
├── scripts/              # Build and deployment scripts
├── migrations/           # Database migration files
└── docs/                 # Additional documentation
```

## Architecture Documentation Procedure

### Creating System Diagrams

**Component diagram pattern:**
```text
┌─────────────────────────────────────────────────────────────┐
│                        Application                           │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │    Client    │    │     API      │    │   Worker     │   │
│  │  (React SPA) │───▶│   (Express)  │───▶│  (Bull MQ)   │   │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘   │
│                             │                    │           │
│                      ┌──────┴───────┐     ┌──────┴───────┐  │
│                      │   Database   │     │    Cache     │  │
│                      │ (PostgreSQL) │     │   (Redis)    │  │
│                      └──────────────┘     └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Data flow diagram pattern:**
```text
User Authentication Flow:

[Browser] ─── POST /login ───▶ [API Gateway]
                                    │
                              ┌─────┴─────┐
                              │ Validate  │
                              │ Request   │
                              └─────┬─────┘
                                    │
                              ┌─────┴─────┐
                              │  Check    │
                              │  User DB  │
                              └─────┬─────┘
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                  Valid User?            Invalid?
                        │                       │
                  ┌─────┴─────┐          ┌─────┴─────┐
                  │  Generate │          │  Return   │
                  │    JWT    │          │   401     │
                  └─────┬─────┘          └───────────┘
                        │
                  ┌─────┴─────┐
                  │  Store in │
                  │   Redis   │
                  └─────┬─────┘
                        │
                  Return Token
```

### Documenting Design Decisions

Use the ADR (Architecture Decision Record) format:

```markdown
## ADR 001: Use PostgreSQL for Primary Database

### Status
Accepted

### Context
We need a database that supports:
- Complex queries with joins
- Strong consistency for financial transactions
- Full-text search capabilities
- JSON storage for flexible schemas

### Decision
Use PostgreSQL as the primary database with:
- pgvector extension for embeddings
- Full-text search for content
- JSON columns for flexible metadata

### Consequences

**Positive:**
- ACID compliance for transaction safety
- Rich ecosystem of tools and extensions
- Team familiarity reduces learning curve

**Negative:**
- Horizontal scaling is more complex than NoSQL
- Schema migrations require careful planning

**Mitigations:**
- Use read replicas for scaling reads
- Implement proper migration testing pipeline
```

## API Documentation Procedure

### Documenting Endpoints

For each endpoint, document:

```markdown
## Create User

Creates a new user account.

### Endpoint
`POST /api/v1/users`

### Authentication
Bearer token required. Must have `users:create` permission.

### Request

**Headers:**
| Header | Value | Required |
|--------|-------|----------|
| Authorization | Bearer {token} | Yes |
| Content-Type | application/json | Yes |

**Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "member"
}
```

**Field Validation:**
| Field | Type | Constraints | Required |
|-------|------|-------------|----------|
| email | string | Valid email, max 255 chars | Yes |
| name | string | 2-100 characters | Yes |
| role | enum | "admin", "member", "viewer" | No (default: "member") |

### Response

**Success (201 Created):**
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "member",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

| Status | Code | Cause |
|--------|------|-------|
| 400 | VALIDATION_ERROR | Invalid request body |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 403 | FORBIDDEN | Insufficient permissions |
| 409 | EMAIL_EXISTS | Email already registered |

**Error Example:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": {
      "email": "Invalid email format"
    }
  }
}
```

### Example

```bash
curl -X POST https://api.example.com/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "name": "New User",
    "role": "member"
  }'
```

## Code Comments Procedure

### When to Add Comments

**Add comments for:**
- Business logic that isn't obvious from code
- Edge cases and their handling
- Performance optimizations (with benchmarks)
- Workarounds for bugs or limitations
- Complex algorithms (with references)
- Security-sensitive code

**Skip comments for:**
- Obvious operations (incrementing counters, etc.)
- Self-documenting code (well-named functions/variables)
- Implementation details that code clearly shows

### Comment Patterns by Language

**JavaScript/TypeScript (JSDoc):**
```javascript
/**
 * Validates and processes a payment transaction.
 *
 * Business rule: Transactions over $10,000 require additional
 * verification and trigger a compliance review.
 *
 * @param {PaymentRequest} request - Payment details
 * @returns {Promise<PaymentResult>} Transaction result
 * @throws {InsufficientFundsError} When account balance is too low
 * @throws {ComplianceHoldError} When transaction exceeds limits
 *
 * @example
 * const result = await processPayment({
 *   amount: 5000,
 *   currency: 'USD',
 *   accountId: 'acc_123'
 * });
 */
```

**Python (NumPy docstring):**
```python
def calculate_compound_interest(
    principal: float,
    rate: float,
    time: int,
    n: int = 12
) -> float:
    """
    Calculate compound interest for an investment.

    Uses the formula: A = P(1 + r/n)^(nt)

    Parameters
    ----------
    principal : float
        Initial investment amount in dollars.
    rate : float
        Annual interest rate as decimal (e.g., 0.05 for 5%).
    time : int
        Investment duration in years.
    n : int, optional
        Compounding frequency per year (default: 12 for monthly).

    Returns
    -------
    float
        Final amount after interest.

    Examples
    --------
    >>> calculate_compound_interest(1000, 0.05, 10)
    1647.01  # $1000 at 5% for 10 years, compounded monthly

    >>> calculate_compound_interest(1000, 0.05, 10, n=1)
    1628.89  # Same but compounded annually
    """
```

### Inline Comment Prefixes

Use consistent prefixes to categorize comments:

```python
# [>]: Business rule - transactions over $10k need review
if amount > 10000:
    trigger_compliance_review(transaction)

# [!]: Security - prevent SQL injection via parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# [~]: Workaround for Safari bug (remove after Safari 16 EOL)
if is_safari:
    use_fallback_animation()

# [?]: Consider caching this if performance becomes an issue
expensive_result = compute_heavy_operation()

# [@]: TODO - implement retry logic for transient failures
response = external_api.call()
```

## Documentation Review Checklist

### Before Publishing

**Completeness:**
- [ ] All required sections present
- [ ] Prerequisites clearly listed with version numbers
- [ ] Setup steps complete and tested
- [ ] Examples are realistic and tested
- [ ] Links work correctly

**Clarity:**
- [ ] Written for target audience
- [ ] Technical terms defined on first use
- [ ] Examples include full context
- [ ] Success criteria are specific

**Accuracy:**
- [ ] Code examples run without errors
- [ ] Commands produce documented output
- [ ] Version numbers are current
- [ ] Links point to correct locations

**Organization:**
- [ ] Logical information flow
- [ ] Progressive disclosure (simple → complex)
- [ ] Related topics linked
- [ ] Visual aids where helpful

**Maintenance:**
- [ ] Last updated date included
- [ ] Version information noted
- [ ] Deprecated features marked
- [ ] Breaking changes documented

### Testing Documentation

```bash
# Test setup instructions on clean environment
docker run -it --rm node:18 bash

# Inside container, follow README steps exactly
git clone [repo]
cd [project]
# Follow each step...

# Verify success criteria
curl localhost:3000/health
```

## Common Anti-Patterns

### What to Avoid

**Vague instructions:**
```markdown
# BAD
Configure the database appropriately.

# GOOD
Set DATABASE_URL in .env:
DATABASE_URL=postgresql://user:pass@localhost:5432/myapp
```

**Assuming knowledge:**
```markdown
# BAD
Use the standard REST patterns.

# GOOD
All endpoints follow REST conventions:
- GET for reading data
- POST for creating resources
- PATCH for partial updates
- DELETE for removing resources
```

**Missing error handling:**
```markdown
# BAD
Run `npm start` and the app will work.

# GOOD
Run `npm start`. If you see errors:
- "Port 3000 in use" → Run `PORT=3001 npm start`
- "Database connection failed" → Check DATABASE_URL in .env
- "Module not found" → Run `npm install` again
```

**Outdated examples:**
```markdown
# BAD (version not specified)
Install React: npm install react

# GOOD (version specified)
Install React 18: npm install react@18 react-dom@18
```
