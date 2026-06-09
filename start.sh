#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python app.py &
sleep 2
xdg-open http://localhost:5000
wait
