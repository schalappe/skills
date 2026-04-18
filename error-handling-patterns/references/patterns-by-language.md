# Error Handling Patterns by Language

Detailed error handling patterns for Python, TypeScript, Rust, and Go. Load this reference when implementing error handling in specific languages.

## Python Patterns

### Custom Exception Hierarchy

```python
from datetime import datetime
from typing import Optional

class ApplicationError(Exception):
    """Base exception for all application errors."""
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class ValidationError(ApplicationError):
    """Raised when validation fails."""
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
        self.field = field

class NotFoundError(ApplicationError):
    """Raised when resource not found."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            f"{resource} not found",
            code="NOT_FOUND",
            details={"resource": resource, "id": resource_id}
        )

class ExternalServiceError(ApplicationError):
    """Raised when external service fails."""
    def __init__(self, message: str, service: str, **kwargs):
        super().__init__(message, code="EXTERNAL_SERVICE_ERROR", **kwargs)
        self.service = service
```

### Context Managers

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def database_transaction(session) -> Generator:
    """Ensure transaction is committed or rolled back."""
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def error_context(context: str) -> Generator:
    """Add context to any exception raised within."""
    try:
        yield
    except Exception as e:
        raise type(e)(f"{context}: {e}") from e
```

### Retry Decorator

```python
import time
from functools import wraps
from typing import TypeVar, Callable, Tuple, Type

T = TypeVar('T')

def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] = None
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if on_retry:
                        on_retry(e, attempt + 1)
                    if attempt < max_attempts - 1:
                        sleep_time = backoff_factor ** attempt
                        time.sleep(sleep_time)
            raise last_exception
        return wrapper
    return decorator
```

## TypeScript Patterns

### Result Type

```typescript
// Result type for explicit error handling
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

// Helper functions
function Ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function Err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

// Usage
function parseJSON<T>(json: string): Result<T, SyntaxError> {
  try {
    return Ok(JSON.parse(json) as T);
  } catch (error) {
    return Err(error as SyntaxError);
  }
}

// Consuming Result
const result = parseJSON<User>(userJson);
if (result.ok) {
  console.log(result.value.name);
} else {
  console.error("Parse failed:", result.error.message);
}

// Chaining Results
function chain<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => Result<U, E>
): Result<U, E> {
  return result.ok ? fn(result.value) : result;
}

function map<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => U
): Result<U, E> {
  return result.ok ? Ok(fn(result.value)) : result;
}
```

### Custom Error Classes

```typescript
class ApplicationError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      details: this.details,
    };
  }
}

class ValidationError extends ApplicationError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, "VALIDATION_ERROR", 400, details);
  }
}

class NotFoundError extends ApplicationError {
  constructor(resource: string, id: string) {
    super(`${resource} not found`, "NOT_FOUND", 404, { resource, id });
  }
}

class UnauthorizedError extends ApplicationError {
  constructor(message: string = "Unauthorized") {
    super(message, "UNAUTHORIZED", 401);
  }
}
```

### Async Error Handling

```typescript
// Wrap async function to catch all errors
function asyncHandler<T extends unknown[], R>(
  fn: (...args: T) => Promise<R>
): (...args: T) => Promise<R> {
  return async (...args: T): Promise<R> => {
    try {
      return await fn(...args);
    } catch (error) {
      if (error instanceof ApplicationError) {
        throw error;
      }
      throw new ApplicationError(
        error instanceof Error ? error.message : "Unknown error",
        "INTERNAL_ERROR"
      );
    }
  };
}

// Promise.allSettled for multiple async operations
async function fetchAllUsers(ids: string[]): Promise<User[]> {
  const results = await Promise.allSettled(ids.map((id) => fetchUser(id)));

  const users: User[] = [];
  const errors: Error[] = [];

  for (const result of results) {
    if (result.status === "fulfilled") {
      users.push(result.value);
    } else {
      errors.push(result.reason);
    }
  }

  if (errors.length > 0) {
    console.error(`Failed to fetch ${errors.length} users:`, errors);
  }

  return users;
}
```

## Rust Patterns

### Custom Error Types

```rust
use std::fmt;
use std::error::Error;

#[derive(Debug)]
pub enum AppError {
    Io(std::io::Error),
    Parse(std::num::ParseIntError),
    NotFound { resource: String, id: String },
    Validation { field: String, message: String },
    External { service: String, message: String },
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::Io(e) => write!(f, "IO error: {}", e),
            AppError::Parse(e) => write!(f, "Parse error: {}", e),
            AppError::NotFound { resource, id } =>
                write!(f, "{} not found: {}", resource, id),
            AppError::Validation { field, message } =>
                write!(f, "Validation error in {}: {}", field, message),
            AppError::External { service, message } =>
                write!(f, "External service {} error: {}", service, message),
        }
    }
}

impl Error for AppError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            AppError::Io(e) => Some(e),
            AppError::Parse(e) => Some(e),
            _ => None,
        }
    }
}

// Automatic conversion from std::io::Error
impl From<std::io::Error> for AppError {
    fn from(error: std::io::Error) -> Self {
        AppError::Io(error)
    }
}
```

### Using thiserror Crate

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Parse error: {0}")]
    Parse(#[from] std::num::ParseIntError),

    #[error("{resource} not found: {id}")]
    NotFound { resource: String, id: String },

    #[error("Validation error in {field}: {message}")]
    Validation { field: String, message: String },
}
```

### Result Combinators

```rust
fn process_file(path: &str) -> Result<i32, AppError> {
    std::fs::read_to_string(path)?        // ? propagates error
        .trim()
        .parse()
        .map_err(AppError::Parse)          // Convert error type
}

// Chaining with and_then
fn process_and_validate(path: &str) -> Result<i32, AppError> {
    std::fs::read_to_string(path)?
        .trim()
        .parse::<i32>()
        .map_err(AppError::Parse)
        .and_then(|n| {
            if n > 0 {
                Ok(n)
            } else {
                Err(AppError::Validation {
                    field: "number".into(),
                    message: "must be positive".into(),
                })
            }
        })
}
```

## Go Patterns

### Sentinel Errors

```go
import "errors"

var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrInvalidInput = errors.New("invalid input")
)

// Check with errors.Is
if errors.Is(err, ErrNotFound) {
    // Handle not found
}
```

### Custom Error Types

```go
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for %s: %s", e.Field, e.Message)
}

type NotFoundError struct {
    Resource string
    ID       string
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s not found: %s", e.Resource, e.ID)
}

// Check with errors.As
var valErr *ValidationError
if errors.As(err, &valErr) {
    fmt.Printf("Validation error in field: %s\n", valErr.Field)
}
```

### Error Wrapping

```go
func processUser(id string) error {
    user, err := getUser(id)
    if err != nil {
        return fmt.Errorf("process user %s failed: %w", id, err)
    }
    // ... process
    return nil
}

// Unwrap chain
err := processUser("123")
if errors.Is(err, ErrNotFound) {
    // Original error is preserved and detectable
}
```

### Multi-Error Handling

```go
import "golang.org/x/sync/errgroup"

func processAll(ids []string) error {
    g := new(errgroup.Group)

    for _, id := range ids {
        id := id // capture for goroutine
        g.Go(func() error {
            return processUser(id)
        })
    }

    return g.Wait() // Returns first error
}
```
