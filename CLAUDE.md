# Gymmy Thesis - Adaptive Physical Exercise Training System

## Project Overview

This is a research project implementing an adaptive physical exercise training system that combines:
- **Poppy Torso robot** - demonstrates physical exercises
- **MediaPipe pose detection** - tracks user movements via camera
- **Machine learning** - classifies exercise performance quality
- **Adaptive feedback** - adjusts training based on real-time performance

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
