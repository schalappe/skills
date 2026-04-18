# Go Logging

Wide-event implementation with `zerolog` and `context.Context`. Load when adding structured logging to a Go service.

## zerolog with request context

Use `context.Context` to carry the request context through handler chains.

```go
package logging

import (
    "context"
    "os"
    "time"

    "github.com/rs/zerolog/log"
)

type contextKey string

const requestContextKey contextKey = "request_context"

type RequestContext struct {
    fields    map[string]interface{}
    startTime time.Time
}

func NewRequestContext(requestID, service string) *RequestContext {
    return &RequestContext{
        fields: map[string]interface{}{
            "request_id":  requestID,
            "service":     service,
            "environment": os.Getenv("ENVIRONMENT"),
        },
        startTime: time.Now(),
    }
}

func (rc *RequestContext) Add(key string, value interface{}) {
    rc.fields[key] = value
}

func (rc *RequestContext) Emit() {
    rc.fields["duration_ms"] = time.Since(rc.startTime).Milliseconds()

    event := log.Info()
    for k, v := range rc.fields {
        event = event.Interface(k, v)
    }
    event.Msg("request_completed")
}

// Carry the context through the handler chain.
func WithRequestContext(ctx context.Context, rc *RequestContext) context.Context {
    return context.WithValue(ctx, requestContextKey, rc)
}

func GetRequestContext(ctx context.Context) *RequestContext {
    rc, _ := ctx.Value(requestContextKey).(*RequestContext)
    return rc
}
```
