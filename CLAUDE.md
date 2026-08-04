# Gymmy Thesis - Adaptive Physical Exercise Training System

## Thesis Context

This repository is the codebase for **Noam Zelig's Master's thesis**. The existing system was inherited from an earlier project (adaptive exercise training with a Poppy Torso robot + MediaPipe pose tracking + ML performance classification). The thesis contribution being added on top is:

**Goal: integrate an LLM into the training loop.**

Two phases, in priority order:

1. **Phase 1 — LLM as a feedback translator (primary contribution).**
   Today the system decides *what* to say to the trainee via hardcoded audio files (`audio files/{lang}/{gender}/*.wav`) triggered by rule-based logic (e.g. "corrective feedback fires at rep 4 if user counter ≤ 2"). This is rigid, robotic, and doesn't adapt phrasing to context. Phase 1 replaces the hardcoded verbal feedback path with an LLM that takes the current performance signals (angle data, ML performance class, rep counts, which hand is problematic, exercise name) and generates a **natural, human-understandable coaching cue**, which the robot then speaks to the trainee. The robot remains the delivery channel; the LLM sits between the classifier and the audio output.

2. **Phase 2 — Voice input from the trainee (stretch goal, only if Phase 1 lands).**
   Today the *only* input signal from the trainee is the camera / MediaPipe skeleton. Phase 2 adds a **voice input channel** so the trainee can talk back to the robot ("this hurts my shoulder", "slow down", "I'm ready"), and the LLM incorporates that natural-language input into its next feedback turn. The camera stays as the pose-tracking sensor; voice is added *alongside* it as a second modality, not as a replacement. Feasibility is uncertain — this is only pursued if there's time after Phase 1.

**What this means for future sessions:**
- Any change that touches feedback generation, audio playback, or the `say(...)` path is thesis-relevant — flag it and ask before altering behavior in a way that would conflict with the LLM integration point.
- The natural insertion point for Phase 1 is between `performance_classification.py` (produces the class) and `Audio.py::say(...)` (speaks the .wav). A new module (e.g. `LLMFeedback.py`) should own the prompt construction + LLM call + TTS handoff.
- Voice input (Phase 2) will need a new thread parallel to `Camera` / `MP`, feeding into `Settings.py` the same way pose data does.
- Don't refactor the existing rule-based feedback out yet — Phase 1 needs it as the fallback path and as the ground-truth baseline for the thesis evaluation.

## Project Overview

This is a research project implementing an adaptive physical exercise training system that combines:
- **Poppy Torso robot** - demonstrates physical exercises
- **MediaPipe pose detection** - tracks user movements via camera
- **Machine learning** - classifies exercise performance quality
- **Adaptive feedback** - adjusts training based on real-time performance
- **LLM (planned, thesis contribution)** - generates natural coaching cues from performance signals; optional voice input in a later phase

## Session Onboarding

Before answering the first substantive question of a new session, do this in parallel:
1. `ls sessions/ 2>/dev/null | tail -3` — read the most recent session log if one exists. That file's "Tomorrow — start here" section is the highest-signal context for where work left off.
2. `git log --oneline -10` — last ten commits on this branch.
3. `git status` — current working tree state.

Skip this only if the user's opening message is a trivial one-liner ("what does file X do?"). For any task that will touch behavior, start with the session log.

## Architecture & Core Components

### Multi-threaded System

All components run as separate threads:

1. **Training.py** - Main training flow orchestrator, manages exercise sequences
2. **Poppy.py** - Robot control thread (6 upper-body exercises)
3. **Camera.py** - Pose tracking and performance evaluation
4. **MP.py** - MediaPipe processing (socket-based communication)
5. **Screen.py** - GUI with robot "eyes"
6. **Audio.py** - Voice feedback system

### Key Design Patterns

- All major components inherit from `threading.Thread`
- Inter-thread communication via global `Settings.py` variables
- Socket-based (UDP port 7000) communication between MP.py and Camera.py
- Exercises follow naming convention: `{exercise_name}` with optional `_one_hand` suffix

## Exercise Catalog

Six exercises with angle-based recognition:

1. **raise_arms_horizontally** - Arms to sides (2 angles tracked)
2. **bend_elbows** - Elbow flexion (1 angle tracked)
3. **raise_arms_bend_elbows** - Combined movement (2 angles)
4. **open_and_close_arms** - Arm opening (2 angles)
5. **open_and_close_arms_90** - 90° arm opening (2 angles)
6. **raise_arms_forward** - Forward arm raise (2 angles)

