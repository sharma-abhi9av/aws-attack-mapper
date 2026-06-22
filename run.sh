#!/bin/bash

set -e

echo "[+] Removing existing .venv"
rm -rf .venv

echo "[+] Creating fresh .venv"
python3 -m venv .venv

echo "[+] Installing Python dependencies"
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

echo "[+] Running AWS extraction"
./.venv/bin/python main.py --default

echo "[+] Building API"
cd api

go mod tidy
go build -o mooaws-api .

echo "[+] Stopping old API instance"
pkill -f mooaws-api 2>/dev/null || true

echo "[+] Starting API"
nohup ./mooaws-api >/tmp/mooaws.log 2>&1 &

sleep 2

echo "[+] MooAWS running"
echo "[+] Dashboard: http://localhost:8080"

curl -s http://localhost:8080 >/dev/null && echo "[+] API is responding"
