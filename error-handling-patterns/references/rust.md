# Rust Error Handling

## Custom error enum

Model the failure domain with an enum. Implement `Display` and `Error::source` so errors compose cleanly with `?` and downstream `source()` chains.

```rust
use std::error::Error;
use std::fmt;

#[derive(Debug)]
pub enum AppError {
    Io(std::io::Error),
    Parse(std::num::ParseIntError),
    NotFound   { resource: String, id: String },
    Validation { field: String,    message: String },
    External   { service: String,  message: String },
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::Io(e)    => write!(f, "IO error: {e}"),
            AppError::Parse(e) => write!(f, "parse error: {e}"),
            AppError::NotFound   { resource, id } =>
                write!(f, "{resource} not found: {id}"),
            AppError::Validation { field, message } =>
                write!(f, "validation error in {field}: {message}"),
            AppError::External   { service, message } =>
                write!(f, "external service {service} error: {message}"),
        }
    }
}

impl Error for AppError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            AppError::Io(e)    => Some(e),
            AppError::Parse(e) => Some(e),
            _ => None,
        }
    }
}

impl From<std::io::Error> for AppError {
    fn from(error: std::io::Error) -> Self { AppError::Io(error) }
}
```

## With `thiserror`

For libraries, `thiserror` removes the boilerplate without leaking a dep onto callers.

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("parse error: {0}")]
    Parse(#[from] std::num::ParseIntError),

    #[error("{resource} not found: {id}")]
    NotFound { resource: String, id: String },

    #[error("validation error in {field}: {message}")]
    Validation { field: String, message: String },
}
```

Rule of thumb: `thiserror` for library errors (typed, matchable), `anyhow` for application-level errors (opaque, contextual).

## Combinators and `?`

Prefer `?` for propagation and `map_err` / `and_then` for targeted transformations.

```rust
fn process_file(path: &str) -> Result<i32, AppError> {
    let contents = std::fs::read_to_string(path)?;
    contents
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

## See also

- `references/resilience.md` — retry and circuit breaker patterns
