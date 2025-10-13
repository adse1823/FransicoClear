# scripts/run.ps1
# Run Streamlit (background) + FastAPI (foreground) with one root venv.
# Opens http://localhost:8501 automatically when the UI is ready.

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Paths & config ---
$ProjectRoot  = Join-Path $PSScriptRoot '..'
$VenvActivate = Join-Path $ProjectRoot '.venv\Scripts\Activate.ps1'
$FrontendDir  = Join-Path $ProjectRoot 'frontend'
$BackendDir   = Join-Path $ProjectRoot 'backend'

# Ports (override with environment variables if you like)
$UiPort   = if ($env:UI_PORT) { [int]$env:UI_PORT } else { 8501 }
$ApiPort  = if ($env:API_PORT) { [int]$env:API_PORT } else { 8000 }
$UiUrl    = "http://localhost:$UiPort/"

# Optional data dir for backend
if (-not $env:DATA_DIR) { $env:DATA_DIR = Join-Path $ProjectRoot 'data' }

# --- Sanity checks ---
if (-not (Test-Path $VenvActivate)) {
  Write-Error "Virtualenv activation script not found at $VenvActivate. Create venv first."
}
if (-not (Test-Path $FrontendDir)) { Write-Error "Missing folder: $FrontendDir" }
if (-not (Test-Path $BackendDir))  { Write-Error "Missing folder: $BackendDir"  }
if (-not (Test-Path (Join-Path $BackendDir 'main.py'))) { Write-Error "Missing backend/main.py" }
if (-not (Test-Path (Join-Path $FrontendDir 'app.py'))) { Write-Error "Missing frontend/app.py" }

# --- Activate venv ---
. $VenvActivate
Write-Host "(.venv) activated" -ForegroundColor Green

# --- Start frontend (background) ---
Write-Host "Starting frontend (Streamlit) on port $UiPort..." -ForegroundColor Cyan
$FrontendCmd = ". `"$VenvActivate`"; cd `"$FrontendDir`"; streamlit run app.py --server.address 0.0.0.0 --server.port $UiPort"
# Hidden window; keep it open for logs
$FrontendProc = Start-Process powershell -ArgumentList "-NoExit","-Command",$FrontendCmd -WindowStyle Hidden -PassThru

# --- Wait until UI responds, then open browser ---
$maxTries = 40
$opened = $false
for ($i=1; $i -le $maxTries; $i++) {
  try {
    $resp = Invoke-WebRequest -Uri $UiUrl -UseBasicParsing -TimeoutSec 3
    if ($resp.StatusCode -ge 200) {
      Start-Process $UiUrl
      Write-Host "UI is up → $UiUrl (opened in your browser)" -ForegroundColor Green
      $opened = $true
      break
    }
  } catch { }
  Start-Sleep -Milliseconds 500
}
if (-not $opened) {
  Write-Warning "UI did not respond in time; opening $UiUrl anyway."
  Start-Process $UiUrl
}

# --- Start backend (foreground) ---
Write-Host "Starting backend (FastAPI) on port $ApiPort..." -ForegroundColor Cyan
Push-Location $BackendDir
try {
  # Respect env vars if you set them outside; otherwise these defaults apply
  if (-not $env:API_PORT) { $env:API_PORT = "$ApiPort" }
  uvicorn main:app --host 0.0.0.0 --port $env:API_PORT
} finally {
  Pop-Location
}

# --- When backend stops, kill the frontend ---
Write-Host "Backend stopped. Stopping frontend..." -ForegroundColor Yellow
try {
  # Prefer killing only the process we spawned
  if ($FrontendProc -and -not $FrontendProc.HasExited) {
    $FrontendProc.CloseMainWindow() | Out-Null
    Start-Sleep -Seconds 1
    if (-not $FrontendProc.HasExited) { $FrontendProc.Kill() }
  } else {
    # Fallback: stop any stray streamlit processes
    Get-Process -Name streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
  }
} catch {
  Write-Warning "Could not stop frontend cleanly: $($_.Exception.Message)"
}
Write-Host "All done." -ForegroundColor Green
