# Profiling

CPU, memory, and allocation profiling across languages. Load when chasing slow endpoints, high memory use, or suspected leaks.

## The profiling rule

**Measure before you change anything.** The bottleneck is almost never where you think. Profile → identify hotspot → change → re-profile. If you can't show a before/after number, you haven't improved anything.

## JavaScript / TypeScript

### User-timing API

```typescript
performance.mark("start-op");
// ... operation
performance.mark("end-op");
performance.measure("op", "start-op", "end-op");
console.log(performance.getEntriesByType("measure"));
```

### Chrome DevTools

- **Performance** tab → record a trace → flame chart shows per-call time
- **Memory** tab → heap snapshot → compare two snapshots to find retained objects
- **Allocation instrumentation on timeline** → see which code paths allocate

### Node CPU / heap profiles

```bash
node --cpu-prof --cpu-prof-dir=./profiles app.js   # .cpuprofile files
node --heap-prof --heap-prof-dir=./profiles app.js # .heapprofile files
# Load either file in Chrome DevTools → Performance / Memory tab
```

### Test-level memory leak check

```typescript
let before: number;
beforeEach(() => { before = process.memoryUsage().heapUsed; });
afterEach(() => {
  const diff = process.memoryUsage().heapUsed - before;
  if (diff > 10 * 1024 * 1024) console.warn(`possible leak: ${diff / 1024 / 1024} MB`);
});
```

## Python

### cProfile

```python
import cProfile, pstats
cProfile.run("slow_function()", "profile.out")
stats = pstats.Stats("profile.out")
stats.sort_stats("cumulative").print_stats(10)  # top 10 by cumulative time
```

### Line-level profilers

```python
# pip install line_profiler
@profile
def slow_function():
    ...
# kernprof -l -v script.py

# pip install memory_profiler
@profile
def memory_heavy():
    ...
# python -m memory_profiler script.py
```

### Continuous profilers

`py-spy record -o profile.svg -- python app.py` produces a flamegraph without code changes — works on running PIDs too (`py-spy dump --pid <pid>`).

## Go

### pprof

```go
import (
    "os"
    "runtime/pprof"
)

// CPU profile
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// heap snapshot
fm, _ := os.Create("mem.prof")
pprof.WriteHeapProfile(fm)
```

```go
// HTTP endpoint — exposes all pprof profiles at /debug/pprof/
import _ "net/http/pprof"
// go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
```

```bash
go tool pprof cpu.prof                  # interactive TUI
go tool pprof -http=:8080 cpu.prof      # flamegraph web UI
go tool pprof -alloc_space mem.prof     # allocations, not in-use
```

## Rust

### Flamegraph

```bash
cargo install flamegraph
cargo flamegraph --bin myapp            # produces flamegraph.svg
```

### Benchmarks + profiling

```bash
cargo bench                             # criterion gives statistically sound measurements
RUSTFLAGS="-C force-frame-pointers=yes" cargo build --release
perf record --call-graph=dwarf target/release/myapp
perf report
```

## Common culprits

| Symptom                          | Likely cause                                                |
| -------------------------------- | ----------------------------------------------------------- |
| High CPU, low throughput         | Inefficient algorithm, unnecessary serialization, regex abuse |
| Memory grows over time           | Unbounded cache, event-listener leak, closure retention     |
| Latency spikes under load        | Connection pool exhaustion, GC pauses, lock contention      |
| DB query slow                    | Missing index, N+1, or row-by-row ORM fetch                 |
| Slow first request, fast after   | Cold cache, JIT warm-up, lazy initialization                |
