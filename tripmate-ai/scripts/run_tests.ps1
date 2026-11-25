# TripMate AI - Test Suite Runner Script (PowerShell)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Set-Location -Path "$rootDir"

Write-Host "Executing TripMate AI Pytest Test Suite..." -ForegroundColor Cyan
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
& "$rootDir\.venv\Scripts\python.exe" -m pytest -c "$rootDir/backend/pytest.ini" -p asyncio "$rootDir/backend/tests" -v
