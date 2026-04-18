# Tool Setup Guides

Step-by-step setup guides for changelog automation tools.

## Table of Contents

- [Commit Linting (commitlint + husky)](#commit-linting)
- [release-please](#release-please)
- [semantic-release](#semantic-release)
- [GitHub Actions Workflows](#github-actions-workflows)
- [git-cliff](#git-cliff)
- [commitizen (Python)](#commitizen-python)

## Commit Linting

Set up commitlint with husky to enforce Conventional Commits on every commit:

```bash
# Install tools
npm install -D @commitlint/cli @commitlint/config-conventional
npm install -D husky

# Setup commitlint
cat > commitlint.config.js << 'EOF'
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'docs',
        'style',
        'refactor',
        'perf',
        'test',
        'chore',
        'ci',
        'build',
        'revert',
      ],
    ],
    'subject-case': [2, 'never', ['start-case', 'pascal-case', 'upper-case']],
    'subject-max-length': [2, 'always', 72],
  },
};
EOF

# Setup husky
npx husky init
echo "npx --no -- commitlint --edit \$1" > .husky/commit-msg
```

## release-please

Google's release automation tool. Creates release PRs that update changelog and version when merged.

### Configuration

Create `release-please-config.json` in the project root:

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "node",
  "packages": {
    ".": {
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true,
      "bump-patch-for-minor-pre-major": true
    }
  }
}
```

Create `.release-please-manifest.json`:

```json
{
  ".": "1.0.0"
}
```

### Supported Release Types

| Type | Language/Ecosystem |
| --- | --- |
| `node` | Node.js (package.json) |
| `python` | Python (setup.py, setup.cfg, pyproject.toml) |
| `rust` | Rust (Cargo.toml) |
| `go` | Go (no version file needed) |
| `simple` | Any project (version.txt) |

### GitHub Actions Integration

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
```

### Package.json Scripts

```json
{
  "scripts": {
    "release:dry": "release-please release-pr --dry-run --repo-url=owner/repo"
  }
}
```

## semantic-release

Full automation: analyzes commits, determines version bump, generates changelog, publishes to npm, and creates GitHub releases.

```javascript
// release.config.js
module.exports = {
  branches: [
    "main",
    { name: "beta", prerelease: true },
    { name: "alpha", prerelease: true },
  ],
  plugins: [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/changelog",
      {
        changelogFile: "CHANGELOG.md",
      },
    ],
    [
      "@semantic-release/npm",
      {
        npmPublish: true,
      },
    ],
    [
      "@semantic-release/github",
      {
        assets: ["dist/**/*.js", "dist/**/*.css"],
      },
    ],
    [
      "@semantic-release/git",
      {
        assets: ["CHANGELOG.md", "package.json"],
        message:
          "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}",
      },
    ],
  ],
};
```

## GitHub Actions Workflows

### Automated Release with semantic-release

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - run: npm ci

      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Run semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npx semantic-release
```

### Manual Release with git-cliff

```yaml
# .github/workflows/manual-release.yml
name: Manual Release

on:
  workflow_dispatch:
    inputs:
      release_type:
        description: "Release type"
        required: true
        default: "patch"
        type: choice
        options:
          - patch
          - minor
          - major

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Install git-cliff
        run: cargo install git-cliff || npm install -g git-cliff

      - name: Bump version and generate changelog
        id: version
        run: |
          # Get current version from package.json (or adapt for your project)
          CURRENT=$(node -p "require('./package.json').version")

          # Calculate next version
          IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
          case "${{ inputs.release_type }}" in
            major) NEXT="$((MAJOR+1)).0.0" ;;
            minor) NEXT="${MAJOR}.$((MINOR+1)).0" ;;
            patch) NEXT="${MAJOR}.${MINOR}.$((PATCH+1))" ;;
          esac

          echo "tag=v${NEXT}" >> "$GITHUB_OUTPUT"

          # Update version in package.json
          npm version "$NEXT" --no-git-tag-version

          # Generate changelog
          git cliff --tag "v${NEXT}" -o CHANGELOG.md

          # Commit and tag
          git add -A
          git commit -m "chore(release): v${NEXT}"
          git tag "v${NEXT}"

      - name: Push changes
        run: git push --follow-tags origin main

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.version.outputs.tag }}
          generate_release_notes: true
