# Start AI Job Hunter locally (Windows PowerShell).
# Usage:  powershell -ExecutionPolicy Bypass -File .\start.ps1
# Stops with Ctrl+C in this window (both servers are closed).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Fail([string]$message) {
    Write-Host ""
    Write-Host $message -ForegroundColor Red
    Write-Host ""
    exit 1
}

# 1. Required programs
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Fail "Python belum terpasang. Install dari https://www.python.org/downloads/ (centang 'Add python.exe to PATH'), lalu jalankan lagi."
}
$pyOk = & python -c "import sys; print(int(sys.version_info >= (3, 12)))"
if (-not $pyOk) {
    Fail "Python belum terpasang (perintah 'python' hanya membuka Microsoft Store). Install dari https://www.python.org/downloads/ dan centang 'Add python.exe to PATH'."
}
if ($pyOk -ne "1") { Fail "Python 3.12 atau lebih baru dibutuhkan. Versi sekarang: $(& python --version). Install versi terbaru dari https://www.python.org/downloads/" }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Fail "Node.js belum terpasang. Install versi LTS dari https://nodejs.org/, lalu jalankan lagi."
}

# 2. First run: create .env with a random secret key and dashboard password
if (-not (Test-Path ".env")) {
    $chars = [char[]]"ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    $secret = -join (1..64 | ForEach-Object { $chars | Get-Random })
    $password = -join (1..12 | ForEach-Object { $chars | Get-Random })
    $lines = (Get-Content ".env.example") `
        -replace '^APP_SECRET_KEY=$', "APP_SECRET_KEY=$secret" `
        -replace '^DASHBOARD_PASSWORD=$', "DASHBOARD_PASSWORD=$password"
    [System.IO.File]::WriteAllLines((Join-Path $root ".env"), $lines, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host ""
    Write-Host "==============================================================" -ForegroundColor Green
    Write-Host " File .env dibuat. Password dashboard kamu:  $password" -ForegroundColor Green
    Write-Host " (Simpan password ini. Bisa diganti di file .env, baris DASHBOARD_PASSWORD)" -ForegroundColor Green
    Write-Host "==============================================================" -ForegroundColor Green
    Write-Host ""
}

# 3. First run: install dependencies (takes a few minutes, only once)
if (-not (Test-Path "backend\.venv\Scripts\python.exe")) {
    Write-Host "Instalasi pertama: menyiapkan Python (beberapa menit)..."
    python -m venv backend\.venv
    backend\.venv\Scripts\python -m pip install --disable-pip-version-check -q -r backend\requirements.txt
    if ($LASTEXITCODE -ne 0) { Remove-Item -Recurse -Force backend\.venv; Fail "Instalasi paket Python gagal. Cek koneksi internet lalu jalankan lagi." }
    backend\.venv\Scripts\python -m playwright install chromium
}
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Instalasi pertama: menyiapkan dashboard (beberapa menit)..."
    Push-Location frontend; npm install --no-audit --no-fund; $code = $LASTEXITCODE; Pop-Location
    if ($code -ne 0) { Remove-Item -Recurse -Force frontend\node_modules -ErrorAction SilentlyContinue; Fail "npm install gagal. Cek koneksi internet lalu jalankan lagi." }
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
            Fail "Port $port dipakai program lain ($($owner.Name), PID $($owner.ProcessId)). Tutup program itu lalu jalankan lagi."
        }
    }
}

Write-Host "Menyiapkan database..."
Push-Location backend; .venv\Scripts\python -m alembic upgrade head; $code = $LASTEXITCODE; Pop-Location
if ($code -ne 0) { Fail "Database gagal disiapkan. Baca pesan error di atas (biasanya isi .env tidak valid)." }

Write-Host "Menyiapkan dashboard..."
Push-Location frontend; $env:NEXT_TELEMETRY_DISABLED = "1"; npx next build | Out-Null; $code = $LASTEXITCODE; Pop-Location
if ($code -ne 0) { Fail "Dashboard gagal dibuat. Jalankan 'cd frontend; npx next build' untuk melihat errornya." }

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
    Fail "Backend gagal jalan. Baca pesan error di atas (misalnya isi .env tidak valid), perbaiki, lalu jalankan lagi."
}
Start-Sleep -Seconds 2
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host " AI Job Hunter sudah jalan:  http://localhost:3000" -ForegroundColor Green
Write-Host " Password: lihat DASHBOARD_PASSWORD di file .env" -ForegroundColor Green
Write-Host " JANGAN tutup jendela ini. Untuk berhenti: tekan Ctrl+C." -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
try {
    Start-Process "http://localhost:3000"
    while (-not $backend.HasExited -and -not $frontend.HasExited) { Start-Sleep -Seconds 2 }
    if ($backend.HasExited) { Write-Host "The backend stopped unexpectedly (see errors above). Stopping the dashboard too." -ForegroundColor Red }
} finally {
    foreach ($p in @($backend, $frontend)) { if ($p -and -not $p.HasExited) { taskkill /PID $p.Id /T /F | Out-Null } }
}
