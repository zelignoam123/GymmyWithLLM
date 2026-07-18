#!/bin/bash
# One-time setup: builds an x86_64 Python 3.11 venv and installs all deps.
# Required because pypot's V-REP remote API (remoteApi.dylib) is x86_64 only,
# so the venv must be x86_64 even on Apple Silicon.
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

echo "==> gymmy_thesis setup"

# --- 1. Rosetta (Apple Silicon only) -----------------------------------------
if [[ "$(uname -m)" == "arm64" ]]; then
    if ! /usr/bin/pgrep -q oahd; then
        echo "==> Installing Rosetta 2"
        echo "    NOTE: may prompt for your **Mac login password** (the one you"
        echo "    use to unlock your Mac). Nothing is shown as you type."
        softwareupdate --install-rosetta --agree-to-license
    else
        echo "==> Rosetta already installed"
    fi
fi

# --- 2. x86_64 Homebrew ------------------------------------------------------
X86_BREW="/usr/local/bin/brew"
if [[ ! -x "$X86_BREW" ]]; then
    echo "==> Installing x86_64 Homebrew at /usr/local"
    echo "    NOTE: you will be prompted for your **Mac login password** (the one"
    echo "    you use to unlock your Mac). Nothing is shown as you type."
    arch -x86_64 /bin/bash -c \
        "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "==> x86_64 Homebrew already installed"
fi

# --- 3. x86_64 Python 3.11 + Tk ---------------------------------------------
# Homebrew's python@3.11 bottle does NOT ship Tk — you must add `python-tk@3.11`
# separately (which drops _tkinter.so into the same site-packages).
X86_PY="/usr/local/opt/python@3.11/bin/python3.11"
if [[ ! -x "$X86_PY" ]]; then
    echo "==> Installing x86_64 Python 3.11"
    arch -x86_64 "$X86_BREW" install python@3.11
else
    echo "==> x86_64 Python 3.11 already installed"
fi

if ! arch -x86_64 "$X86_BREW" list --formula python-tk@3.11 >/dev/null 2>&1; then
    echo "==> Installing x86_64 python-tk@3.11 (Tk support for Python 3.11)"
    arch -x86_64 "$X86_BREW" install python-tk@3.11
else
    echo "==> x86_64 python-tk@3.11 already installed"
fi

# Verify Tk works in the brewed Python before we build the venv.
if ! arch -x86_64 "$X86_PY" -c 'import _tkinter' 2>/dev/null; then
    echo "ERROR: python@3.11 still cannot import _tkinter after python-tk@3.11 install." >&2
    echo "       Try: arch -x86_64 $X86_BREW reinstall python-tk@3.11 python@3.11" >&2
    exit 1
fi

# --- 4. Fresh .venv ----------------------------------------------------------
if [[ -d .venv ]]; then
    STAMP="$(date +%Y%m%d-%H%M%S)"
    echo "==> Backing up existing .venv to .venv.bak-$STAMP"
    mv .venv ".venv.bak-$STAMP"
fi

echo "==> Creating x86_64 venv"
arch -x86_64 "$X86_PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

ARCH_IN_VENV="$(python -c 'import platform; print(platform.machine())')"
if [[ "$ARCH_IN_VENV" != "x86_64" ]]; then
    echo "ERROR: venv is $ARCH_IN_VENV, expected x86_64" >&2
    exit 1
fi

if ! python -c 'import tkinter' 2>/dev/null; then
    echo "ERROR: venv Python is missing Tk (_tkinter). tcl-tk install may have failed." >&2
    echo "       Try: arch -x86_64 $X86_BREW reinstall tcl-tk python@3.11" >&2
    exit 1
fi

# --- 5. Dependencies ---------------------------------------------------------
echo "==> Installing pip + build tools"
pip install --upgrade pip
pip install "setuptools<58" "wheel<0.38"

echo "==> Installing requirements.txt"
pip install --no-build-isolation -r requirements.txt

# --- 6. Poppy Torso V-REP scene ---------------------------------------------
# The scene file was dropped from newer poppy-torso releases. Grab it from the
# upstream repo so users don't have to hunt for it.
SCENE="$REPO/poppy_torso.ttt"
SCENE_URL="https://raw.githubusercontent.com/poppy-project/poppy-torso/master/software/poppy_torso/vrep-scene/poppy_torso.ttt"
# Re-download if missing OR suspiciously small (<10 KB → likely a 404 stub from a prior bad URL).
if [[ ! -f "$SCENE" ]] || [[ "$(wc -c <"$SCENE")" -lt 10000 ]]; then
    echo "==> Downloading Poppy Torso V-REP scene"
    curl -fL --retry 3 -o "$SCENE" "$SCENE_URL"
    if [[ "$(wc -c <"$SCENE")" -lt 10000 ]]; then
        echo "ERROR: Downloaded scene is smaller than 10 KB — URL likely broken." >&2
        echo "       Check: $SCENE_URL" >&2
        exit 1
    fi
else
    echo "==> Poppy Torso V-REP scene already present ($(wc -c <"$SCENE") bytes)"
fi

echo
echo "==> Setup complete."
echo "    Next:"
echo "      1. Launch CoppeliaSim 4.1"
echo "      2. File → Open Scene → $SCENE"
echo "      3. Ensure simulation is STOPPED (not playing)"
echo "      4. Run  ./run.sh"
