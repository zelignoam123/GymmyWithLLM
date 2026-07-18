---
description: Launch the Gymmy trainer via ./run.sh (activates venv, checks CoppeliaSim on 19997, runs code/main.py)
argument-hint: "[extra args passed through to run.sh]"
allowed-tools: Bash(./run.sh:*)
---

Run the project entry point.

```bash
./run.sh $ARGUMENTS
```

Notes:
- `run.sh` will fail fast if `.venv` is missing (run `./setup.sh` first), if the venv is not x86_64, or if `pypot` can't import.
- It only warns (does not abort) if CoppeliaSim is not listening on port 19997 — launch CoppeliaSim first for simulator mode.
- All output is mirrored to `logs/run-<timestamp>.log`.
