---
name: changelog-automation
description: Use when automating changelogs, setting up conventional commits, generating release notes, configuring semantic versioning, standardizing commit messages, or creating a release workflow — even if the user just says "I want better release management" or "how should I version my project?"
---

# Changelog Automation

Patterns and tools for automating changelog generation, release notes, and version management following industry standards.

## Agent Workflow

Follow these steps when invoked:

### Step 1: Assess the Project

1. **Identify the ecosystem** — Read `package.json`, `pyproject.toml`, `Cargo.toml`, or other config files to determine the language and package manager
2. **Check existing setup** — Grep for `commitlint`, `semantic-release`, `release-please`, `git-cliff`, or `commitizen` in config files and dependencies
3. **Review commit history** — Run `git log --oneline -20` to see if the project already follows conventional commits
4. **Check for existing changelog** — Look for `CHANGELOG.md`, `HISTORY.md`, or `RELEASES.md`

### Step 2: Choose a Tool

Use this decision framework based on project needs:

| Project Type | Recommended Tool | Why |
| --- | --- | --- |
| Node.js library (npm publish) | semantic-release | Full automation: versioning, npm publish, GitHub releases |
| Node.js app (no publish) | release-please | Generates release PRs with changelog and version bumps |
| Rust project | git-cliff | Fast, native Rust, flexible Tera templates |
| Python project | commitizen | Native Python, pyproject.toml integration |
| Any project (CI-first) | release-please via GitHub Actions | Language-agnostic, works with any project |
| Monorepo | release-please or semantic-release | Both support multi-package workspaces |

### Step 3: Implement

1. **Set up commit linting** — Install commitlint + husky to enforce Conventional Commits (see `references/tool-setup-guides.md`)
2. **Configure the chosen tool** — Follow the setup guide for the selected tool in `references/tool-setup-guides.md`
3. **Add CI workflow** — Set up GitHub Actions for automated releases if the user wants CI integration
4. **Create initial changelog** — Generate a CHANGELOG.md from existing commits if possible

### Step 4: Verify

1. Test commit linting with a properly formatted commit
2. Run a dry-run release to verify changelog generation
3. Confirm the generated changelog follows Keep a Changelog format

## Core Concepts

### 1. Keep a Changelog Format

The standard format for human-readable changelogs:

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
- Dark mode support

### Changed

- Improved loading performance by 40%

### Fixed

- Login timeout issue (#123)

### Security

- Updated dependencies for CVE-2024-1234

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
```

### 2. Conventional Commits

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

| Type       | Description      | Changelog Section  |
| ---------- | ---------------- | ------------------ |
| `feat`     | New feature      | Added              |
| `fix`      | Bug fix          | Fixed              |
| `docs`     | Documentation    | (usually excluded) |
| `style`    | Formatting       | (usually excluded) |
| `refactor` | Code restructure | Changed            |
| `perf`     | Performance      | Changed            |
| `test`     | Tests            | (usually excluded) |
| `chore`    | Maintenance      | (usually excluded) |
| `ci`       | CI changes       | (usually excluded) |
| `build`    | Build system     | (usually excluded) |
| `revert`   | Revert commit    | Removed            |

### 3. Semantic Versioning

```text
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (feat! or BREAKING CHANGE footer)
MINOR: New features (feat)
PATCH: Bug fixes (fix)
```

## Best Practices

### Do's

- **Follow Conventional Commits** — Enables all automation tools
- **Write clear commit messages** — Future maintainers will thank you
- **Reference issues** — Link commits to tickets with `Fixes #123`
- **Use scopes consistently** — Define team conventions for scope names
- **Automate releases** — Reduce manual errors and forgotten steps

### Don'ts

- **Don't mix unrelated changes** — One logical change per commit
- **Don't skip commit validation** — Use commitlint to enforce conventions
- **Don't manually edit generated changelogs** — Automation-generated only
- **Don't forget breaking changes** — Mark with `!` suffix or `BREAKING CHANGE` footer
- **Don't ignore CI validation** — Validate commit messages in the pipeline

## Reference Files

For tool-specific setup and configuration:

- **`references/tool-setup-guides.md`** — Step-by-step setup for commitlint, release-please, semantic-release, git-cliff, commitizen, and GitHub Actions workflows
- **`references/templates-and-examples.md`** — Release note templates (GitHub and internal) and commit message examples

Load references when implementing a specific tool or when the user needs templates for release notes.

## External Resources

- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

## Related Skills

- **codebase-documenter** — General project documentation
- **openapi-spec-generation** — API specification patterns
