---
name: changelog-automation
description: Use when automating changelogs, setting up conventional commits, generating release notes, configuring semantic versioning, standardizing commit messages, or creating a release workflow — even if the user just says "I want better release management" or "how should I version my project?"
---

# Changelog Automation

Patterns and tools for automating changelog generation, release notes, and version management following industry standards.

## Agent Workflow

### Step 1: Assess

1. **Ecosystem** — read `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` to infer language + package manager
2. **Existing setup** — grep for `commitlint`, `semantic-release`, `release-please`, `git-cliff`, `changesets`, `cocogitto`, `commitizen`
3. **Commit history** — `git log --oneline -20` to see if repo already follows Conventional Commits
4. **Changelog** — look for `CHANGELOG.md`, `HISTORY.md`, `RELEASES.md`
5. **Monorepo signals** — `pnpm-workspace.yaml`, `packages/*`, `workspaces` in `package.json`, Cargo workspace → jump to [monorepo-releases.md](references/monorepo-releases.md)

### Step 2: Pick a tool

Categorize by **workflow style**, not language. All tools below work on any Conventional Commits repo unless noted.

| Project profile                           | Recommended tool  | Why                                                                  |
| ----------------------------------------- | ----------------- | -------------------------------------------------------------------- |
| JS/TS library published to npm            | semantic-release  | Analyze → bump → publish → GitHub release in one pass                |
| JS/TS monorepo (workspace publishing)     | changesets        | Opt-in changeset files per PR, per-package bumps, fixed/linked groups |
| Polyglot app or lib (release-PR flow)     | release-please    | Language-agnostic release PR; Node/Python/Rust/Go/simple types       |
| Any repo (changelog only, bring-your-own) | git-cliff         | Fast, template-driven; no opinions on bump/tag/publish               |
| Any repo (opinionated CLI + CI)           | cocogitto (`cog`) | `cog bump` enforces commits, tags, writes changelog, runs hooks      |
| Python with native pyproject integration  | commitizen        | `cz bump`, `cz commit`, `version_files`, Python-first                |

### Step 3: Implement

1. **Commit linting** — install commitlint + husky (Node), or use `cz check` / `cog check` for Python + polyglot repos
2. **Configure the tool** — see [tool-setup-guides.md](references/tool-setup-guides.md)
3. **CI workflow** — add GitHub Actions for automated releases if requested
4. **Seed changelog** — generate initial `CHANGELOG.md` from existing history

### Step 4: Verify

1. Test commit linting with a properly formatted commit
2. Dry-run release to verify changelog generation
3. Confirm output follows [Keep a Changelog](https://keepachangelog.com/)

## Core Concepts

### Keep a Changelog format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- New feature X

## [1.2.0] - 2024-01-15

### Added

- User profile avatars

### Changed

- Improved loading performance by 40%

### Fixed

- Login timeout issue (#123)

### Security

- Updated dependencies for CVE-2024-1234

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
```

Sections: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

### Conventional Commits

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

| Type       | Meaning          | Changelog section |
| ---------- | ---------------- | ----------------- |
| `feat`     | New feature      | Added             |
| `fix`      | Bug fix          | Fixed             |
| `perf`     | Performance      | Changed           |
| `refactor` | Code restructure | Changed           |
| `docs`     | Documentation    | (excluded)        |
| `style`    | Formatting       | (excluded)        |
| `test`     | Tests            | (excluded)        |
| `chore`    | Maintenance      | (excluded)        |
| `ci`       | CI changes       | (excluded)        |
| `build`    | Build system     | (excluded)        |

Breaking change: append `!` (e.g. `feat(api)!:`) OR add `BREAKING CHANGE:` footer. Drives MAJOR bump.

### Semantic Versioning

```text
MAJOR.MINOR.PATCH

MAJOR: breaking changes (feat! or BREAKING CHANGE footer)
MINOR: new features (feat)
PATCH: bug fixes (fix, perf)
```

## Best Practices

**Do**

- Enforce Conventional Commits in CI (commitlint, `cog check`, `cz check`)
- Reference issues in commits: `Fixes #123`, `Closes #456`
- Keep scopes consistent across a repo (document the allowed list)
- Let automation write the changelog — never edit generated entries by hand
- Mark breaking changes with `!` or `BREAKING CHANGE:` footer

**Don't**

- Mix unrelated changes in one commit (one logical change per commit)
- Hand-edit release commits (bots will overwrite you)
- Skip commit validation locally then fight CI
- Forget the manifest file (release-please, `.release-please-manifest.json`) — most common cause of broken release PRs

## References

- [tool-setup-guides.md](references/tool-setup-guides.md) — commitlint, semantic-release, release-please, git-cliff, cocogitto, commitizen + GitHub Actions workflows
- [monorepo-releases.md](references/monorepo-releases.md) — changesets, release-please manifest mode, fixed/linked groups, snapshot releases
- [templates-and-examples.md](references/templates-and-examples.md) — release note templates + commit message examples

## External Resources

- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Changesets](https://github.com/changesets/changesets)
- [Cocogitto](https://docs.cocogitto.io/)

## Related Skills

- **codebase-documenter** — project documentation
- **api-design-principles** — API + webhook versioning
