#!/usr/bin/env bash
# Startet den MANANI FIT Meal Planner sauber im Browser (macOS).
# Repariert bei Bedarf ein kaputtes/fehlendes .venv automatisch.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
APP_PORT=5050
APP_URL="http://127.0.0.1:$APP_PORT"

cd "$PROJECT_DIR"

# Prüfen, wer den Port belegt, bevor wir starten.
PORT_PID="$(lsof -nP -iTCP:"$APP_PORT" -sTCP:LISTEN -t 2>/dev/null | head -1 || true)"
if [ -n "$PORT_PID" ]; then
    if ps -p "$PORT_PID" -o args= 2>/dev/null | grep -q "app.py"; then
        echo "==> Server läuft bereits (PID $PORT_PID) unter $APP_URL – öffne Browser."
        open "$APP_URL"
        exit 0
    else
        PORT_CMD="$(ps -p "$PORT_PID" -o comm= 2>/dev/null || echo unbekannt)"
        echo "Fehler: Port $APP_PORT ist bereits belegt von einem anderen Prozess (PID $PORT_PID, $PORT_CMD)."
        echo "Bitte diesen Prozess beenden oder APP_PORT in start_mac.sh anpassen."
        exit 1
    fi
fi

venv_python_ok() {
    [ -x "$VENV_DIR/bin/python" ] \
        && "$VENV_DIR/bin/python" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1
}

find_system_python() {
    for cand in python3.13 python3.12 python3.11 \
        /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11; do
        if command -v "$cand" >/dev/null 2>&1; then
            command -v "$cand"
            return 0
        fi
    done
    return 1
}

if ! venv_python_ok; then
    echo "==> .venv fehlt oder ist beschädigt (benötigt Python >=3.11) — wird neu erstellt..."
    BASE_PY="$(find_system_python || true)"
    if [ -z "$BASE_PY" ]; then
        echo "Fehler: Keine Python-3.11+-Installation gefunden."
        echo "Bitte installieren mit: brew install python@3.12"
        exit 1
    fi
    rm -rf "$VENV_DIR"
    "$BASE_PY" -m venv "$VENV_DIR"
fi

PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo "==> Prüfe Abhängigkeiten..."
"$PIP" install -q --upgrade pip >/dev/null

if ! "$PY" -c "import flask, flask_sqlalchemy, weasyprint, matplotlib, PIL" >/dev/null 2>&1; then
    echo "==> Installiere Abhängigkeiten (kann beim ersten Start etwas dauern)..."
    if ! "$PIP" install -q -e "$PROJECT_DIR" 2>/tmp/manani_pip_error.log; then
        echo "==> 'pip install -e .' fehlgeschlagen (siehe /tmp/manani_pip_error.log)."
        echo "==> Installiere Kern-Abhängigkeiten stattdessen direkt."
        "$PIP" install -q \
            "flask>=3.0" \
            "flask-sqlalchemy>=3.1" \
            "werkzeug>=3.0" \
            "weasyprint==61.2" \
            "pydyf==0.10.0" \
            "matplotlib>=3.8" \
            "pillow>=10.0"
    fi
fi

echo "==> Starte Server..."
"$PY" app.py &
SERVER_PID=$!

cleanup() {
    echo ""
    echo "==> Beende Server..."
    pkill -P "$SERVER_PID" 2>/dev/null || true
    kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo -n "==> Warte auf Server"
for _ in $(seq 1 40); do
    if curl -s -o /dev/null "$APP_URL"; then
        echo " – läuft!"
        break
    fi
    echo -n "."
    sleep 0.5
done

open "$APP_URL"

echo "==> MANANI FIT läuft unter $APP_URL"
echo "==> Zum Beenden dieses Fenster schließen oder Ctrl+C drücken."

wait "$SERVER_PID"
