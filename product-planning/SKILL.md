---
name: product-planning
description: Use when creating product documentation from scratch, defining product vision, building roadmaps, or documenting tech stack choices. Triggers include "plan a product", "create mission document", "build roadmap", "document tech stack", "define product vision", "start a new project", "greenfield app", "what should I build first", or when a user begins a new project without existing product docs — even if they just say "I want to build something" or "help me plan my app."
---

# Product Planning Skill

Domain knowledge for systematic product planning and documentation. This skill provides the templates, structures, and quality standards—the `/plan-product` command provides the step-by-step procedure.

## Output Structure

Product planning creates three documents:

```text
docs/product/
├── mission.md      # Product vision, users, problems, differentiators
├── roadmap.md      # Prioritized feature list with effort estimates
└── tech-stack.md   # Technical choices and constraints
```

## Mission Document Structure

`docs/product/mission.md` defines the product strategy:

| Section         | Purpose                                     |
| --------------- | ------------------------------------------- |
| Pitch           | One-sentence value proposition              |
| Users           | Primary customers and detailed personas     |
| The Problem     | Problem statement and solution approach     |
| Differentiators | Unique advantages over alternatives         |
| Key Features    | Categorized feature list with user benefits |

### Mission Template

The mission document follows this structure: Pitch (one-sentence value prop), Users (segments and detailed personas with pain points/goals), The Problem (statement with quantifiable impact and solution approach), Differentiators (competitive advantages with measurable benefits), and Key Features (categorized by Core/Collaboration/Advanced with user benefit descriptions).

Focus on user benefits over technical implementation. Keep content concise and scannable. Use quantifiable impacts where possible.

For the complete template with placeholder fields, see `references/mission-template.md`.

## Roadmap Structure

`docs/product/roadmap.md` prioritizes features using the **Onion Layer Philosophy**.

### Onion Layer Philosophy

Features are ordered in concentric layers: Foundation (essential infrastructure) → Core (primary user value) → Extended (enhanced capabilities) → Advanced (polish and power features). Each layer builds on the previous, and the product must remain functional after completing any feature. Features deliver user value (user gains a capability or can accomplish a task); technical setup tasks are embedded within the features that need them.

Each roadmap item follows: `[#]. [ ] [FEATURE_NAME] — [1-2 sentence description] [EFFORT]` with effort estimates from XS (1 day) to XL (3+ weeks).

For the full onion layer diagram, feature vs. non-feature examples, effort scale, and ordering criteria, see `references/roadmap-guide.md`.

### Roadmap Constraints

- Each item must deliver user value (not just technical setup)
- Each item must be end-to-end functional and testable
- Product must work after completing each feature
- Include both frontend and backend when applicable
- Do NOT include bootstrapping or initialization tasks
- Assume bare-bones application already exists

## Tech Stack Document

`docs/product/tech-stack.md` records technical choices.

Tech stack choices are gathered from user input (highest priority), global standards (`~/.claude/CLAUDE.md`), and project documentation (`CLAUDE.md`). For the full information source hierarchy and document structure, see `references/tech-stack-template.md`.

## Required Information

Before creating documents, gather:

| Required Info | Description                                   |
| ------------- | --------------------------------------------- |
| Product Idea  | Core concept and purpose                      |
| Key Features  | Minimum 3 features with descriptions          |
| Target Users  | At least 1 user segment with use cases        |
| Tech Stack    | Confirmation or deviations from default stack |

## Best Practices

### Sequential Execution

- Complete each document fully before proceeding
- Wait for user confirmation between phases
- Do not skip ahead or combine phases

### User Alignment

- Ensure documents align with user's standards
- Reference user's CLAUDE.md for preferences
- Ask clarifying questions when needed

### Document Quality

- Keep content concise and scannable
- Focus on "why" over "what"
- Use clear, actionable language
- Include quantifiable metrics where possible

## Quality Checklist

Before completing each document:

**Mission:**
- [ ] Pitch clearly states value proposition
- [ ] User personas are specific and actionable
- [ ] Problems include quantifiable impacts
- [ ] Differentiators show competitive advantage
- [ ] Features focus on user benefits

**Roadmap:**
- [ ] Each feature delivers user value (not technical setup)
- [ ] Features follow onion layer order (foundation → core → extended → polish)
- [ ] Product remains functional after completing each feature
- [ ] Each item is end-to-end (frontend + backend + tests)
- [ ] Effort estimates are realistic
- [ ] No bootstrapping or infrastructure-only tasks

**Tech Stack:**
- [ ] User preferences prioritized
- [ ] All major technology choices documented
- [ ] Constraints and trade-offs noted

## Additional Resources

### Reference Files

For detailed templates and guidance, consult:

- **`references/mission-template.md`** - Complete mission document examples
- **`references/roadmap-guide.md`** - Detailed roadmap creation guidance
- **`references/tech-stack-template.md`** - Tech stack documentation patterns

## Related Commands

- **`/plan-product`** — Creates mission.md, roadmap.md, and tech-stack.md for a new product
