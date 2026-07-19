# Future Tasks

Backlog of improvements, bugs, and features to implement. Ordered roughly by priority within each section.

---

## UX — Calibration

### Fix calibration interaction
- **Current state:** Camera.py `init_position()` silently loops forever if joints aren't visible. User has no idea what to do or what's wrong.
- **What it needs:**
  - Robot speaks a clear instruction when calibration starts: *"Please step back and raise your arms out to the sides"* (T-pose).
  - If specific joints are missing (elbow, wrist, hip all report 0,0,0), robot identifies which ones: *"I can't see your elbows — please step back a little"*.
  - Periodic reminder every ~5s if still not passing: *"Still waiting — raise your arms out to the sides like this"* (robot demonstrates T-pose).
  - Progress feedback: *"Almost there — I can see your shoulders and head, now I need your elbows and hips"*.
  - Timeout: after ~30s of failure, skip calibration and warn instead of hanging forever.
- **Files:** `code/Camera.py:init_position()`, `code/Audio.py`, new audio files `calibration_step_back.wav`, `calibration_raise_arms.wav`, `calibration_missing_elbow.wav`, `calibration_missing_hip.wav`, `calibration_complete.wav`.

### Voice + gesture guidance during calibration
- Robot should **demonstrate the T-pose** in CoppeliaSim while explaining (arms out to sides, held for ~2s).
- Robot speaks each phase:
  - "Starting calibration" → holds T-pose
  - "I can see you!" → when skeleton is first detected
  - "Perfect, hold it" → when count and angles are close
  - "Calibration complete, let's begin!" → on success
- Add visual progress indicator to the Tkinter GUI (e.g. a joint checklist or a simple text overlay on the camera thumbnail showing which joints are detected).
- **Files:** `code/Poppy.py` (T-pose method), `code/Screen.py` (GUI overlay), `code/Camera.py`.

---

## UX — Robot GUI

### Animated mouth + sympathetic smile on the robot eyes screen
- Current eyes screen (`pictures/eyes.png`) is a static image.
- When the robot speaks (`say(...)` is called), animate the mouth opening/closing in sync.
- Add a soft smile expression when the trainee completes a rep or an exercise successfully (triggered by `s.success_exercise = True`).
- Consider: a neutral resting face, a speaking face (mouth open), a happy face (wider eyes + smile), and an encouraging face (eyebrows raised).
- **Files:** `code/Screen.py`, `code/Audio.py` (hook into `say()` to trigger animation), `pictures/` (new face images or animated GIF).

---

## Phase 1 — LLM Feedback Translator (thesis core)

> See `CLAUDE.md` Thesis Context for full scope. These are the implementation sub-tasks.

- [ ] Map all `say(...)` call sites in `Training.py` and `Camera.py` — identify which ones are rule-based corrective feedback vs. static exercise names.
- [ ] Design `LLMFeedback.py` module interface: input (performance class, rep count, exercise name, which hand, angle delta), output (natural-language string).
- [ ] Choose TTS path: existing `pygame` audio files replaced by real-time TTS (e.g. `pyttsx3`, `gTTS`, or the robot's built-in voice), or LLM generates text → robot speaks via existing `say()` mechanism.
- [ ] Implement prompt template for the corrective feedback case (the highest-value target: rep 4, user counter ≤ 2).
- [ ] Keep rule-based `say()` as fallback if LLM call fails or times out.
- [ ] Evaluation: record LLM cues vs. rule-based cues for the same performance signal, compare trainee comprehension.

---

## Phase 2 — Voice Input (stretch goal)

> Only if Phase 1 is complete and there is time remaining.

- [ ] Add a microphone input thread (`VoiceInput.py`) running parallel to `Camera` / `MP`.
- [ ] Use Whisper (local) or a cloud STT API to transcribe trainee speech in real time.
- [ ] Feed transcribed text into `Settings.py` (e.g. `s.trainee_speech`), picked up by the LLM feedback context in Phase 1.
- [ ] Handle key commands: "stop", "slow down", "this hurts", "I'm ready".
- [ ] Graceful degradation: if mic not available / STT fails, system continues with camera-only input.

---

## Polish / tech debt

- Clean up `Pictures//icon.jpg` double-slash path in `code/main.py` (cosmetic, harmless).
- Delete accumulated `.venv.bak-*` directories periodically (`rm -rf .venv.bak-*`).
- `Training.py` `not done` prints are noisy — replace with a single heartbeat log per exercise.
- Make exercise order random (there's already a TODO in `Training.py`).
- Add a graceful shutdown: `Ctrl-C` currently kills mid-exercise; Training thread should finish the current exercise before exiting.
