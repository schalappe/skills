---
name: debugging-strategies
description: Use when debugging bugs, investigating crashes, tracking regressions, profiling performance, hunting memory leaks, or analyzing stack traces — even without the word "debug." Covers the scientific method, binary search, differential debugging, language-specific debuggers (JS/TS, Python, Go, Rust), profilers, and safe production investigation.
---

# Debugging Strategies

Turn elusive bugs into systematic problem-solving with reproducible steps, differential analysis, and the right language-specific tool.

## Agent workflow

### 1. Reproduce

- Can you trigger it on demand? If not, make it reproducible first — randomness usually means you don't yet understand it
- Shrink to a minimal case: smallest input, fewest dependencies, shortest code path
- Record exact steps, environment details, and full error output

### 2. Gather

| Category       | Collect                                                  |
| -------------- | -------------------------------------------------------- |
| Error output   | Full stack trace, error codes, console/server logs       |
| Environment    | OS, language/runtime version, dependency versions        |
| Recent changes | `git log` since last known-good, deployment timeline     |
| Scope          | All users? All browsers? Production only? Specific data? |

### 3. Hypothesize

Frame a testable theory:

- What differs between working and broken? (see *differential debugging* below)
- What's the smallest input that could trigger this?
- Which layer could fail — input validation, business logic, data, external service?

Articulate expected vs actual behavior out loud or in writing. Forcing precise language often exposes the wrong assumption ("explain-to-discover").

### 4. Test & verify

| Strategy              | When to use                                                     |
| --------------------- | --------------------------------------------------------------- |
| Binary search         | Comment out half; for regressions use `git bisect`              |
| Add instrumentation   | Log values, trace execution, measure timing                     |
| Isolate components    | Run each piece standalone, mock dependencies                    |
| Differential analysis | Diff working vs broken: config, env, data, user, concurrency    |
| Confirm + clean up    | Write a test that would have caught it, then remove scaffolding |

## Techniques

### Binary search

For code regressions, use `git bisect` to automate the search — see the `git-advanced-workflows` skill for the full workflow. For live code paths, comment out or feature-flag half the suspect code and narrow iteratively.

### Differential debugging

Compare working vs broken across: runtime/version, data shape, user role, time of day, deployment target, concurrency level. A single diff often points straight at the cause.

### Explain-to-discover

State the expected behavior, then narrate the actual execution step-by-step. The assumption you glossed over usually falls out.

## Mindset

- "It can't be X" — yes it can. Verify.
- "I didn't change Y" — check the diff anyway.
- "Works on my machine" — find the difference.
- Change one thing at a time. Multiple simultaneous changes make cause-and-effect invisible.

## By issue type

| Issue           | First move                                                                                              |
| --------------- | ------------------------------------------------------------------------------------------------------- |
| Intermittent    | Stress-test in a loop; log timing and state transitions; suspect race conditions or ordering            |
| Performance     | Profile before optimizing — see [profiling.md](references/profiling.md)                                 |
| Production-only | Gather evidence without mutating prod — see [production-debugging.md](references/production-debugging.md) |
| Query slowness  | `EXPLAIN ANALYZE` first — see [data-layer-debugging.md](references/data-layer-debugging.md)             |
| Memory leak    | Heap snapshots + allocation profiling — see [profiling.md](references/profiling.md)                     |

## References — load on demand

| File                                                          | Load when                                                               |
| ------------------------------------------------------------- | ----------------------------------------------------------------------- |
| [language-debuggers.md](references/language-debuggers.md)     | setting up a debugger or IDE launch config for JS/TS, Python, Go, Rust  |
| [profiling.md](references/profiling.md)                       | investigating CPU hotspots, memory pressure, or slow response times     |
| [data-layer-debugging.md](references/data-layer-debugging.md) | debugging slow SQL queries or inspecting HTTP request/response bodies   |
| [production-debugging.md](references/production-debugging.md) | investigating a live production incident safely                         |

## Related skills

- `git-advanced-workflows` — `git bisect`, reflog recovery, history archaeology
- `logging-standards` — what to log so bugs are traceable after the fact
- `error-handling-patterns` — prevent bugs that need debugging in the first place
