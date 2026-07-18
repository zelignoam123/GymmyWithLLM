---
description: Wrap up the session — write a dated log to sessions/ with what changed, what's blocked, what to do tomorrow, and thesis-progress bullets. Then commit-ready summary.
argument-hint: "[optional one-line focus, e.g. 'CoppeliaSim + Tk setup']"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(mkdir:*), Bash(date:*), Read, Write, Edit
---

Wrap up today's work. Follow the steps in order — do not skip.

## 1. Gather context

Run in parallel:
- `git status` — what's modified/untracked right now
- `git diff --stat` — line counts per file for quick scope read
- `git diff` — full working-tree diff (for anything committed today, also `git log --since=midnight --oneline`)
- Also read the earlier assistant/user messages in this conversation — the summary must reflect what *we did in this session*, including changes I only described but didn't `git commit`.

## 2. Write the session log

Path: `sessions/YYYY-MM-DD.md` (use today's date from `date +%Y-%m-%d`). Create the `sessions/` folder if it doesn't exist. If a file for today already exists, append a new `## <HH:MM> — <focus>` block instead of overwriting.

Template — fill every section, drop any that would be empty:

```markdown
# Session — YYYY-MM-DD

**Focus:** $ARGUMENTS  (or infer one from the diff / conversation)

## What changed
- Bullet per meaningful edit. Reference files as `path:line` links. State the *why*, not just the *what*.
- Group by file if there are many small edits to the same file.

## What broke and how we fixed it
- The runtime errors we actually hit this session, and the fix. This is the highest-value section for future-me — keep it concrete.
- Include the exact error message (one line) so it's greppable next time it recurs.

## Still blocked / open questions
- Anything left unresolved. Be honest — "I don't know if X works because I couldn't test it" belongs here.

## Tomorrow — start here
- Concrete next actions, ordered. Each one should be small enough to do in under an hour.
- If a specific command is the very next step, include it verbatim in a code block.

## Thesis-progress bullets
Short, presentable phrases suitable for a slide / advisor update. Past tense, verb-first, no jargon the advisor wouldn't know:
- "Set up simulator + robot toolchain on Apple Silicon (Rosetta, x86_64 venv, CoppeliaSim 4.1)"
- "Added progress logging + timestamped per-run log files"
- etc.
```

## 3. Report back

After writing the file, print:
1. The full path to the session log.
2. A 3-5 line executive summary (what got done, what's blocked, first action tomorrow).
3. If there are uncommitted changes on disk, remind the user with the exact `git add / git commit` command they'd need — but do **not** commit unless they explicitly ask.

Do not run tests, linters, or the app. This is a wrap-up, not a verify.