```

## git-cliff

Rust-based changelog generator. Fast, flexible, works with any project.

```bash
# Install
cargo install git-cliff
# or
npm install -g git-cliff
```

### Configuration

```toml
# cliff.toml
[changelog]
header = """
# Changelog

All notable changes to this project will be documented in this file.

"""
body = """
{% if version %}\
    ## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
    ## [Unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | upper_first }}
    {% for commit in commits %}
        - {% if commit.scope %}**{{ commit.scope }}:** {% endif %}\
            {{ commit.message | upper_first }}\
            {% if commit.github.pr_number %} ([#{{ commit.github.pr_number }}](https://github.com/owner/repo/pull/{{ commit.github.pr_number }})){% endif %}\
    {% endfor %}
{% endfor %}
"""
footer = """
{% for release in releases -%}
    {% if release.version -%}
        {% if release.previous.version -%}
            [{{ release.version | trim_start_matches(pat="v") }}]: \
                https://github.com/owner/repo/compare/{{ release.previous.version }}...{{ release.version }}
        {% endif -%}
    {% else -%}
        [unreleased]: https://github.com/owner/repo/compare/{{ release.previous.version }}...HEAD
    {% endif -%}
{% endfor %}
"""
trim = true

[git]
conventional_commits = true
filter_unconventional = true
split_commits = false
commit_parsers = [
    { message = "^feat", group = "Features" },
    { message = "^fix", group = "Bug Fixes" },
    { message = "^doc", group = "Documentation" },
    { message = "^perf", group = "Performance" },
    { message = "^refactor", group = "Refactoring" },
    { message = "^style", group = "Styling" },
    { message = "^test", group = "Testing" },
    { message = "^chore\\(release\\)", skip = true },
    { message = "^chore", group = "Miscellaneous" },
]
filter_commits = false
tag_pattern = "v[0-9]*"
skip_tags = ""
ignore_tags = ""
topo_order = false
sort_commits = "oldest"

[github]
owner = "owner"
repo = "repo"
```

### Usage

```bash
# Generate full changelog
git cliff -o CHANGELOG.md

# Generate for specific range
git cliff v1.0.0..v2.0.0 -o RELEASE_NOTES.md

# Preview without writing
git cliff --unreleased --dry-run
```

## commitizen (Python)

Python-native commit standardization and changelog generation.

```bash
# Install
pip install commitizen
# or
uv add --dev commitizen
```

### Configuration

```toml
# pyproject.toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "1.0.0"
version_files = [
    "pyproject.toml:version",
    "src/__init__.py:__version__",
]
tag_format = "v$version"
update_changelog_on_bump = true
changelog_incremental = true
changelog_start_rev = "v0.1.0"

[tool.commitizen.customize]
message_template = "{{change_type}}{% if scope %}({{scope}}){% endif %}: {{message}}"
schema = "<type>(<scope>): <subject>"
schema_pattern = "^(feat|fix|docs|style|refactor|perf|test|chore)(\\(\\w+\\))?:\\s.*"
bump_pattern = "^(feat|fix|perf|refactor)"
bump_map = {"feat" = "MINOR", "fix" = "PATCH", "perf" = "PATCH", "refactor" = "PATCH"}
```

### Usage

```bash
# Create commit interactively
cz commit

# Bump version and update changelog
cz bump --changelog

# Check commits follow conventions
cz check --rev-range HEAD~5..HEAD

# Dry run
cz bump --dry-run
```
