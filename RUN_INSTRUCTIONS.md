# How to Run — Gymmy Thesis

Adaptive exercise trainer: Poppy Torso robot (or CoppeliaSim simulator) + MediaPipe pose tracking + ML performance classification. Entry point is `code/main.py`.

## TL;DR

```bash
cd /Users/noamzelig/gymmy_thesis
./setup.sh          # once, ~10 min: builds x86_64 venv, installs deps
# launch CoppeliaSim
./run.sh            # every time
```

Two shell scripts do the work:
- **`setup.sh`** — installs Rosetta, x86_64 Homebrew, x86_64 Python 3.11, creates `.venv`, installs `requirements.txt`. Idempotent (safe to re-run; existing `.venv` is backed up as `.venv.bak-<timestamp>`).
- **`run.sh`** — activates the venv, verifies arch, checks pypot imports, warns if CoppeliaSim isn't listening on port 19997, then runs `python code/main.py`.

## Why the x86_64 venv is required

`pypot`'s V-REP remote API ships an **x86_64-only** `remoteApi.dylib`. On Apple Silicon Macs, an arm64 Python can't `dlopen` it — you get:

```
OSError: dlopen(... remoteApi.dylib): mach-o file, but is an incompatible architecture
  (have 'x86_64', need 'arm64')
```

Options:
- **Simulator mode** (no physical robot) → venv must be x86_64. `setup.sh` handles this.
- **Real robot mode** → arm64 venv is fine. Edit `code/Poppy.py` lines 12–13 to use `PoppyTorso()` instead of `PoppyTorso(simulator='vrep')`, and skip `setup.sh` (build a normal arm64 venv instead).

## Requirements

