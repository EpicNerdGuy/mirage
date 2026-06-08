#!/bin/bash

MIRAGE_DIR="/home/kali/Desktop/mirage"
HAVOC_DIR="/home/kali/Desktop/havoc"

# ── setup venv if it doesnt exist ───────────────────────────────
if [ ! -d "$MIRAGE_DIR/env" ]; then
    echo "[*] Creating virtual environment..."
    cd "$MIRAGE_DIR"
    python3 -m venv env
    source env/bin/activate
    pip install flask requests websocket-client 2>/dev/null
else
    echo "[*] Activating existing virtual environment..."
    source "$MIRAGE_DIR/env/bin/activate"
fi

# ── teamserver ──────────────────────────────────────────────────
echo "[*] Starting Havoc teamserver..."
cd "$HAVOC_DIR"
./havoc server --profile ./profiles/havoc.yaotl &
sleep 6

# ── flask website ───────────────────────────────────────────────
echo "[*] Starting main.py..."
cd "$MIRAGE_DIR"
python main.py &
sleep 2

# ── handler ─────────────────────────────────────────────────────
echo "[*] Running handler.py..."
python handler.py &
sleep 3

# ── listener ────────────────────────────────────────────────────
echo "[*] Starting listener.py..."
python listener.py &
sleep 2

# ── agent ───────────────────────────────────────────────────────
echo "[*] Starting agent.py..."
python agent.py &

echo ""
echo "[+] Full stack is up."
echo "[+] Open client: cd $HAVOC_DIR && ./havoc client"