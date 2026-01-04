# GymGem Services Startup Script for Windows
# Run as: .\operate.ps1

Write-Host "Starting GymGem services..." -ForegroundColor Cyan

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Activate virtualenv
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$VenvActivate = Join-Path $ScriptDir "venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
} else {
    Write-Host "Virtual environment not found at $VenvActivate" -ForegroundColor Red
    Write-Host "Please create it with: python -m venv venv" -ForegroundColor Red
    exit 1
}

# Environment variables
$env:DJANGO_SETTINGS_MODULE = "GymGem.settings"
$env:PYTHONUNBUFFERED = "1"

# Check if Redis is running
Write-Host "Checking Redis..." -ForegroundColor Yellow
$RedisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue

if (-not $RedisProcess) {
    Write-Host "Redis not running." -ForegroundColor Yellow
    Write-Host "You can start it using Docker:" -ForegroundColor Yellow
    Write-Host "docker run -d -p 6379:6379 redis:alpine" -ForegroundColor Yellow
    Write-Host ""

    $RedisPath = Get-Command redis-server -ErrorAction SilentlyContinue
    if ($RedisPath) {
        Write-Host "Found Redis, starting..." -ForegroundColor Green
        Start-Process -FilePath "redis-server" -WindowStyle Hidden
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Continuing without Redis auto-start..." -ForegroundColor Yellow
    }
} else {
    Write-Host "Redis is already running." -ForegroundColor Green
}

Start-Sleep -Seconds 1

# Start Daphne
Write-Host "Starting Daphne..." -ForegroundColor Yellow
$DaphneProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m", "daphne", "-b", "0.0.0.0", "-p", "8000", "GymGem.asgi:application" `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Seconds 2

# Start Celery Worker
Write-Host "Starting Celery Worker..." -ForegroundColor Yellow
$WorkerProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m", "celery", "-A", "GymGem", "worker", "-l", "info", "--pool=solo" `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Seconds 2

# Start Celery Beat
Write-Host "Starting Celery Beat..." -ForegroundColor Yellow
$BeatProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m", "celery", "-A", "GymGem", "beat", "-l", "info" `
    -PassThru `
    -WindowStyle Hidden

Write-Host ""
Write-Host "All services are running!" -ForegroundColor Green
Write-Host "Daphne PID: $($DaphneProcess.Id)" -ForegroundColor Cyan
Write-Host "Worker PID:  $($WorkerProcess.Id)" -ForegroundColor Cyan
Write-Host "Beat PID:    $($BeatProcess.Id)" -ForegroundColor Cyan

# Save PIDs
$PidFile = Join-Path $ScriptDir ".gymgem_pids"
@"
$($DaphneProcess.Id)
$($WorkerProcess.Id)
$($BeatProcess.Id)
"@ | Out-File -FilePath $PidFile -Encoding UTF8

Write-Host ""
Write-Host "Press Enter to stop all services..." -ForegroundColor Gray
Read-Host | Out-Null

Write-Host "Stopping services..." -ForegroundColor Yellow
Stop-Process -Id $DaphneProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $WorkerProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $BeatProcess.Id -Force -ErrorAction SilentlyContinue

Write-Host "[OK] All services stopped." -ForegroundColor Green
