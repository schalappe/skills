# Data Layer Debugging

Database query inspection and HTTP request/response debugging. Load when a query is slow, a response is wrong, or you need to see what actually went over the wire.

## PostgreSQL

### EXPLAIN ANALYZE

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT u.*, o.total
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.email = 'test@example.com';
```

Read the output from the innermost node outward. Watch for:

- **Seq Scan** on a large table with a filter — usually a missing index
- **actual rows** ≫ **rows** (planner estimate) — stale statistics, run `ANALYZE`
- **Nested Loop** with a high iteration count — often an N+1 from the app
- **Buffers: shared read** high — not in cache, cold
- Loop counts inflated by join keys — real cost is `loops × per-loop time`

### Live queries

```sql
-- Sessions and what they're running
SELECT pid, usename, state, wait_event_type, wait_event,
       now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Kill a specific query (cooperative)
SELECT pg_cancel_backend(<pid>);

-- Force-terminate a session (harsh)
SELECT pg_terminate_backend(<pid>);

-- Locks held and waited on
SELECT blocked.pid AS blocked_pid, blocking.pid AS blocking_pid,
       blocked.query AS blocked_query, blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
```

### Index health

```sql
-- Unused indexes (candidate for removal)
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Missing-index candidates: tables with high seq-scan ratio
SELECT relname, seq_scan, idx_scan,
       seq_scan::float / NULLIF(seq_scan + idx_scan, 0) AS seq_ratio
FROM pg_stat_user_tables
WHERE seq_scan + idx_scan > 1000
ORDER BY seq_ratio DESC;
```

## MySQL

```sql
EXPLAIN FORMAT=TREE
SELECT * FROM users WHERE email = 'test@example.com';

SHOW FULL PROCESSLIST;    -- running queries with full text
KILL QUERY <id>;          -- cancel the query but keep the connection
KILL <id>;                -- kill the whole session

-- slow query log (turn on when hunting)
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.1;
```

## HTTP

### curl — the truth of what went over the wire

```bash
curl -v https://api.example.com/endpoint                  # full request/response headers

# Request with JSON body
curl -v -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","email":"jane@example.com"}'

# Just the response status
curl -s -o /dev/null -w "%{http_code}\n" https://api.example.com

# Detailed timing
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com
```

`curl-format.txt`:

```text
dns:        %{time_namelookup}\n
connect:    %{time_connect}\n
tls:        %{time_appconnect}\n
ttfb:       %{time_starttransfer}\n
total:      %{time_total}\n
```

A slow TTFB with fast connect points at the server; a slow connect points at the network.

### HTTPie

```bash
http https://api.example.com/users                        # pretty JSON by default
http POST https://api.example.com/users name=John email=john@example.com
http https://api.example.com Authorization:"Bearer $TOKEN"
http --print=HBhb POST https://api.example.com/endpoint   # show req/res headers + bodies
```

### When the client and server disagree

1. Run the exact call via `curl -v` to see bytes on the wire
2. Check for middleware that rewrites requests (proxies, API gateways, service mesh)
3. Compare Content-Type, charset, and encoding — JSON vs form-urlencoded bugs are common
4. For HTTPS issues: `openssl s_client -connect host:443 -servername host` to inspect the TLS handshake
