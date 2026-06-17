#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCES="$SCRIPT_DIR/Resources"
NDI_LIB="$RESOURCES/NDI SDK for Linux/lib/x86_64-linux-gnu"
VENV="$RESOURCES/venv"
VPY="$VENV/bin/python"

cleanup() {
    if type deactivate &>/dev/null 2>&1; then
        deactivate 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

export LD_LIBRARY_PATH="$NDI_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

echo "[*] Configuring firewall for NDI..."
echo "meat" | sudo -S -p '' ufw allow 5353/udp
echo "meat" | sudo -S -p '' ufw allow 5960:5970/tcp
echo "meat" | sudo -S -p '' ufw allow 5960:5970/udp

APT_PKGS="avahi-daemon avahi-utils libnss-mdns python3-tk python3-venv"
needs_install=0

for pkg in $APT_PKGS; do
    if ! dpkg -s "$pkg" &>/dev/null 2>&1; then
        needs_install=1
        break
    fi
done

if [ "$needs_install" -eq 1 ]; then
    echo "[*] Installing missing system packages..."
    echo "meat" | sudo -S -p '' apt update
    echo "meat" | sudo -S -p '' apt install -y $APT_PKGS
else
    echo "[*] System packages already installed."
fi

echo "[*] Moving to Resources folder..."
cd "$RESOURCES"

echo "[*] Checking virtual environment..."

if [ ! -f "$VENV/bin/activate" ] || [ ! -x "$VPY" ]; then
    echo "[!] Venv is missing or broken. Recreating it..."
    rm -rf "$VENV"
    python3 -m venv "$VENV"
fi

echo "[*] Activating virtual environment..."
source "$VENV/bin/activate"

echo "[*] Confirming venv Python..."
echo "VENV python should be:"
echo "$VPY"

echo "Actual venv Python:"
"$VPY" --version

echo "Actual venv pip:"
"$VPY" -m pip --version

echo "[*] Installing Python requirements inside venv..."
"$VPY" -m pip install --upgrade pip
"$VPY" -m pip install -r "$RESOURCES/requirements.txt"

echo "[*] Launching NDI Viewer..."
setsid "$VPY" NDI2.py &

echo "[*] Session ended."