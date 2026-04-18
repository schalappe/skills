# Log Sampling

Decide which requests survive to the log backend. Load when log volume is a cost/noise problem or when designing a sampling policy.

## Head vs tail sampling

| Type | Decision point | Pros                       | Cons                               |
| ---- | -------------- | -------------------------- | ---------------------------------- |
| Head | Request start  | Consistent trace, simple   | Drops interesting traffic blindly  |
| Tail | Request end    | Keeps errors & slow tail   | More complex, needs buffering      |

**Always prefer tail sampling.** At request start you cannot know if the request will fail, be slow, or hit a VIP code path — the three things you most want to keep.

## Tail-sampling implementation

```python
import random
from dataclasses import dataclass
from typing import Any

@dataclass
class SamplingConfig:
    error_rate: float = 1.0       # always keep errors
    slow_rate: float = 1.0        # always keep slow requests
    vip_rate: float = 1.0         # always keep VIP users
    baseline_rate: float = 0.05   # 5% random sample for the rest

    slow_threshold_ms: int = 1000
    vip_tiers: frozenset = frozenset({"premium", "enterprise"})

def should_sample(ctx: dict[str, Any], config: SamplingConfig) -> bool:
    """Decide whether this request should be logged."""

    if ctx.get("http_status", 200) >= 400:
        return random.random() < config.error_rate

    if ctx.get("duration_ms", 0) > config.slow_threshold_ms:
        return random.random() < config.slow_rate

    if ctx.get("user_tier") in config.vip_tiers:
        return random.random() < config.vip_rate

    return random.random() < config.baseline_rate
```

Call `should_sample(ctx._data, config)` just before emitting the wide event. Return fast when the decision is "keep everything" so hot paths aren't paying the RNG cost on normal traffic.
