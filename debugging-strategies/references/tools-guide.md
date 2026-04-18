# Debugging Tools Guide

Comprehensive guide to debugging tools across languages. Load this reference when setting up debuggers or profiling applications.

## JavaScript/TypeScript Debugging

### Chrome DevTools

```typescript
// Debugger statement
function processOrder(order: Order) {
  debugger; // Execution pauses here

  const total = calculateTotal(order);
  console.log("Total:", total);

  // Conditional breakpoint
  if (order.items.length > 10) {
    debugger; // Only breaks if condition true
  }

  return total;
}

// Console debugging techniques
console.log("Value:", value); // Basic
console.table(arrayOfObjects); // Table format
console.time("operation");
/* code */ console.timeEnd("operation"); // Timing
console.trace(); // Stack trace
console.assert(value > 0, "Value must be positive"); // Assertion

// Performance profiling
performance.mark("start-operation");
// ... operation code
performance.mark("end-operation");
performance.measure("operation", "start-operation", "end-operation");
console.log(performance.getEntriesByType("measure"));
```

### VS Code Configuration

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Program",
      "program": "${workspaceFolder}/src/index.ts",
      "preLaunchTask": "tsc: build - tsconfig.json",
      "outFiles": ["${workspaceFolder}/dist/**/*.js"],
      "skipFiles": ["<node_internals>/**"]
    },
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Tests",
      "program": "${workspaceFolder}/node_modules/jest/bin/jest",
      "args": ["--runInBand", "--no-cache"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Node.js Memory Debugging

```typescript
// Memory usage check
if (process.memoryUsage().heapUsed > 500 * 1024 * 1024) {
  console.warn("High memory usage:", process.memoryUsage());
  require("v8").writeHeapSnapshot();
}

// Memory leak detection in tests
let beforeMemory: number;

beforeEach(() => {
  beforeMemory = process.memoryUsage().heapUsed;
});

afterEach(() => {
  const afterMemory = process.memoryUsage().heapUsed;
  const diff = afterMemory - beforeMemory;
  if (diff > 10 * 1024 * 1024) {
    console.warn(`Possible memory leak: ${diff / 1024 / 1024}MB`);
  }
});
```

## Python Debugging

### Built-in Debugger (pdb)

```python
import pdb

def calculate_total(items):
    total = 0
    pdb.set_trace()  # Debugger starts here

    for item in items:
        total += item.price * item.quantity

    return total

# Python 3.7+ breakpoint
def process_order(order):
    breakpoint()  # More convenient than pdb.set_trace()

# Post-mortem debugging
try:
    risky_operation()
except Exception:
    import pdb
    pdb.post_mortem()  # Debug at exception point
```

### pdb Commands

| Command | Description |
|---------|-------------|
| `n` | Next line |
| `s` | Step into |
| `c` | Continue |
| `l` | List source |
| `p expr` | Print expression |
| `pp expr` | Pretty print |
| `w` | Where (stack trace) |
| `q` | Quit |

### IPython Debugging

```python
from ipdb import set_trace
set_trace()  # Better interface than pdb

# Or use IPython's magic
%debug  # Post-mortem after exception
%pdb on  # Auto-enter debugger on exception
```

### Profiling

```python
import cProfile
import pstats

# Profile function
cProfile.run('slow_function()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 slowest

# Line profiler
# pip install line_profiler
@profile
def slow_function():
    # ... code
    pass
# Run: kernprof -l -v script.py

# Memory profiler
# pip install memory_profiler
@profile
def memory_heavy():
    # ... code
    pass
# Run: python -m memory_profiler script.py
```

## Go Debugging

### Delve Debugger

```bash
# Install
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug program
dlv debug main.go

# Debug test
dlv test ./...

# Attach to process
dlv attach <pid>
```

### Delve Commands

| Command | Description |
|---------|-------------|
| `break main.go:10` | Set breakpoint |
| `continue` | Continue execution |
| `next` | Step over |
| `step` | Step into |
| `print var` | Print variable |
| `goroutines` | List goroutines |
| `stack` | Print stack trace |

### Go Profiling

```go
import (
    "runtime/pprof"
    "os"
)

// CPU profiling
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// Memory profiling
f, _ := os.Create("mem.prof")
pprof.WriteHeapProfile(f)

// HTTP profiling endpoint
import _ "net/http/pprof"
// Visit http://localhost:6060/debug/pprof/
```

```bash
# Analyze profiles
go tool pprof cpu.prof
go tool pprof -http=:8080 cpu.prof  # Web UI
```

## Rust Debugging

### LLDB/GDB

```bash
# Build with debug info
cargo build

# Debug with LLDB
rust-lldb target/debug/myapp

# Or GDB
rust-gdb target/debug/myapp
```

### Common Commands

```text
(lldb) breakpoint set --name main
(lldb) run
(lldb) bt        # Backtrace
(lldb) frame     # Current frame
(lldb) p var     # Print variable
(lldb) continue
```

### Logging for Debug

```rust
use log::{debug, info, warn, error};

fn process(data: &str) {
    debug!("Processing: {}", data);
    // ...
}

// Set RUST_LOG=debug to see output
```

## Database Debugging

### PostgreSQL

```sql
-- Explain query plan
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Show running queries
SELECT pid, query, state, query_start
FROM pg_stat_activity
WHERE state = 'active';

-- Kill long-running query
SELECT pg_terminate_backend(pid);
```

### MySQL

```sql
-- Explain query
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- Show process list
SHOW PROCESSLIST;

-- Kill query
KILL <process_id>;
```

## Network Debugging

### cURL

```bash
# Verbose output
curl -v https://api.example.com/endpoint

# Show timing
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com

# POST with data
curl -X POST -d '{"key":"value"}' -H "Content-Type: application/json" https://api.example.com
```

### HTTPie

```bash
# GET request
http https://api.example.com/users

# POST with JSON
http POST https://api.example.com/users name=John email=john@example.com

# With headers
http https://api.example.com Authorization:"Bearer token"
```
