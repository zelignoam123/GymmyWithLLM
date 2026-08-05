# Gymmy Thesis — Progress Log

Single file tracking all progress, decisions, blockers, and next steps.
Updated at end of each session.

---

## Session 1 — 2026-07-18

**Focus:** CoppeliaSim + toolchain setup, camera fix, live preview

### Completed
- Set up complete simulator + robot toolchain on Apple Silicon Mac (Rosetta x86_64 venv, CoppeliaSim 4.1 Edu, pypot legacy remote API)
- Resolved 7 distinct environment errors from first clone to first successful app boot (Tk, scene loading, camera auth, thread safety)
- Fixed macOS camera-in-background-thread bug (moved `VideoCapture` to main thread)
- Added live camera thumbnail in training GUI so trainee can verify pose
- Added timestamped per-run log files and detailed boot-sequence progress prints
- Documented full setup in `RUN_INSTRUCTIONS.md`
- Defined thesis scope in `CLAUDE.md`: Phase 1 (LLM feedback translator), Phase 2 (voice input)

### Issues resolved
| Error | Fix |
|-------|-----|
| `No module named '_tkinter'` | `brew install python-tk@3.11` before venv |
| `pypot.vrep.io.VrepIOErrors: No value` | Pass `scene=_SCENE_PATH` to PoppyTorso() |
| CoppeliaSim 4.10+ port 19997 missing | Pin to CoppeliaSim Edu V4.1.0 (last with legacy API) |
| `OpenCV: not authorized to capture video` | Reset TCC, reopen terminal, trigger permission dialog |
| Empty camera frames from background thread | Move `VideoCapture` to main thread, share via `s.cap` |
| `cv2.error` in `imshow` from background | Disable `imshow`, add Tkinter thumbnail on main thread |

---

## Session 2 — 2026-08-03/04

**Focus:** LLM feedback module — design, TDD, implementation, Gemini API setup

### Completed
- Designed and implemented full LLM feedback pipeline architecture (Phase 1)
- Built `LLMFeedback.py`: static Hebrew cue map (38 features) + Gemini Flash wrapper + cross-session improvement detection
- Built `simulate_feedback.py`: hardware-free simulation of 6 feedback scenarios
- Built TDD test suite (`test_llm_feedback.py`): 22 assertions, 5 test cases, all passing
- Built `test_api_connection.py`: standalone API connectivity check
- Documented full pipeline in CLAUDE.md (38 features, feedback mapping, tradeoffs, API details)
- Set up Gemini API project + key infrastructure
- Established positive-tone feedback principle
- Added `google-genai` to requirements.txt
- Pushed commit `7d5d5a4` to `start_dev`

### Architecture decisions

| Decision | Rationale |
|----------|-----------|
| Static map is the core mechanism | Zero latency, always works, deterministic, no API dependency |
| LLM is optional wrapper on top | Adds phrasing variety + combination; falls back gracefully |
| Feature importance = coeff × standardized_value | Linear model → contribution is exact, no approximation needed |
| Pre-translate features to Hebrew before LLM | Reduces prompt cost, removes raw feature names from context |
| Cross-session improvement via contribution delta | Same formula, just compare prev vs current session |
| Positive tone only | "Try to reach..." not "You're not reaching..." |

### Interface contract (LLMFeedback.py)

```python
get_top_contributors(contributions: dict, n=3) -> list[tuple[str, float]]
features_to_cues(top_features: list, hand: str) -> list[str]
generate_feedback(context: dict) -> str
detect_improvement(prev, current, threshold=0.2) -> list[tuple[str, float, str]]
```

### Issues resolved
| Error | Fix |
|-------|-----|
| `google-genai>=2.16.0` requires Python 3.10+ | Lowered to `>=1.47.0` (compatible with Python 3.9, same API) |
| Git push auth failed (password not supported) | Switch to `gh auth login` + HTTPS |
| Git push denied (`noamzelig123` vs `zelignoam123`) | Login as repo owner account |

---

## Open Questions

| # | Question | Priority | Context |
|---|----------|----------|---------|
| 1 | **Gemini API `limit: 0`** — key authenticates but quota is 0 on all models | HIGH | Project: `project-0c4af6c5-9e91-4c42-a19`. May need yet another new project or manual API enable |
| 2 | **Model coefficient extraction** — how exactly to access params from `model2.sav` | HIGH | Statsmodels regression: `model.params` + `model.model.data.xnames` |
| 3 | **TTS for Hebrew** — which engine to use for speaking LLM output | MEDIUM | Options: gTTS (free/internet), edge-tts (free/good Hebrew), pyttsx3 (offline/weak) |
| 4 | **Python 3.9 EOL** — google-auth warns, works but upgrade venv eventually | LOW | Non-blocking |

## Blockers

| Blocker | Impact | Workaround |
|---------|--------|------------|
| Gemini API quota = 0 | Can't test LLM rephrasing live | Static map works perfectly as fallback; LLM is optional polish |

## TODO (priority order)

1. **[NEXT] Fix Gemini API** — create key in brand new project at https://aistudio.google.com/apikey → "Create in new project". Test: `python code/test_api_connection.py`
2. **Wire real model coefficients** — load `model2.sav`, extract `model.params`, compute real contributions from exercise data
3. **Integrate into Camera.py** — replace `say(exercise_name + "_" + str(flag))` at line 190/249 with `LLMFeedback.generate_feedback(context)` (keep old path as fallback)
4. **Add session persistence** — save contribution JSONs to `sessions/`, load previous at startup
5. **Add TTS** — convert LLM Hebrew text to speech
6. **Test end-to-end** — run full exercise with robot, verify feedback fires correctly

## Critical Path to Thesis Success

```
[DONE] 1. Understand existing pipeline (ML model, features, trigger logic)
[DONE] 2. Design LLM integration point (between classifier and audio)
[DONE] 3. Build LLMFeedback.py with static map + LLM wrapper
[DONE] 4. Build simulation harness for hardware-free iteration
  ↓
[NEXT] 5. Wire real model coefficients → real feature contributions
[NEXT] 6. Integrate into Camera.py (with fallback to old .wav path)
[    ] 7. Get Gemini API working → test LLM rephrasing quality
[    ] 8. Add TTS (Hebrew text → speech)
[    ] 9. Add cross-session persistence
[    ] 10. Run user study comparing old feedback vs LLM feedback
[    ] 11. Write thesis chapter on LLM integration results
```

## Future Work (Phase 2 — only if Phase 1 complete)

- Voice input from trainee (speech-to-text → LLM context)
- Multi-turn conversation with the robot
- LLM adapts based on trainee's verbal responses

---

*Last updated: 2026-08-04*
