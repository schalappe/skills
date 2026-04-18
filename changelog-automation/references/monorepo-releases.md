# Monorepo Releases

Versioning and changelog strategies for multi-package repositories.

## Table of Contents

- [Decision: changesets vs release-please manifest](#decision)
- [changesets](#changesets)
- [release-please (manifest mode)](#release-please-manifest-mode)
- [Fixed vs Linked groups](#fixed-vs-linked-groups)
- [Snapshot / prerelease flows](#snapshot--prerelease-flows)

## Decision

| Situation                                                       | Pick                      |
| --------------------------------------------------------------- | ------------------------- |
| JS/TS workspace publishing to npm, contributors write changesets | **changesets**            |
| Polyglot monorepo (Node + Python + Rust + Go) in one repo        | **release-please**        |
| Internal-only packages, no npm publish, want GitHub release PRs | **release-please**        |
| Public JS library family with independent + linked versioning   | **changesets**            |

Both create a "release PR" that maintainers merge. Both generate per-package changelogs. Difference: changesets needs contributors to author `.changeset/*.md` files; release-please derives everything from Conventional Commit messages.

## changesets

### Initialize

```bash
# pnpm
pnpm add -Dw @changesets/cli @changesets/changelog-github
pnpm changeset init

# yarn
yarn add -DW @changesets/cli @changesets/changelog-github
yarn changeset init

# npm
npm install -D @changesets/cli @changesets/changelog-github
npx changeset init
```

### Configuration

```json
// .changeset/config.json
{
  "$schema": "https://unpkg.com/@changesets/config@3.0.0/schema.json",
  "changelog": [
    "@changesets/changelog-github",
    { "repo": "owner/repo" }
  ],
  "commit": false,
  "fixed": [],
  "linked": [["@myorg/core", "@myorg/utils"]],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": ["@myorg/internal-tool", "@myorg/dev-*"],
  "privatePackages": {
    "version": true,
    "tag": false
  }
}
```

### Contributor flow

```bash
# Contributor runs this per PR that changes a package
pnpm changeset

# Pick affected packages, pick bump type (patch/minor/major), write summary
# → creates .changeset/<random-name>.md

# Commit the changeset file with the PR
git add .changeset
git commit -m "feat(core): add retry policy"
```

### Release flow

```bash
# On main, consume all pending changesets and bump versions
pnpm changeset version
# → updates package.json versions + CHANGELOG.md per package

# Publish to npm
pnpm changeset publish
```

### GitHub Actions

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

concurrency: ${{ github.workflow }}-${{ github.ref }}

permissions:
  contents: write
  pull-requests: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "pnpm"

      - run: pnpm install --frozen-lockfile

      - name: Create Release Pull Request or Publish
        uses: changesets/action@v1
        with:
          version: pnpm changeset version
          publish: pnpm changeset publish
          commit: "chore: version packages"
          title: "chore: version packages"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## release-please manifest mode

Manifest mode tracks per-package versions in `.release-please-manifest.json`. Works across languages in one repo.

### Config

```json
// release-please-config.json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "bootstrap-sha": "abc123",
  "packages": {
    "packages/core": {
      "release-type": "node",
      "package-name": "@myorg/core",
      "changelog-path": "CHANGELOG.md"
    },
    "packages/cli": {
      "release-type": "node",
      "package-name": "@myorg/cli"
    },
    "services/api": {
      "release-type": "python",
      "package-name": "myorg-api"
    },
    "tools/migrator": {
      "release-type": "rust",
      "package-name": "migrator"
    }
  },
  "plugins": [
    {
      "type": "linked-versions",
      "groupName": "core-libs",
      "components": ["@myorg/core", "@myorg/cli"]
    }
  ]
}
```

```json
// .release-please-manifest.json
{
  "packages/core": "1.4.2",
  "packages/cli": "1.4.2",
  "services/api": "0.9.0",
  "tools/migrator": "0.3.1"
}
```

### GitHub Actions

```yaml
# .github/workflows/release-please.yml
name: Release Please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

Commits use the `path` prefix to scope releases:

```text
feat(packages/core)!: rename SessionToken to AuthToken
fix(services/api): handle empty query params
```

## Fixed vs Linked groups

**Fixed** — packages share the exact same version. Bump in one → bump in all. Use when packages are always published together (e.g. a coordinated SDK family).

```json
// changesets
{ "fixed": [["@myorg/react-*"]] }
```

**Linked** — packages only bump together *when changed in the same release*, but each keeps its own version number. Use for packages with tight compatibility but independent release cadence.

```json
// changesets
{ "linked": [["@myorg/core", "@myorg/utils"]] }
```

release-please equivalent is the `linked-versions` plugin (see config above).

## Snapshot / prerelease flows

### Changesets snapshot (PR previews)

Publish a disposable version tagged with the PR number for live testing:

```bash
# In a PR CI job
pnpm changeset version --snapshot pr-${{ github.event.number }}
pnpm changeset publish --tag snapshot --no-git-tag
```

Result: `@myorg/core@0.0.0-pr-123-20241018123456`. Users install with `npm i @myorg/core@snapshot`.

### Changesets prerelease mode

Enter a long-lived prerelease channel (e.g. `next`, `beta`):

```bash
pnpm changeset pre enter next
# ... normal flow: changeset add, version, publish ...
pnpm changeset pre exit
```

Versions bump as `1.3.0-next.0`, `1.3.0-next.1`, etc. `pre exit` clears the prerelease marker so the next `changeset version` produces a stable `1.3.0`.

### release-please prereleases

Set `prerelease: true` in the config for a branch, or use the `release-as` override in a commit footer:

```text
feat(packages/core): add experimental retry policy

Release-As: 2.0.0-beta.1
```
