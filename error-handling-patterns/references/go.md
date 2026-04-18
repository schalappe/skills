# Go Error Handling

## Sentinel errors

Declare package-level `var Err...` values for conditions callers need to match on. Use `errors.Is` for comparison — never compare strings.

```go
package users

import "errors"

var (
    ErrNotFound     = errors.New("user not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrInvalidInput = errors.New("invalid input")
)

// Caller
if errors.Is(err, users.ErrNotFound) {
    // handle missing user
}
```

## Custom error types

Use struct types when callers need to extract structured fields, not just match identity. Pair with `errors.As`.

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

// Caller
var valErr *ValidationError
if errors.As(err, &valErr) {
    log.Printf("bad field: %s", valErr.Field)
}
```

## Wrapping with `%w`

Annotate with context at each layer; preserve the cause so downstream `errors.Is` / `errors.As` still works across the wrap chain.

```go
func processUser(id string) error {
    user, err := getUser(id)
    if err != nil {
        return fmt.Errorf("process user %s: %w", id, err)
    }
    _ = user
    return nil
}

err := processUser("123")
if errors.Is(err, ErrNotFound) {
    // matches through the wrap chain
}
```

## Concurrent error handling

Use `errgroup` for fan-out operations — it returns the first non-nil error and cancels the shared context so siblings can exit early.

```go
import "golang.org/x/sync/errgroup"

func processAll(ctx context.Context, ids []string) error {
    g, ctx := errgroup.WithContext(ctx)
    for _, id := range ids {
        id := id
        g.Go(func() error {
            return processUser(ctx, id)
        })
    }
    return g.Wait()
}
```

## See also

- `references/resilience.md` — retry and circuit breaker patterns
