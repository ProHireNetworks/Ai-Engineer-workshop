# TripMate AI - Development Server Startup Script (PowerShell)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Set-Location -Path "$rootDir\backend"

Write-Host "Starting TripMate AI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
& "$rootDir\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

