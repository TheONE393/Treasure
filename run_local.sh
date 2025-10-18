#!/usr/bin/env bash
# Start the Treasure Hunt server locally (Linux/WSL)

echo "Installing dependencies (user)..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r ./requirements.txt

echo "Starting Flask app..."
python3 ./app.py