- **macOS** on Apple Silicon or Intel
- **Python 3.11** (3.13 fails on `numpy==2.0.2` and on `poppy-creature==2.0.0`'s legacy `use_2to3` setup)
- **CoppeliaSim Edu V4.1.0 (macOS Intel)** for simulator mode — see [Installing CoppeliaSim](#installing-coppeliasim) below. Newer builds (4.5+) do not ship the legacy remote API on port 19997 and will not work with pypot.
- **Webcam**, **audio output**
- Rosetta 2 (Apple Silicon only) — `setup.sh` installs it if missing
- x86_64 Homebrew at `/usr/local` — `setup.sh` installs it if missing (separate from your arm64 `/opt/homebrew`)

## First-time setup

```bash
cd /Users/noamzelig/gymmy_thesis
./setup.sh
```

`setup.sh` runs these steps and skips any that are already done:

1. Install Rosetta 2 (Apple Silicon).
2. Install x86_64 Homebrew at `/usr/local`.
3. `arch -x86_64 brew install python@3.11`.
4. Back up any existing `.venv`, then create a fresh x86_64 venv.
5. `pip install "setuptools<58" "wheel<0.38"` (poppy-creature needs pre-58 setuptools for `use_2to3`).
6. `pip install --no-build-isolation -r requirements.txt`.

If prompted for a `Password:` during Rosetta or Homebrew install, that's your **Mac login password** (the one you use to unlock your Mac). Nothing is shown as you type — that's normal.

If it prints `Setup complete.` you're ready.

## Installing CoppeliaSim

`pypot` uses the **legacy V-REP remote API on port 19997**. CoppeliaSim removed this from stock builds starting with 4.5. Only **V4.1.0** (and older) auto-loads the plugin. If you install 4.5 / 4.7 / 4.9 / 4.10 you will see only ports 23000 (ZMQ) and 23050 (WebSocket) — pypot cannot talk to those.

**Get the right build:**

1. Open https://www.coppeliarobotics.com/previousVersions
2. Under **CoppeliaSim V4.1.0**, download **CoppeliaSim Edu, macOS (Intel)**.
   - There is no Apple Silicon build for 4.1.0. That's fine — this project already runs its Python venv under Rosetta (x86_64), and macOS will run the Intel CoppeliaSim under Rosetta transparently.
3. Unzip, drag `coppeliaSim.app` into `/Applications/` (rename to `coppeliaSim-4.1.app` if you want to keep other versions installed side-by-side).
4. First launch may be blocked by Gatekeeper (*"Apple could not verify … is free of malware"*). Strip the quarantine flag:

    ```bash
    xattr -dr com.apple.quarantine "/Applications/coppeliaSim-4.1.app"
    ```

    (Adjust the path to match the actual folder name.)

5. Launch it. Verify the legacy API is up:

    ```bash
    lsof -iTCP:19997 -sTCP:LISTEN 2>/dev/null
    ```

    You should see a `coppeliaS` row listening on `*:19997`. If port 19997 is missing but 23000/23050 are present, you installed a version newer than 4.1.0 — uninstall it and start over.

## Camera permission (macOS — one-time, per terminal app)

macOS requires explicit camera permission for each app that accesses the webcam. This must be done **once per terminal app before the first run**, or after resetting permissions.

1. Open the terminal app you will use to run `./run.sh` (iTerm2, VS Code integrated terminal, Terminal.app, etc.).
2. Run:
    ```bash
    OPENCV_AVFOUNDATION_SKIP_AUTH=0 /Users/noamzelig/gymmy_thesis/.venv/bin/python -c "
    import cv2
    cap = cv2.VideoCapture(0)
    ok, frame = cap.read()
    print('ok:', ok, 'shape:', frame.shape if ok else None)
    cap.release()
    "
    ```
3. macOS pops *"[app] wants to access the camera"* — click **OK / Allow**.
4. Verify: output should be `ok: True shape: (720, 1280, 3)` (or similar). If `ok: False`, the permission didn't register — see [Camera not authorized](#camera-not-authorized) in Troubleshooting.
5. Confirm in **System Settings → Privacy & Security → Camera** that your terminal app is listed and toggled on.

After granting permission once, `./run.sh` handles the rest — it sets `OPENCV_AVFOUNDATION_SKIP_AUTH=1` so OpenCV doesn't try to re-request from a background thread (which fails on macOS).

**Which app to grant?**

| How you run `./run.sh` | Grant permission to |
|---|---|
| VS Code integrated terminal | Visual Studio Code |
| iTerm2 | iTerm |
| macOS Terminal.app | Terminal |

VS Code is the recommended terminal for this project — it was already in the camera list from first setup.

## Running

1. **Launch CoppeliaSim 4.1.0** (opens the simulator window; V-REP remote API listens on port 19997).
1a. **Load the Poppy Torso scene**: **File → Open Scene** → `poppy_torso.ttt` in the repo root (downloaded automatically by `setup.sh`; if missing, re-run `./setup.sh` or fetch it manually from https://raw.githubusercontent.com/poppy-project/poppy-torso/master/software/poppy_torso/vrep-scene/poppy_torso.ttt). Ensure the simulation is **stopped** — do not press ▶; pypot starts the simulation itself.
2. **Optional: adjust settings** in `code/main.py`:

    | Variable | Default | Meaning |
    |---|---|---|
    | `s.camera_num` | `0` | `0` = built-in webcam, `2` = second USB cam |
    | `language` | `'Hebrew'` | `'Hebrew'` or `'English'` |
    | `gender` | `'Male'` | `'Male'` or `'Female'` (voice pack) |
    | `s.rep` | `8` | Reps per exercise |
    | `s.adaptive` | `True` | Enable adaptive training mode |
    | `s.corrective_feedback` | `False` | Verbal guidance during exercise |
    | `s.calibration` | `False` | `False` = run calibration session; `True` = skip |
    | `s.robot_count` | `True` | Robot counts reps aloud |

3. **Launch the app**:

    ```bash
    ./run.sh
    ```

    All stdout/stderr is mirrored to `logs/run-<timestamp>.log`. To watch live in a second terminal:

    ```bash
    tail -f logs/run-*.log
    ```

    If `ts` is installed (`brew install moreutils`), each line gets a `[HH:MM:SS]` prefix.

`run.sh` will fail fast if:
- `.venv` is missing (→ run `./setup.sh`)
- the venv isn't x86_64
- `from pypot.creatures import PoppyTorso` fails

and will **warn but continue** if CoppeliaSim isn't listening on 19997 (press Enter to proceed, Ctrl-C to abort).

## Boot sequence

1. Excel workbook created for this participant (`s.participant_code` = timestamp).
2. Camera, Training, Robot threads start.
3. Tkinter fullscreen "eyes" GUI opens.
4. Wave at the camera to start; the system speaks each exercise.

## Outputs (written to the working directory)

- `{participant_code}.xlsx` — per-exercise joint data + performance predictions
- `{participant_code}{exercise}{timestamp}.png` — angle-vs-frame plots
- `code/recorded_data2.json` — raw MediaPipe skeleton stream

## Troubleshooting

### `pypot.vrep.io.VrepIOErrors: No value` when Poppy() initializes
CoppeliaSim is running (port 19997 is up), but the Poppy Torso scene is not loaded — pypot is trying to move joints that don't exist. In CoppeliaSim: **File → Open Scene** → `poppy_torso.ttt`. Do not press ▶ afterwards. Then re-run `./run.sh`.

### CoppeliaSim starts but port 19997 is not listening
Your CoppeliaSim is too new. Versions 4.5+ dropped the legacy remote API and only expose ZeroMQ (23000) and WebSocket (23050). pypot cannot use those. Uninstall the current version and install **CoppeliaSim Edu V4.1.0 (macOS Intel)** — see [Installing CoppeliaSim](#installing-coppeliasim).

### `"coppeliaSim" cannot be opened because Apple could not verify it is free of malware`
Gatekeeper blocks older unsigned builds. Strip the quarantine attribute:
```bash
xattr -dr com.apple.quarantine "/Applications/coppeliaSim-4.1.app"
```

### `remoteApi.dylib ... incompatible architecture (have 'x86_64', need 'arm64')`
Your venv is arm64. Re-run `./setup.sh` to rebuild it as x86_64. If you don't need the simulator, switch to real robot mode in `code/Poppy.py:12-13`.

### `numpy` / `mediapipe` build errors
You're probably on Python 3.13. `setup.sh` explicitly uses Python 3.11 — re-run it.

### `FileNotFoundError` on `Pictures/icon.jpg`
The folder is `pictures/` (lowercase). On case-sensitive filesystems, edit `code/main.py` line 72 to `image1 = Image.open('pictures/icon.jpg')`.

### Camera not authorized
`OpenCV: not authorized to capture video (status 0)` — macOS blocked the camera. Fix:
1. Run `/camera` (or the one-liner in [Camera permission](#camera-permission-macos--one-time-per-terminal-app)) from the terminal you use to launch `./run.sh`.
2. Click **Allow** on the dialog.
3. If no dialog appears, the permission was previously denied. Reset it:
    ```bash
    # iTerm2:
    tccutil reset Camera com.googlecode.iterm2
    # VS Code:
    tccutil reset Camera com.microsoft.VSCode
    # Terminal.app:
    tccutil reset Camera com.apple.Terminal
    ```
   Then fully quit (⌘Q) and reopen the terminal, and re-run step 1.

### `cv2.imshow` / `cv2.error: Unknown C++ exception` in MP.py
`cv2.imshow` cannot open a window from a background thread on macOS. This line is disabled in [code/MP.py](code/MP.py) — if you see this error it means you have an older version of the file. Re-run to pick up the fix.

### Camera not found
Change `s.camera_num` in `code/main.py` (`0` for built-in webcam, `2` for a USB cam).

### Audio silent
Check that `audio files/{language}/{gender}/` matches the `language`/`gender` set in `main.py`.

### `Class SDLView is implemented in both ... cv2 ... pygame`
Harmless warning from duplicate SDL2 shipped by `opencv-contrib-python` and `pygame`. Ignore it.