Each has `_one_hand` variant for adaptive training focusing on problematic side.

## Adaptive Training Logic

The system adapts based on performance:

1. **Initial Assessment** - First 2 exercises evaluate both hands
2. **Performance Classification** - ML model (`performance_evaluation_model.sav` or `model2.sav`) predicts performance quality (lower score is better)
3. **Decision Making**:
   - Both hands problematic (sum > 1.1) → corrective feedback for both
   - Right hand problematic → focused training on right hand with mirrored robot demo
   - Left hand problematic → focused training on left hand with mirrored robot demo
   - No problems → user-led training (robot doesn't count, user tries again on failure)
4. **Repeat Assessment** - Runs initial 2 exercises again to measure improvement

## Classification & Feedback Pipeline

All classification and feedback happens **intra-session in real time** — not between sessions.

```
Camera.py (collects angle timeseries per exercise)
    → performance_classification.py::feature_extraction() (38 features per hand)
        → performance_classification.py::predict_performance() (statsmodels regression → float score)
            → s.performance_class[exercise] = {'right': score, 'left': score}
                → Training.py line 59-79 (sum > 1.1 → adaptation decision)
                    → Camera.py line 190/249 (corrective feedback trigger mid-exercise)
                        → Audio.py say(exercise_name + "_" + str(flag)) → plays .wav
```

### Timing within a session

1. User does exercise → Camera.py tracks angles → exercise ends
2. **Immediately**: `classify_performance()` extracts features from the angle data, predicts score
3. After both assessment exercises complete → Training.py makes adaptation decision
4. During subsequent exercises → corrective feedback fires mid-rep if user is struggling

### Feature List (38 features per hand)

Extracted from the angle timeseries by `performance_classification.py::feature_extraction()`:

**Repetition features** (aggregated mean + std across all reps):
| # | Feature | Measures |
|---|---------|----------|
| 1 | `rep_count` | Number of completed reps detected |
| 2-3 | `start_value_mean/std` | Angle at rep start — consistency of starting position |
| 4-5 | `peak_value_mean/std` | Angle at rep peak — consistency of full range of motion |
| 6-7 | `end_value_mean/std` | Angle at rep end — consistency of return position |
| 8-9 | `num_frames_up_mean/std` | Time (frames) for raising phase — rhythm consistency |
| 10-11 | `num_frames_down_mean/std` | Time (frames) for lowering phase — rhythm consistency |

**Velocity & acceleration features** (per phase, aggregated mean + std):
| # | Feature | Measures |
|---|---------|----------|
| 12-13 | `vel_mean_up_mean/std` | Raising speed — are you moving fast enough upward |
| 14-15 | `vel_sd_up_mean/std` | Smoothness during raise — jerky vs fluid |
| 16-17 | `acc_mean_up_mean/std` | Raising acceleration — momentum building |
| 18-19 | `acc_sd_up_mean/std` | Jerk during raise — stability of effort |
| 20-21 | `vel_mean_down_mean/std` | Lowering speed — controlled descent |
| 22-23 | `vel_sd_down_mean/std` | Smoothness during lower — controlled vs dropping |
| 24-25 | `acc_mean_down_mean/std` | Lowering acceleration — gravity vs control |
| 26-27 | `acc_sd_down_mean/std` | Jerk during lower — stability of descent |

**FFT (frequency) features:**
| # | Feature | Measures |
|---|---------|----------|
| 28 | `freq_num` | Number of frequency components — movement complexity |
| 29-30 | `magnitude_mean/sd` | Spectral energy distribution — rhythmic consistency |
| 31-32 | `DF1_freq/mag` | Dominant frequency — main movement rhythm |
| 33-34 | `DF2_freq/mag` | 2nd dominant frequency — secondary pattern |
| 35-36 | `DF3_freq/mag` | 3rd dominant frequency — tertiary pattern |
| 37 | `CL` | Cycle length (frames per rep) — pacing |
| 38 | `cycles_num` | Number of movement cycles — completeness |

### Feature-to-Feedback Mapping (positive tone)

Each feature maps to an actionable, positive coaching cue:

| Feature group | Positive coaching cue (Hebrew intent) |
|---------------|--------------------------------------|
| `peak_value` low | "Try reaching full range of motion with your {hand}" |
| `start_value` inconsistent | "Try starting each rep from the same position" |
| `vel_sd_up` high | "Try moving more smoothly on the way up" |
| `vel_sd_down` high | "Try lowering your arms with a steady pace" |
| `vel_mean_up` low | "Try picking up the pace a bit on the way up" |
| `vel_mean_down` too fast | "Try controlling the descent — a little slower" |
| `num_frames_up` inconsistent | "Try keeping the same rhythm for each rep" |
| `CL` too long | "Try shortening your reps a bit — keep momentum" |
| `rep_count` low | "Try completing the full set of repetitions" |
| `acc_sd` high | "Try keeping your movement steady — less jerky" |

### Where the LLM fits in this pipeline

The LLM replaces **only the last step** — the rigid `say(filename)` call:

```
[EXISTING - stays unchanged]
Camera.py → feature_extraction → predict_performance → s.performance_class → Training.py decision

[EXISTING trigger - stays unchanged]
Camera.py line 190: if corrective_feedback and robot_rep >= rep/2 and counter <= 2:

[OLD - hardcoded]
    say(exercise_name + "_" + str(flag))  →  plays generic .wav

[NEW - LLM replaces this]
    context = {features, scores, top_3_contributors, exercise, hand, flag, angle...}
    feedback_text = LLMFeedback.generate(context)  →  natural Hebrew cue via TTS
```

The LLM receives the **top 3 features that most impacted the score** (via model coefficient × standardized value) and generates a **positive, specific, context-aware Hebrew coaching cue** that addresses those exact weaknesses. The ML model still decides *whether* to give feedback; the LLM decides *how to phrase it*.

### LLM vs Static Map — Tradeoff Table

| Aspect | Static map (dict lookup) | LLM |
|--------|--------------------------|-----|
| Latency | ~0ms | 500-2000ms (API call + TTS) |
| Cost | Free | Per-token API cost |
| Phrasing variety | Same sentence every time | Different phrasing each time |
| Combining cues | Concatenates 3 separate sentences | Merges into one fluent coaching turn |
| Progress-awareness | Can do with if/else on improvement delta | Natural ("you're getting closer!") |
| Offline/no-internet | Works always | Fails without connectivity |
| Thesis contribution | "feature-importance-based feedback" | "LLM-generated natural coaching" |
| Implementation effort | 1 dict + format() | Prompt engineering + API integration + TTS |
| Determinism | 100% reproducible | Varies per call |

**Recommended approach**: Static map as the **core mechanism** (always works, zero latency). LLM as an **optional wrapper** that takes the 3 static cues + context and rephrases them into one natural sentence. Fallback to static map if LLM fails/times out.

### Cross-Session Improvement Tracking

**Goal**: Detect improvement between sessions and add positive reinforcement ("Your range of motion improved since last time!")

**What to compare**: The **contribution** per feature = `coefficient × standardized_value`. Coefficients are fixed model weights; what changes between sessions is the user's actual feature values.

```
contribution_i = coefficient_i × ((feature_value_i - mean_i) / std_i)
```

**How it works**:

1. After each session's `predict_performance()`, save per-hand contributions dict:
   ```python
   # Saved to file: sessions/{participant_code}_{exercise}_{date}.json
   {
       "exercise": "raise_arms_horizontally",
       "hand": "right",
       "date": "2026-08-03",
       "contributions": {
           "peak_value_mean": 1.2,
           "vel_sd_up_mean": 0.8,
           "start_value_std": 0.3,
           ...
       },
       "total_score": 1.5
   }
   ```

2. At start of next session, load previous contributions for the same exercise+hand

3. Compare: `delta_i = prev_contribution_i - current_contribution_i` (positive delta = improvement)

4. Top improved features get positive reinforcement in feedback:
   ```python
   IMPROVEMENT_FEEDBACK = {
       'peak_value': "טווח התנועה שלך השתפר מהפעם הקודמת עם יד {hand}!",
       'vel_sd_up': "התנועה שלך חלקה יותר מהפעם הקודמת!",
       'num_frames_up': "הקצב שלך יציב יותר — כל הכבוד!",
       ...
   }
   ```

**Calculation summary**:
- Same contribution formula: `coeff × standardized_value`
- Compare across sessions (not within): `prev_session - current_session`
- Positive delta → feature improved → add positive feedback
- Threshold for "meaningful" improvement: delta > 0.2 (prevents noise)
- Only comment on features that were previously in the top-3 problematic (user heard about them)

**Storage**: One JSON file per session/exercise/hand in a `sessions/` directory. Lightweight, human-readable, no database needed.

## Code Conventions

### Important Implementation Details

- **3D Angle Calculation**: Uses `calc_angle_3d()` with numpy for joint angle measurement from (x,y,z) coordinates
- **Exercise Recognition**: Two-threshold system (up_lb/up_ub, down_lb/down_ub) with flag toggling for rep counting
- **Corrective Feedback**: Triggers at rep 4 (`robot_rep >= rep/2`) if user counter ≤2
- **Performance Features**: Extracts velocity, acceleration, FFT features from movement data via `performance_classification.py`
- **Data Export**: Excel workbook per participant with per-exercise sheets containing joint data and performance classifications

### Critical Settings Variables

Located in `Settings.py`:

- `s.adaptive` - Enable/disable adaptive mode (True/False)
- `s.corrective_feedback` - Provide verbal guidance during exercise (True/False)
- `s.one_hand` - Focus training: `False`, `'left'`, or `'right'`
- `s.robot_count` - Whether robot counts reps aloud (True/False)
- `s.rep` - Default 8 repetitions per exercise
- `s.req_exercise` - Current exercise name (coordination signal between threads)
- `s.finish_workout` - Signal to terminate all threads
- `s.poppy_done` / `s.camera_done` - Synchronization flags
- `s.waved` - User wave detection flag
- `s.calibration` - Calibration complete flag
- `s.participant_code` - Unique ID for data files

### Thread Synchronization Pattern

Threads coordinate using global flags:

```python
# Training sets exercise name
s.req_exercise = "raise_arms_horizontally"

# Robot and Camera execute in parallel
# Each sets their done flag when complete
s.poppy_done = True
s.camera_done = True

# Training waits for both
while (not s.poppy_done) or (not s.camera_done):
    time.sleep(1)

# Reset for next exercise
s.poppy_done = False
s.camera_done = False
```

## Development Workflow

### Running the System

```bash
python code/main.py
```

### Configuration in main.py

Key settings to configure before running:

```python
s.camera_num = 0  # 0 = webcam, 2 = second USB
language = 'Hebrew'  # or 'English'
gender = 'Male'  # or 'Female'
s.rep = 8  # repetitions per exercise
s.adaptive = True  # enable adaptive training
s.calibration = False  # False to require calibration
```

### Testing Individual Components

Each module has `if __name__ == "__main__"` for standalone testing:

- **Camera angle checking**: `Camera.check_angle_range("Shoulder", "Elbow", "Wrist")`
- **Robot exercise demo**: `Poppy.exercise_demo("exercise_name")`
- **Audio testing**: `say("exercise_name")`

### Adding New Exercises

1. **Add exercise method to Poppy.py**:
   - Define robot movements using `goto_position(angle, duration, wait=True/False)`
   - Include counter announcement: `if s.robot_count: say(str(counter + 1))`
   - Return to init position at end

2. **Add corresponding method to Camera.py**:
   - Use `exercise_one_angle_3d()` or `exercise_two_angles_3d()`
   - Define joint triplets and angle thresholds (up_lb, up_ub, down_lb, down_ub)
   - Specify which angle to use for classification ("first" or "second")

3. **Add audio files**:
   - `audio files/{language}/{gender}/{exercise_name}.wav`
   - For one-hand variants: `{exercise_name}_right.wav` and `{exercise_name}_left.wav`
   - For corrective feedback: `{exercise_name}_True.wav` and `{exercise_name}_False.wav`

4. **Update exercise list in Training.py**:
   - Add to `exercise_names` list in appropriate training method

## Dependencies & Environment

### Virtual Environment Setup

**The project uses a Python virtual environment** to isolate dependencies.

**Activate the virtual environment:**
```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**Install all dependencies:**
```bash
pip install -r requirements.txt
```

**Or install manually:**
```bash
pip install poppy-torso mediapipe pygame xlsxwriter scikit-learn pandas
```

### Required Libraries

- **Robot**: `pypot` 5.0.2, `poppy-torso` 3.0.0
- **Vision**: `mediapipe` 0.10.35, `opencv-contrib-python` 4.13.0
- **ML**: `scikit-learn` 1.6.1, `pandas` 2.3.3, `numpy` 2.0.2, `scipy` 1.13.1
- **Audio**: `pygame` 2.6.1 (mixer)
- **UI**: `tkinter` (built-in), `Pillow` 11.3.0
- **Data**: `xlsxwriter` 3.2.9

### Hardware Requirements

- **Poppy Torso robot** (or CoppeliaSim/V-REP simulator)
- **Webcam** for pose detection
- **Audio output** for voice feedback

### Setting Up the Simulator

**1. Install CoppeliaSim (V-REP):**
- **Windows**: Download V-REP 3.3.0 from http://www.coppeliarobotics.com/
- **macOS/Linux**: Download latest CoppeliaSim version

**2. Enable simulator in code:**

In `code/Poppy.py` line 12-13, uncomment the simulator line:
```python
# self.poppy = PoppyTorso()  # for real robot
self.poppy = PoppyTorso(simulator='vrep')  # for simulator
```

**3. Run the project:**
```bash
# First: Launch CoppeliaSim application
# Then: Run Python code (with venv activated)
python code/main.py
```

## Performance Classification System

Located in `performance_classification.py`:

### Feature Extraction

For each hand's angle data:
- **Repetition Features**: start/peak/end values, frames up/down
- **Velocity Features**: mean/SD of velocity and acceleration (up and down phases)
- **FFT Features**: frequency analysis, dominant frequencies, cycle length

### Model Usage

```python
features = feature_extraction(right_hand_data, left_hand_data)
predictions = predict_performance(features, exercise_name, model_name)
# predictions[0] = left hand score, predictions[1] = right hand score
```

Lower scores indicate better performance quality.

## File Structure

```
gymmy_thesis/
├── code/
│   ├── main.py              # Entry point
│   ├── Training.py          # Training orchestrator
│   ├── Poppy.py            # Robot control
│   ├── Camera.py           # Pose tracking
│   ├── MP.py               # MediaPipe processing
│   ├── Audio.py            # Sound system
│   ├── Screen.py           # GUI
│   ├── Settings.py         # Global variables
│   ├── Excel.py            # Data export
│   ├── Joint.py            # Joint data structure
│   ├── performance_classification.py  # ML features
│   ├── model2.sav          # ML model
│   ├── performance_evaluation_model.sav  # Alternative model
│   └── standardize_values_dict  # Feature normalization
├── audio files/
│   ├── Hebrew/
│   │   ├── Male/
│   │   └── Female/
│   └── English/
├── pictures/
│   ├── eyes.png
│   └── icon.jpg
├── dats/                   # Data storage
└── venv/                   # Virtual environment
```

## Known Issues & Future Work

From code TODOs and analysis:

- [ ] Add more exercises
- [ ] Improve adaptive framework
- [ ] GUI enhancements
- [ ] Optimize delay between exercises
- [ ] Refine early termination logic when user completes reps before robot
- [ ] Make exercise selection random instead of sequential
- [ ] Better handling of one-hand training completion

## Data Output

Each session generates:

1. **Excel workbook**: `{participant_code}.xlsx`
   - One sheet per exercise with joint positions and angles
   - "success" sheet: exercise completion counts
   - "performance_class" sheet: ML predictions for each hand

2. **Performance plots**: `{participant_code}{exercise_name}{timestamp}.png`
   - Angle vs frame plots for visual verification

3. **Recorded data**: `recorded_data2.json`
   - Complete MediaPipe skeleton data stream

## API Key Details

| Field | Value |
|-------|-------|
| Key name | Gemini API Key |
| Project ID | project-0c4af6c5-9e91-4c42-a19 |
| Project number | 599699470946 |
| Provider | Google AI Studio (Gemini Flash) |
| Model | gemini-2.0-flash |
| Free tier | 15 RPM, 1M tokens/day, $0 billing |
| Expiry | Never (unless manually revoked) |

**Key location**: `code/.env` (gitignored — never committed)

**How to generate/regenerate**:
1. Go to https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click "Create API Key" (or find existing key under the project above)
4. Copy the key into `code/.env` as: `GEMINI_API_KEY=your-key`

`LLMFeedback.py` loads the key automatically from `code/.env` at import time.

