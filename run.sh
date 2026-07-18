#!/bin/bash
# Launches the training app. Assumes ./setup.sh has been run once.
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

if [[ ! -f .venv/bin/activate ]]; then
    echo "ERROR: .venv not found. Run ./setup.sh first." >&2
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

ARCH="$(python -c 'import platform; print(platform.machine())')"
if [[ "$ARCH" != "x86_64" ]]; then
    echo "ERROR: venv is $ARCH but pypot's V-REP remote API needs x86_64." >&2
    echo "       Re-run ./setup.sh." >&2
    exit 1
fi

# Sanity-check the V-REP dylib load before launching the GUI.
if ! python -c "from pypot.creatures import PoppyTorso" 2>/dev/null; then
    echo "ERROR: Failed to import pypot / PoppyTorso." >&2
    echo "       This usually means remoteApi.dylib arch mismatch. Re-run ./setup.sh." >&2
    exit 1
fi

# Camera sanity-check: open one frame from camera 0 before launching the full app.
# Must run with SKIP_AUTH=0 so macOS can pop the permission dialog if needed.
echo "==> Checking camera access..."
CAMERA_OK=$(OPENCV_AVFOUNDATION_SKIP_AUTH=0 python -c "
import cv2, sys
cap = cv2.VideoCapture(0)
ok, frame = cap.read()
cap.release()
print('ok' if ok else 'fail')
" 2>/dev/null)
if [[ "$CAMERA_OK" != "ok" ]]; then
    echo "ERROR: Camera not accessible (got: $CAMERA_OK)." >&2
    echo "       Grant camera permission to this terminal app:" >&2
    echo "         System Settings -> Privacy & Security -> Camera" >&2
    echo "       Then fully quit and reopen the terminal and retry." >&2
    echo "       If no permission dialog appeared, reset with:" >&2
    echo "         tccutil reset Camera com.googlecode.iterm2    # iTerm2" >&2
    echo "         tccutil reset Camera com.microsoft.VSCode     # VS Code" >&2
    echo "         tccutil reset Camera com.apple.Terminal       # Terminal.app" >&2
    exit 1
fi
echo "==> Camera OK"

# Warn if CoppeliaSim's V-REP remote API port (19997) is not listening.
# Non-blocking: prints a warning and proceeds. If the simulator really isn't up,
# pypot will error out on connect with a clear traceback.
if ! /usr/sbin/lsof -i TCP:19997 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "WARNING: CoppeliaSim does not appear to be running (port 19997 not listening)."
    echo "         Continuing anyway — pypot will fail fast if the simulator isn't up."
fi

LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run-$(date +%Y%m%d-%H%M%S).log"

echo "==> Launching. Logs streamed to $LOG_FILE"
echo "    (tail -f  '$LOG_FILE'  in another terminal for live follow)"
echo

export PYTHONUNBUFFERED=1
# On macOS, OpenCV's AVFoundation backend can't request camera authorization from a
# background thread — it will silently fail and every frame times out. Skip the runtime
# request; grant Terminal camera access once via System Settings → Privacy & Security → Camera.
export OPENCV_AVFOUNDATION_SKIP_AUTH=1
# Prefix every line with a wallclock timestamp. Prefer `ts` from moreutils; fall back
# to an awk one-liner so timestamps work out of the box without extra installs.
if command -v ts >/dev/null 2>&1; then
    python -u code/main.py 2>&1 | ts '[%H:%M:%S]' | tee "$LOG_FILE"
else
    python -u code/main.py 2>&1 \
        | awk '{ "date +%H:%M:%S" | getline t; close("date +%H:%M:%S"); printf "[%s] %s\n", t, $0; fflush(); }' \
        | tee "$LOG_FILE"
fi
