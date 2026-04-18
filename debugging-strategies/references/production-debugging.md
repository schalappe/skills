# Production Debugging

Safely investigate live incidents without making things worse. Load when debugging an issue that only reproduces in production or is affecting live users.

## The one rule

**Don't debug on prod. Gather evidence, reproduce elsewhere, fix there, deploy.**

Prod is evidence, not a workbench. Every change in a live system is a potential second incident.

## Phase 1: Stabilize

Before investigating, decide whether to **roll back** or **roll forward**:

| Situation                                          | Action                            |
| -------------------------------------------------- | --------------------------------- |
| Regression from the last deploy, root cause unclear | Roll back — investigate in staging |
| Root cause clear and fix is trivial                 | Roll forward with a targeted fix  |
| Issue predates recent deploys                       | Stabilize via feature flag or config, then investigate |
| Data corruption in progress                         | Stop writes (disable feature, put DB in read-only) before anything else |

If users are actively being hurt, mitigate first (flag off the feature, drain traffic, scale up, failover). Investigation comes after the bleeding stops.

## Phase 2: Gather evidence (read-only)

- **Error trackers** — Sentry / Rollbar / Bugsnag: group by release, count, first-seen timestamp. Look for spikes that align with a deploy or config change.
- **Logs** — filter by `correlation_id`, `user_id`, or `request_id` across every service the request touched. If you don't have correlation IDs wired up, see the `logging-standards` skill before your next incident.
- **Metrics** — request rate, error rate, p50/p95/p99 latency, saturation (CPU, memory, connections). An RED/USE dashboard exists for exactly this moment.
- **Distributed traces** — OpenTelemetry / Jaeger / Honeycomb: find a slow or failing trace, walk the spans, spot the culprit service.
- **Recent changes** — last N deploys, feature flag toggles in the last 24h, infra changes, DB migrations. Most prod bugs are fresh.

## Phase 3: Reproduce off-prod

Never debug against the live database. Options, in order of fidelity:

1. **Replay in staging** with anonymized prod data — highest fidelity, slowest setup
2. **Synthetic repro** from the failing request's logged parameters — fast, may miss state-dependent bugs
3. **Local reproduction** mirroring prod's runtime version, env vars, feature-flag state — good for code-path bugs
4. **Shadow traffic** — mirror a fraction of real traffic to a debug replica

If none reproduce, the bug is environmental (network, concurrency, data scale, specific user/tenant). Keep gathering scope evidence.

## Phase 4: Controlled prod investigation (last resort)

If you truly cannot reproduce and must look in prod:

- **Feature-flag the investigation** — enable verbose logging for one user, one region, or a small cohort. Never flip global debug logging on — log volume will overwhelm your aggregator and cost money
- **Read-only attach** — for Node/Python/Go, a profiler like `py-spy dump --pid` or Go's `/debug/pprof/` can observe without modifying state
- **Tracing single requests** — add a header-based sampling hook so you can force-trace one request by setting `X-Debug: 1`
- **Never**: no `pdb.set_trace()`, no interactive debugger, no `console.log` added directly to prod. They pause the process or flood the logs.

## Anonymizing prod data for repro

- Hash or mask PII before export (emails, names, addresses, payment info)
- Preserve **shape**: string lengths, enum distributions, null rates, foreign-key cardinality — bugs often depend on these, not on the real values
- Keep timestamps relative, not absolute, if timezone behavior matters
- Verify the anonymized dump doesn't leak through foreign keys or JSON blobs

Tools: `pganonymize`, `fake-it`, custom scripts over `pg_dump`. For small bugs, often a single anonymized row beats a full dump.

## Correlation IDs — the single biggest prod-debugging investment

Every inbound request should be stamped with a `correlation_id` (also called `trace_id` or `request_id`) and that ID propagated through:

- Every log line touching that request
- Every downstream HTTP call as a header (`X-Correlation-Id` or `traceparent`)
- Every async job spawned for that request (job metadata or headers)
- Every error report (attach as a tag/context)

Without this, "which log lines belong to the failing request?" has no answer. See the `logging-standards` skill for the implementation pattern.

## Distributed tracing quick start

OpenTelemetry is the cross-language standard:

- **SDK**: instrument your app (auto-instrumentation exists for most frameworks)
- **Collector**: receives spans via OTLP, exports to a backend
- **Backend**: Jaeger (OSS, self-hosted), Tempo, Honeycomb, Datadog APM

A trace answers: "For this one failing request, which service or span was slow or errored?" in seconds. Without traces, the same question takes hours of log-diving across services.

## Post-incident

- Write a blameless postmortem: timeline, detection, mitigation, root cause, lessons
- Add a regression test that would have caught it — see the `tdd` skill for writing one around a reproducer
- Note the gap in monitoring/logging that delayed detection and fix it
- If the bug hid behind missing correlation IDs or traces, the postmortem action item is to install them everywhere, not just where this bug bit
