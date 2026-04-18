# Release Notes Templates and Examples

Templates for release notes and examples of well-formatted commit messages.

## GitHub Release Template

```markdown
## What's Changed

### Features

{{ range .Features }}
- {{ .Title }} by @{{ .Author }} in #{{ .PR }}
{{ end }}

### Bug Fixes

{{ range .Fixes }}
- {{ .Title }} by @{{ .Author }} in #{{ .PR }}
{{ end }}

### Documentation

{{ range .Docs }}
- {{ .Title }} by @{{ .Author }} in #{{ .PR }}
{{ end }}

### Maintenance

{{ range .Chores }}
- {{ .Title }} by @{{ .Author }} in #{{ .PR }}
{{ end }}

## New Contributors

{{ range .NewContributors }}
- @{{ .Username }} made their first contribution in #{{ .PR }}
{{ end }}

**Full Changelog**: https://github.com/owner/repo/compare/v{{ .Previous }}...v{{ .Current }}
```

## Internal Release Notes Template

```markdown
# Release v2.1.0 - January 15, 2024

## Summary

This release introduces dark mode support and improves checkout performance
by 40%. It also includes important security updates.

## Highlights

### Dark Mode

Users can now switch to dark mode from settings. The preference is
automatically saved and synced across devices.

### Performance

- Checkout flow is 40% faster
- Reduced bundle size by 15%

## Breaking Changes

None in this release.

## Upgrade Guide

No special steps required. Standard deployment process applies.

## Known Issues

- Dark mode may flicker on initial load (fix scheduled for v2.1.1)

## Dependencies Updated

| Package | From    | To      | Reason                   |
| ------- | ------- | ------- | ------------------------ |
| react   | 18.2.0  | 18.3.0  | Performance improvements |
| lodash  | 4.17.20 | 4.17.21 | Security patch           |
```

## Commit Message Examples

### Feature with scope

```text
feat(auth): add OAuth2 support for Google login
```

### Bug fix with issue reference

```text
fix(checkout): resolve race condition in payment processing

Closes #123
```

### Breaking change

```text
feat(api)!: change user endpoint response format

BREAKING CHANGE: The user endpoint now returns `userId` instead of `id`.
Migration guide: Update all API consumers to use the new field name.
```

### Multi-paragraph commit

```text
fix(database): handle connection timeouts gracefully

Previously, connection timeouts would cause the entire request to fail
without retry. This change implements exponential backoff with up to
3 retries before failing.

The timeout threshold has been increased from 5s to 10s based on p99
latency analysis.

Fixes #456
Reviewed-by: @alice
```

### Other common types

```text
docs(readme): update installation instructions for v2

refactor(auth): extract token validation into middleware

perf(queries): add index on users.email for faster lookups

test(auth): add integration tests for OAuth flow

chore(deps): update dependencies to latest versions

ci(github): add caching to speed up CI pipeline
```
