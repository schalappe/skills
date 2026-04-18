# Language Debuggers

Debugger setup and IDE launch configs for JS/TS, Python, Go, and Rust. Load when setting up an interactive debugger or stepping through code.

## JavaScript / TypeScript

### Breakpoints and console

```typescript
function processOrder(order: Order) {
  debugger; // execution pauses here when DevTools is open

  // conditional pause
  if (order.items.length > 10) debugger;

  console.log("value:", value);
  console.table(arrayOfObjects);           // tabular view
  console.time("op"); /* ... */ console.timeEnd("op");
  console.trace();                         // current stack
  console.assert(value > 0, "must be > 0");
}
```

### VS Code launch config

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

### Node memory snapshots

```typescript
// Trigger a heap snapshot when memory gets high
if (process.memoryUsage().heapUsed > 500 * 1024 * 1024) {
  require("v8").writeHeapSnapshot(); // load the .heapsnapshot file in Chrome DevTools
}
```

## Python

### pdb / breakpoint()

```python
def calculate_total(items):
    breakpoint()                # Python 3.7+, honors PYTHONBREAKPOINT
    total = sum(i.price * i.quantity for i in items)
    return total

# post-mortem at the failing frame
try:
    risky_operation()
except Exception:
    import pdb; pdb.post_mortem()
```

### pdb commands

| Command   | Description         |
| --------- | ------------------- |
| `n`       | Next line           |
| `s`       | Step into           |
| `c`       | Continue            |
| `l`       | List source         |
| `p expr`  | Print expression    |
| `pp expr` | Pretty print        |
| `w`       | Where (stack trace) |
| `u` / `d` | Move up / down frames |
| `q`       | Quit                |

### IPython / ipdb

```python
from ipdb import set_trace
set_trace()      # richer pdb with tab completion + colors

# in an IPython session
%debug           # post-mortem after an exception
%pdb on          # auto-enter debugger on any future exception
```

## Go

### Delve (`dlv`)

```bash
go install github.com/go-delve/delve/cmd/dlv@latest

dlv debug ./cmd/server     # debug a program
dlv test ./...             # debug a test
dlv attach <pid>           # attach to a running process
```

### Delve commands

| Command            | Description          |
| ------------------ | -------------------- |
| `break main.go:10` | Set breakpoint       |
| `continue` / `c`   | Continue execution   |
| `next` / `n`       | Step over            |
| `step` / `s`       | Step into            |
| `print var` / `p`  | Print variable       |
| `goroutines`       | List goroutines      |
| `stack` / `bt`     | Print stack trace    |

## Rust

### LLDB / GDB

```bash
cargo build                          # build with debug info (default in dev)
rust-lldb target/debug/myapp         # macOS default
rust-gdb target/debug/myapp          # Linux default
```

```text
(lldb) breakpoint set --name main
(lldb) run
(lldb) bt           # backtrace
(lldb) frame        # current frame
(lldb) p var        # print variable
(lldb) continue
```

### Logging

```rust
use log::{debug, info, warn, error};

fn process(data: &str) {
    debug!("processing: {}", data);
}
// RUST_LOG=debug cargo run
```
