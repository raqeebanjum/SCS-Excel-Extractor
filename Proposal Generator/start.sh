#!/bin/bash

echo "[*] Moving into src directory..."
cd src || { echo "src directory not found"; exit 1; }

echo "[*] Creating virtual environment..."
python3 -m venv venv

echo "[*] Activating virtual environment..."
source venv/bin/activate

echo "[*] Installing requirements..."
pip install -r ../requirements.txt

clear

echo "[*] Starting the application..."
python3 main.py

echo
echo "[✔] Done. To run again later:"
echo "    cd src"
echo "    source venv/bin/activate"
echo "    python3 main.py"