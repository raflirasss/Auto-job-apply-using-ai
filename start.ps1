# Start AI Job Hunter locally (Windows PowerShell).
# Usage:  powershell -ExecutionPolicy Bypass -File .\start.ps1
# Stops with Ctrl+C in this window (both servers are closed).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".env")) { throw "Missing .env. Copy .env.example to .env and set APP_SECRET_KEY and DASHBOARD_PASSWORD." }
if (-not (Test-Path "backend\.venv\Scripts\python.exe")) {
    Write-Host "Creating Python environment..."
    python -m venv backend\.venv
    backend\.venv\Scripts\python -m pip install --disable-pip-version-check -r backend\requirements.txt
    backend\.venv\Scripts\python -m playwright install chromium
}
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    Push-Location frontend; npm install --no-audit --no-fund; Pop-Location
}

function Get-PortOwner([int]$port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) { Get-CimInstance Win32_Process -Filter "ProcessId=$($conn.OwningProcess)" }
}

# Ports must be free: a leftover server from an earlier run makes the dashboard return 500 errors.
foreach ($port in 8000, 3000) {
    $owner = Get-PortOwner $port
    if ($owner) {
        if ($owner.CommandLine -match [regex]::Escape($root) -or $owner.CommandLine -match "uvicorn app.main:app|next(\\dist\\bin\\next)?.*start") {
            Write-Host "Stopping leftover AI Job Hunter process on port $port (PID $($owner.ProcessId))..."
            taskkill /PID $owner.ProcessId /T /F | Out-Null
            Start-Sleep -Seconds 1
        } else {
            throw "Port $port is used by another program ($($owner.Name), PID $($owner.ProcessId)). Close it and run start.ps1 again."
        }
    }
}

Write-Host "Applying database migrations..."
Push-Location backend; .venv\Scripts\python -m alembic upgrade head; Pop-Location

Write-Host "Building dashboard..."
Push-Location frontend; $env:NEXT_TELEMETRY_DISABLED = "1"; npx next build | Out-Null; Pop-Location

$backend = Start-Process -FilePath "backend\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory "backend" -PassThru -NoNewWindow
$frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npx next start -H 127.0.0.1 -p 3000" -WorkingDirectory "frontend" -PassThru -NoNewWindow

# Wait until the backend really answers; otherwise every dashboard request would fail with 500.
$healthy = $false
for ($i = 0; $i -lt 45; $i++) {
    if ($backend.HasExited) { break }
    try {
        if ((Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/api/health" -TimeoutSec 2).StatusCode -eq 200) { $healthy = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}
if (-not $healthy) {
    foreach ($p in @($backend, $frontend)) { if ($p -and -not $p.HasExited) { taskkill /PID $p.Id /T /F | Out-Null } }
    throw "The backend did not start. Read the error lines above (e.g. an invalid value in .env), fix it, and run start.ps1 again."
}
Start-Sleep -Seconds 2
Write-Host ""
Write-Host "AI Job Hunter is running: http://localhost:3000  (password: DASHBOARD_PASSWORD in .env)"
Write-Host "Press Ctrl+C to stop."
try {
    Start-Process "http://localhost:3000"
    while (-not $backend.HasExited -and -not $frontend.HasExited) { Start-Sleep -Seconds 2 }
    if ($backend.HasExited) { Write-Host "The backend stopped unexpectedly (see errors above). Stopping the dashboard too." -ForegroundColor Red }
} finally {
    foreach ($p in @($backend, $frontend)) { if ($p -and -not $p.HasExited) { taskkill /PID $p.Id /T /F | Out-Null } }
}
