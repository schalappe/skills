---
name: product-planning
description: Use when creating product documentation from scratch, defining product vision, building roadmaps, or documenting tech stack choices. Triggers include "plan a product", "create mission document", "build roadmap", "document tech stack", "define product vision", "start a new project", "greenfield app", "what should I build first", or when a user begins a new project without existing product docs — even if they just say "I want to build something" or "help me plan my app."
---

# Product Planning

Produce three aligned documents — mission, roadmap, tech stack — before shipping code. Each doc gates the next so the team agrees on *why*, *what*, and *how* in that order.

## Output structure

```text
docs/product/
├── mission.md      # Vision, users, problems, differentiators
├── roadmap.md      # Prioritized features with effort estimates
└── tech-stack.md   # Technical choices and constraints
```

| Doc           | Anchors             | Written before               |
| ------------- | ------------------- | ---------------------------- |
| mission.md    | Why / Who / What    | any feature work             |
| roadmap.md    | Order + effort      | sprint planning              |
| tech-stack.md | Stack + constraints | first architectural decision |

## Required information

Gather before writing anything:

| Input        | Minimum                             |
| ------------ | ----------------------------------- |
| Product idea | Core concept and purpose            |
| Key features | At least 3 with descriptions        |
| Target users | At least 1 segment with use cases   |
| Tech stack   | Confirm defaults or list deviations |

## Documents

### Mission — `docs/product/mission.md`

Pitch → Users (segments + personas) → Problem (with quantifiable impact) → Differentiators → Key Features (Core / Collaboration / Advanced). Write user benefits, not implementation. Template and section guidance in `references/mission-template.md`.

### Roadmap — `docs/product/roadmap.md`

**Onion-layer ordering:** Foundation → Core → Extended → Advanced. Each layer builds on the previous, and the product must stay functional after every item.

Each item: `[#]. [ ] [FEATURE_NAME] — [1–2 sentence description] [EFFORT]` with effort on the XS (1 day) → XL (3+ weeks) scale.

Constraints:

- Every item delivers user value, end-to-end (frontend + backend).
- No bootstrapping or pure-infrastructure tasks — assume a bare-bones app exists.
- Each item is testable.

Full layer diagram, ordering criteria, good/bad examples, and the effort scale in `references/roadmap-guide.md`.

### Tech stack — `docs/product/tech-stack.md`

Source priority (highest first): user input → global standards (`~/.claude/CLAUDE.md`) → project docs (`CLAUDE.md`, `package.json`, etc.). Cover frontend, backend, infrastructure, dev tools. Specify versions; explain any non-standard choice. Structure and example in `references/tech-stack-template.md`.

## Best practices

- **Sequential, not parallel.** Finish mission before roadmap; finish roadmap before tech stack. Later docs reference earlier ones.
- **Confirm between phases.** Don't batch three documents and hope — alignment at each step saves a full rewrite later.
- **User benefits over implementation.** Especially in mission and roadmap — the reader should see what they can *do*, not how it's built.
- **Quantify impact.** "Reduces onboarding from 30min to 2min" beats "improves UX".
- **Prefer defaults.** Use the user's stated stack unless there's a concrete reason to deviate — then document it.

## Common pitfalls

| Pitfall                           | Fix                                                      |
| --------------------------------- | -------------------------------------------------------- |
| Roadmap item is "Set up backend"  | Fold infra into the first feature that needs it          |
| Mission describes tech, not users | Rewrite from "the user can…" perspective                 |
| Tech stack lists alternatives     | Pick one; document it; move on                           |
| Features unordered by dependency  | Reorder by onion layer — foundation items first          |
| Effort estimates all `M`          | Rescale; a real roadmap spans XS through XL              |
| Documents drift apart             | Roadmap features must trace to mission's Key Features    |

## References — load on demand

| File                                | Load when                                                            |
| ----------------------------------- | -------------------------------------------------------------------- |
| `references/mission-template.md`    | writing mission.md — template, section guidance, quality checklist   |
| `references/roadmap-guide.md`       | writing roadmap.md — onion layers, good/bad examples, validation     |
| `references/tech-stack-template.md` | writing tech-stack.md — structure, stack patterns, example doc       |

## Related commands

- **`/plan-product`** — step-by-step procedure that drives this skill end-to-end.
