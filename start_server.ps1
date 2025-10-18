#!/usr/bin/env pwsh
<#
Start the Treasure Hunt server locally on Windows (PowerShell).

Usage: Open PowerShell in the project root and run:
  .\start_server.ps1

This script will install required packages to the user site (no admin needed)
and then run app.py with the system Python.
#>

Write-Host "Installing dependencies (user site)..."
python -m pip install --user --upgrade pip
python -m pip install --user -r .\requirements.txt

Write-Host "Starting Flask app..."
python .\app.py
