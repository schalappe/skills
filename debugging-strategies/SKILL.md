---
name: debugging-strategies
description: Use when the user needs debugging methodologies, tool configurations, profiling setup, or systematic debugging approaches. Covers binary search, differential debugging, language-specific tools, and profiling. For active bug investigation in the current session, prefer the systematic-debugging skill instead.
---

# Debugging Strategies

Transform debugging from frustrating guesswork into systematic problem-solving with proven strategies, powerful tools, and methodical approaches.

## When to Use This Skill

- Tracking down elusive bugs
- Investigating performance issues
- Understanding unfamiliar codebases
- Debugging production issues
- Analyzing crash dumps and stack traces
- Profiling application performance
- Investigating memory leaks

## Core Principles

### The Scientific Method

1. **Observe**: What's the actual behavior?
2. **Hypothesize**: What could be causing it?
3. **Experiment**: Test your hypothesis
4. **Analyze**: Did it prove/disprove your theory?
5. **Repeat**: Until you find the root cause

### Debugging Mindset

**Don't Assume:**
- "It can't be X" - Yes it can
- "I didn't change Y" - Check anyway
- "It works on my machine" - Find out why

**Do:**
- Reproduce consistently
- Isolate the problem
- Keep detailed notes
- Question everything
- Take breaks when stuck

## Systematic Process

### Phase 1: Reproduce

1. **Can you reproduce it?** - Always? Sometimes? Randomly?
2. **Create minimal reproduction** - Simplify to smallest example
3. **Document steps** - Exact steps, environment details, error messages

### Phase 2: Gather Information

| Category | What to Collect |
|----------|-----------------|
| Error Messages | Full stack trace, error codes, console output |
| Environment | OS, language version, dependencies |
| Recent Changes | Git history, deployment timeline, config changes |
| Scope | Affects all users? All browsers? Production only? |

### Phase 3: Form Hypothesis

Ask:
- What changed recently?
- What's different between working and broken?
- Where could this fail? (input validation, business logic, data layer, external services)

### Phase 4: Test & Verify

| Strategy | When to Use |
|----------|-------------|
| Binary Search | Comment out half the code, narrow down |
| Add Logging | Track variable values, trace execution flow |
| Isolate Components | Test each piece separately, mock dependencies |
| Compare Working vs Broken | Diff configurations, environments, data |

## Debugging Techniques

### Technique 1: Binary Search Debugging

```bash
# Git bisect for finding regression
git bisect start
git bisect bad                    # Current commit is bad
git bisect good v1.0.0            # v1.0.0 was good

# Git checks out middle commit - test it
# Then mark as good or bad
git bisect good   # if it works
git bisect bad    # if it's broken

# Continue until bug found
git bisect reset  # when done

# Automated version
git bisect start HEAD v1.0.0
git bisect run npm test
```

### Technique 2: Differential Debugging

Compare working vs broken:

| Aspect | Working | Broken |
|--------|---------|--------|
| Environment | Development | Production |
| Node version | 18.16.0 | 18.15.0 |
| Data | Empty DB | 1M records |
| User | Admin | Regular user |
| Time | During day | After midnight |

### Technique 3: Explain-to-Discover

Articulate the problem step-by-step — describe what the code should do, then what it actually does. Walk through the execution path out loud or in writing. Forcing precise explanation often exposes the faulty assumption.

## Debugging by Issue Type

### Intermittent Bugs

1. **Add extensive logging** - timing, state transitions, external interactions
2. **Look for race conditions** - concurrent access, async timing
3. **Check timing dependencies** - setTimeout, Promise order, animation frames
4. **Stress test** - Run many times, vary timing, simulate load

### Performance Issues

1. **Profile first** - Don't optimize blindly
2. **Common culprits** - N+1 queries, unnecessary re-renders, large data processing, synchronous I/O
3. **Measure before and after** - Verify improvement

### Production Bugs

1. **Gather evidence** - Error tracking, logs, user reports, metrics
2. **Reproduce locally** - Use production data (anonymized), match environment
3. **Safe investigation** - Don't change production, use feature flags

## Quick Debugging Checklist

When stuck, check:

- [ ] Spelling errors (typos in variable names)
- [ ] Case sensitivity (fileName vs filename)
- [ ] Null/undefined values
- [ ] Array index off-by-one
- [ ] Async timing (race conditions)
- [ ] Scope issues (closure, hoisting)
- [ ] Type mismatches
- [ ] Missing dependencies
- [ ] Environment variables
- [ ] File paths (absolute vs relative)
- [ ] Cache issues (clear cache)
- [ ] Stale data (refresh database)

## Language Quick Reference

### JavaScript/TypeScript

```typescript
debugger;                         // Pause execution
console.log("Value:", value);     // Basic logging
console.table(arrayOfObjects);    // Table format
console.time("op"); /* code */ console.timeEnd("op");  // Timing
console.trace();                  // Stack trace
```

### Python

```python
breakpoint()                      # Python 3.7+ debugger
import pdb; pdb.set_trace()      # Traditional debugger
import pdb; pdb.post_mortem()    # Debug at exception point

# Profiling
import cProfile
cProfile.run('slow_function()', 'profile_stats')
```

### Go

```go
import "runtime/debug"
debug.PrintStack()               // Print stack trace

// Profile endpoint
import _ "net/http/pprof"
// Visit http://localhost:6060/debug/pprof/
```

## Common Debugging Mistakes

| Mistake | Better Approach |
|---------|-----------------|
| Making multiple changes | Change one thing at a time |
| Not reading error messages | Read the full stack trace |
| Assuming it's complex | Often it's simple |
| Debug logging in prod | Remove before shipping |
| Not using debugger | console.log isn't always best |
| Giving up too soon | Persistence pays off |
| Not testing the fix | Verify it actually works |

## Best Practices

1. **Reproduce First** - Can't fix what you can't reproduce
2. **Isolate the Problem** - Remove complexity until minimal case
3. **Read Error Messages** - They're usually helpful
4. **Check Recent Changes** - Most bugs are recent
5. **Use Version Control** - Git bisect, blame, history
6. **Take Breaks** - Fresh eyes see better
7. **Document Findings** - Help future you
8. **Fix Root Cause** - Not just symptoms

## Additional Resources

### Reference Files

For detailed tool configurations and profiling guides:

- **`references/tools-guide.md`** - Complete debugging tool guide for JavaScript, Python, Go, and Rust including VS Code configuration and profilers
