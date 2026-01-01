# GymGem Services Stop Script for Windows
# Run as: .\stop.ps1

Write-Host "🛑 Stopping GymGem services..." -ForegroundColor Yellow

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $ScriptDir ".gymgem_pids"

if (Test-Path $PidFile) {
    $Pids = Get-Content $PidFile
    foreach ($Pid in $Pids) {
        if ($Pid -match '^\d+$') {
            $Process = Get-Process -Id $Pid -ErrorAction SilentlyContinue
            if ($Process) {
                Write-Host "   Stopping process $Pid ($($Process.ProcessName))..." -ForegroundColor Gray
                Stop-Process -Id $Pid -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Remove-Item $PidFile -Force
    Write-Host "✅ All tracked services stopped." -ForegroundColor Green
} else {
    Write-Host "   No PID file found. Attempting to stop by process name..." -ForegroundColor Yellow
    
    # Stop Daphne/Python processes running our app
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "daphne|celery"
    } | ForEach-Object {
        Write-Host "   Stopping $($_.ProcessName) (PID: $($_.Id))..." -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "✅ Done." -ForegroundColor Green
}

Write-Host ""
Write-Host "Note: Redis may still be running. To stop Redis:" -ForegroundColor Yellow
Write-Host "   Stop-Process -Name redis-server -Force" -ForegroundColor Gray

