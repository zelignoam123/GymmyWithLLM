---
description: End-of-session — append today's progress to PROGRESS.md, update TODO/blockers/critical path, set tomorrow's start point.
argument-hint: "[optional one-line focus, e.g. 'LLM feedback module']"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(mkdir:*), Bash(date:*), Read, Write, Edit
---

Wrap up today's work into `PROGRESS.md`. This is a SINGLE file — append, don't create new files.

## 1. Gather context

Run in parallel:
- `git status`
- `git diff --stat`
- `git log --since=midnight --oneline`
- Read `PROGRESS.md` to see current state

## 2. Update PROGRESS.md

Edit the file (don't overwrite). Do ALL of:

### A. Append a new session block
After the last `---` session separator, add:

```markdown
---

## Session N — YYYY-MM-DD

**Focus:** $ARGUMENTS (or infer)

### Completed
- What got done this session (past tense, verb-first)

### Architecture decisions
| Decision | Rationale |
(only if decisions were made)

### Issues resolved
| Error | Fix |
(only if errors were hit)
```

### B. Update the living sections
These sections are NOT per-session — they reflect CURRENT state:

- **Open Questions** — add new ones, mark resolved ones as RESOLVED
- **Blockers** — add/remove as status changes
- **TODO** — reorder, mark completed with ~~strikethrough~~, add new items, move [NEXT] tag
- **Critical Path** — mark completed steps with [DONE], advance [NEXT]
- **Future Work** — add any new ideas discussed

### C. Update the timestamp
Change `*Last updated: ...*` at the bottom.

## 3. Report back

Print:
1. Path: `PROGRESS.md`
2. 3-line summary: done / blocked / first action tomorrow
3. If uncommitted changes exist, show `git add` / `git commit` commands (don't commit)
4. Remind: "Type `/done` at end of every session"
