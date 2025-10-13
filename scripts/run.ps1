# scripts/run.ps1
# PowerShell script to run backend (foreground) and frontend (background) in VS Code terminal
# Both processes use the .venv virtual environment

$ErrorActionPreference = 'Stop'

# Activate virtual environment

# Build .venv activation path correctly
$projectRoot = Join-Path $PSScriptRoot '..'
$venvPath = Join-Path $projectRoot '.venv'
$venvActivate = Join-Path (Join-Path $venvPath 'Scripts') 'Activate.ps1'
. $venvActivate


# Start frontend (Streamlit) in background
Write-Host "Starting frontend (Streamlit) on port 8501..."
$frontendDir = Join-Path (Join-Path $PSScriptRoot '..') 'frontend'
Start-Process powershell -ArgumentList "-NoExit", "-Command", ". $venvActivate; cd '$frontendDir'; streamlit run app.py --server.port 8501" -WindowStyle Hidden

# Start backend (FastAPI) in foreground
Write-Host "Starting backend (FastAPI) on port 8000..."
$backendDir = Join-Path (Join-Path $PSScriptRoot '..') 'backend'
cd $backendDir
uvicorn main:app --host 0.0.0.0 --port 8000

# When backend stops, kill frontend
Write-Host "Stopping frontend..."
Get-Process -Name streamlit -ErrorAction SilentlyContinue | Stop-Process
