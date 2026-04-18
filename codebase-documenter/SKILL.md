---
name: codebase-documenter
description: Create project documentation: READMEs, architecture guides, API references, ADRs, runbooks, onboarding material, CONTRIBUTING guides, module/package overviews, and inline code comments. Use when documenting a project, writing a README, explaining project structure, adding code comments, producing a code walkthrough, or when the user asks "how does this codebase work?" — even without the word "documentation." Out of scope: OpenAPI specs (see openapi-spec-generation) and release notes (see changelog-automation).
---

# Codebase Documenter

Produce beginner-friendly documentation for an existing codebase using templates, references, and a repeatable analysis workflow.

## Agent workflow

### 1. Analyze the codebase

- **Entry points** — Glob `**/index.{ts,js,py}`, `**/main.{ts,js,py}`, `**/app.{ts,js,py}`, `**/server.{ts,js,py}`
- **Project metadata** — Read `package.json`, `pyproject.toml`, `tsconfig.json`, `Cargo.toml`, `go.mod`, or `Makefile`
- **Structure** — list the top-level and `src/` directories
- **Tech stack** — infer from dependencies and framework configs
- **Existing docs** — Glob `**/*.md` to avoid duplication

For >10 source files or a non-obvious layout, see `references/workflow_procedures.md`.

### 2. Choose the documentation type

| Request signal                 | Deliverable                                         |
| ------------------------------ | --------------------------------------------------- |
| New project / missing README   | README                                              |
| Complex module layout or flows | Architecture doc                                    |
| HTTP endpoints / SDK methods   | API reference                                       |
| Confusing code sections        | Inline code comments                                |
| Design decision rationale      | ADR (format in `references/workflow_procedures.md`) |
| "How does this work?"          | README → Architecture → API → Comments              |

### 3. Generate from a template

1. Read the matching template from `assets/templates/`
2. Replace placeholders with real content discovered in step 1
3. Use concrete examples from the actual project — not generic `foo`/`bar`
4. Drop irrelevant sections rather than leaving `[placeholder]` text
5. For diagrams beyond a simple file tree, see `references/visual_aids_guide.md`
6. Cross-link related docs

### 4. Review

- Makes sense without prior knowledge of the project
- Setup steps are complete and testable
- Code examples point to real files in the project
- Scannable via headings, tables, and file trees — not a wall of text

## Templates

| Template                                     | Use for                        |
| -------------------------------------------- | ------------------------------ |
| `assets/templates/README.template.md`        | Project READMEs                |
| `assets/templates/ARCHITECTURE.template.md`  | System design, data flow, ADRs |
| `assets/templates/API.template.md`           | HTTP / SDK references          |
| `assets/templates/CODE_COMMENTS.template.md` | Inline documentation patterns  |

## References — load on demand

Load a reference only when needed. All three live under `references/`.

| File                          | Load when                                                           |
| ----------------------------- | ------------------------------------------------------------------- |
| `documentation_guidelines.md` | user asks for style, tone, or review-checklist guidance             |
| `visual_aids_guide.md`        | the doc needs a diagram beyond a basic file tree                    |
| `workflow_procedures.md`      | deeper codebase analysis, ADR format, or language-specific comments |

## Related skills

- `openapi-spec-generation` — machine-readable OpenAPI specs
- `changelog-automation` — release notes and changelog generation
