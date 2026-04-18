# Git Rebase Deep Dive

Comprehensive guide to interactive rebase operations. Load this reference when cleaning up commit history or resolving complex rebase conflicts.

## Interactive Rebase Operations

### Available Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `pick` | `p` | Use commit as-is |
| `reword` | `r` | Use commit but edit message |
| `edit` | `e` | Use commit but stop for amending |
| `squash` | `s` | Meld into previous commit |
| `fixup` | `f` | Like squash but discard message |
| `drop` | `d` | Remove commit |
| `exec` | `x` | Run command |
| `break` | `b` | Stop here |

### Common Rebase Workflows

#### Squash Multiple Commits

```bash
# Start rebase
git rebase -i HEAD~4

# In editor, change to:
pick abc123 First commit
squash def456 Second commit
squash ghi789 Third commit
squash jkl012 Fourth commit

# Result: All commits squashed into first with combined message
```

#### Reword Commit Message

```bash
git rebase -i HEAD~3

# Change pick to reword:
reword abc123 Old message
pick def456 Second commit
pick ghi789 Third commit

# Editor opens to change message
```

#### Split a Commit

```bash
git rebase -i HEAD~3

# Mark commit with edit:
edit abc123 Big commit to split
pick def456 Other commit

# When rebase stops:
git reset HEAD^                    # Undo commit, keep changes
git add file1.py && git commit -m "Part 1"
git add file2.py && git commit -m "Part 2"
git rebase --continue
```

#### Reorder Commits

```bash
git rebase -i HEAD~4

# Simply change the order:
pick def456 Second commit
pick abc123 First commit    # Moved down
pick ghi789 Third commit
```

#### Drop a Commit

```bash
git rebase -i HEAD~3

# Change pick to drop:
pick abc123 Keep this
drop def456 Remove this
pick ghi789 Keep this too
```

## Autosquash Workflow

### Creating Fixup Commits

```bash
# Make initial commit
git commit -m "feat: add user authentication"
# commit hash: abc123

# Later, find a bug in that commit
git add fixed-file.py
git commit --fixup abc123

# Or use HEAD to fix the last commit
git commit --fixup HEAD

# Rebase with autosquash
git rebase -i --autosquash main
# Git automatically marks fixup commits with fixup!
```

### Squash vs Fixup

| Type | Message Handling |
|------|------------------|
| `squash` | Combines all messages in editor |
| `fixup` | Discards fixup commit message |

## Conflict Resolution

### During Rebase Conflicts

```bash
# When conflict occurs:
git status                    # See conflicting files

# Fix conflicts in files
# Remove conflict markers: <<<<<<<, =======, >>>>>>>

git add resolved-file.py      # Mark as resolved
git rebase --continue         # Continue rebase

# Or abort if stuck
git rebase --abort            # Return to pre-rebase state
```

### Complex Conflict Strategies

```bash
# Accept all changes from one side
git checkout --theirs path/to/file   # Accept incoming
git checkout --ours path/to/file     # Keep current

# Use merge tool
git mergetool

# Skip problematic commit
git rebase --skip
```

## Rebase onto Different Base

### Transplanting Branches

```bash
# Move feature branch from old-base to new-base
git rebase --onto new-base old-base feature-branch

# Example: Move feature from develop to main
git checkout feature
git rebase --onto main develop
```

### Removing Commits from Middle

```bash
# Remove commits C and D from: A-B-C-D-E-F
git rebase --onto B D
# Result: A-B-E'-F' (new hashes)
```

## Preserving Merge Commits

```bash
# Normal rebase flattens merge commits
git rebase -i main

# Preserve merge structure
git rebase -i --rebase-merges main
```

## Recovering from Rebase Mistakes

### Using Reflog

```bash
# See all HEAD movements
git reflog

# Find pre-rebase state
# Example output:
# abc123 HEAD@{0}: rebase finished
# def456 HEAD@{1}: rebase: ...
# ghi789 HEAD@{2}: commit: before rebase

# Restore to pre-rebase state
git reset --hard ghi789

# Or create recovery branch
git branch recovery-branch ghi789
```

### ORIG_HEAD

```bash
# Git stores previous HEAD in ORIG_HEAD
git reset --hard ORIG_HEAD
```

## Best Practices

### Safe Rebasing

1. **Never rebase pushed commits** unless you're the only one using the branch
2. **Create backup branch** before complex rebases
3. **Use --force-with-lease** instead of --force when pushing

```bash
# Safe force push
git push --force-with-lease origin feature-branch
```

### When to Rebase vs Merge

| Use Rebase | Use Merge |
|------------|-----------|
| Local commits not yet pushed | Shared branches |
| Clean linear history needed | Preserve collaboration history |
| Before creating PR | Integrating feature into main |

### Configuring Rebase Behavior

```bash
# Auto-squash by default
git config --global rebase.autoSquash true

# Auto-stash during rebase
git config --global rebase.autoStash true

# Use abbreviate commands
git config --global rebase.abbreviateCommands true
```
