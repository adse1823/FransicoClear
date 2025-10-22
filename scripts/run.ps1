# scripts/run.ps1
# Run Streamlit (frontend) + FastAPI (backend) together inside VS Code terminal
# Both processes log directly to this terminal (no new windows).

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Paths ---
$ProjectRoot  = Split-Path -Parent $PSScriptRoot
$VenvPath     = Join-Path $ProjectRoot '.venv\Scripts'
$FrontendDir  = Join-Path $ProjectRoot 'frontend'
$BackendDir   = Join-Path $ProjectRoot 'backend'
$PythonExe    = Join-Path $VenvPath 'python.exe'

# --- Port setup ---
if ($env:UI_PORT) {
    $UiPort = [int]$env:UI_PORT
} else {
    $UiPort = 8501
}

if ($env:API_PORT) {
    $ApiPort = [int]$env:API_PORT
} else {
    $ApiPort = 8000
}

$UiUrl = "http://localhost:$UiPort/"

# --- Environment setup ---
if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtualenv Python not found at $PythonExe. Run 'python -m venv .venv' first."
}

# Activate venv
& "$VenvPath\Activate.ps1"
Write-Host "Activated virtual environment (.venv)" -ForegroundColor Green

# --- Start backend (FastAPI) ---
Write-Host "`nStarting backend (FastAPI) on port $ApiPort..." -ForegroundColor Cyan
$backend = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port $ApiPort" `
    -WorkingDirectory $BackendDir `
    -NoNewWindow -PassThru
Write-Host "Backend PID: $($backend.Id)" -ForegroundColor DarkGray

# --- Start frontend (Streamlit) ---
Write-Host "`nStarting frontend (Streamlit) on port $UiPort..." -ForegroundColor Cyan
$frontend = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m streamlit run app.py --server.address 0.0.0.0 --server.port $UiPort" `
    -WorkingDirectory $FrontendDir `
    -NoNewWindow -PassThru
Write-Host "Frontend PID: $($frontend.Id)" -ForegroundColor DarkGray

# --- Wait and open browser ---
Start-Sleep -Seconds 3
Start-Process $UiUrl
Write-Host "`nBrowser opened at $UiUrl" -ForegroundColor Green

# --- Graceful shutdown handler ---
Write-Host "`nPress Ctrl + C to stop both servers." -ForegroundColor Yellow
try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
    if (-not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force }
    Write-Host "All processes stopped. ✅" -ForegroundColor Green
}
