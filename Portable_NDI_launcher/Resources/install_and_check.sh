#!/usr/bin/env bash
set -euo pipefail

echo "== Butcher-x-NDI: Install & Check =="

PY=python3

command -v "$PY" >/dev/null 2>&1 || {
  echo "ERROR: $PY not found. Please install Python 3 and retry." >&2
  exit 1
}

echo "Checking for NewTek NDI native library..."

found_lib=""
if [[ -n "${NDI_SDK_PATH:-}" ]]; then
  if [[ -f "$NDI_SDK_PATH" ]]; then
    found_lib="$NDI_SDK_PATH"
    echo "  Found via NDI_SDK_PATH=$NDI_SDK_PATH"
  else
    echo "  NDI_SDK_PATH is set but file not found: $NDI_SDK_PATH" >&2
  fi
fi

uname_s=$(uname -s)
if [[ -z "$found_lib" ]]; then
  if [[ "$uname_s" == "Darwin" ]]; then
    candidates=("/Library/NDI SDK for Apple/lib/macOS/libndi.dylib" "/usr/local/lib/libndi.dylib")
  elif [[ "$uname_s" == "Linux" ]]; then
    candidates=("/usr/lib/libndi.so" "/usr/local/lib/libndi.so")
  else
    candidates=()
  fi

  for p in "${candidates[@]}"; do
    if [[ -f "$p" ]]; then
      found_lib="$p"
      echo "  Found native library at: $p"
      break
    fi
  done
fi

if [[ -z "$found_lib" ]]; then
  cat <<EOF >&2
ERROR: Could not find the NewTek NDI native library on this machine.

Please install the NewTek NDI SDK for your platform (https://ndi.video) and either:
- Install it to a standard system location (macOS: /Library/NDI SDK for Apple/lib/macOS/libndi.dylib, Linux: /usr/lib/libndi.so), OR
- Set the environment variable NDI_SDK_PATH to the full path of the native library file.

Example (macOS):
  export NDI_SDK_PATH="/Library/NDI SDK for Apple/lib/macOS/libndi.dylib"

After installing the SDK, re-run this script.
EOF
  exit 2
fi

echo "Installing Python dependencies from requirements.txt..."
$PY -m pip install --user -r requirements.txt || {
  echo "ERROR: pip install failed. Try running: $PY -m pip install -r requirements.txt" >&2
  exit 3
}

echo "Checking for Tkinter (optional GUI)..."
if $PY -c "import tkinter" >/dev/null 2>&1; then
  echo "  Tkinter appears to be available. GUI will work."
else
  echo "  Tkinter not found. Source selector GUI will not be available." >&2
  case "$uname_s" in
    Darwin)
      echo "  macOS: install Tcl/Tk via Homebrew: brew install tcl-tk" >&2
      echo "  or use the python.org macOS installer which bundles Tk." >&2
      ;;
    Linux)
      echo "  Debian/Ubuntu: sudo apt-get install python3-tk" >&2
      echo "  Fedora: sudo dnf install python3-tkinter" >&2
      echo "  Arch: sudo pacman -S tk" >&2
      ;;
    *)
      echo "  Refer to your OS docs to install tkinter." >&2
      ;;
  esac
  echo "  The script will continue, but GUI functionality will be disabled." >&2
fi

echo "Running smoke-test (check_ndilib.py)..."
if $PY check_ndilib.py; then
  echo "Smoke test passed: NDI wrapper and SDK appear functional."
else
  echo "ERROR: Smoke test failed. See the output above for details." >&2
  exit 4
fi

echo "All checks passed. You can now run: python3 NDI2.py" 

exit 0
