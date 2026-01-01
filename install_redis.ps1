#Requires -Version 5.1

# Redis Installation and Setup Script for Django Channels on Windows
# Usage: .\install_redis.ps1

param(
    [switch]$Force
)

Write-Host "Installing Redis for Django Channels on Windows..." -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Check if Redis is already installed
$redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
if ($redisService -and -not $Force) {
    Write-Host "Redis is already installed and running." -ForegroundColor Yellow
    Write-Host "Use -Force to reinstall." -ForegroundColor Yellow
    exit 0
}

# Define Redis version and download URL
$redisVersion = "3.0.504"  # Latest stable for Windows
$redisUrl = "https://github.com/microsoftarchive/redis/releases/download/win-$redisVersion/Redis-x64-$redisVersion.zip"
$downloadPath = "$env:TEMP\redis.zip"
$installPath = "C:\Redis"

# Download Redis
Write-Host "Downloading Redis $redisVersion..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $redisUrl -OutFile $downloadPath -UseBasicParsing
} catch {
    Write-Host "Failed to download Redis. Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Extract Redis
Write-Host "Extracting Redis..." -ForegroundColor Cyan
if (Test-Path $installPath) {
    Remove-Item $installPath -Recurse -Force
}
Expand-Archive -Path $downloadPath -DestinationPath $installPath

# Clean up download
Remove-Item $downloadPath -Force

# Install Redis as a service
Write-Host "Installing Redis service..." -ForegroundColor Cyan
Set-Location $installPath
& ".\redis-server.exe" --service-install

# Start Redis service
Write-Host "Starting Redis service..." -ForegroundColor Cyan
Start-Service -Name "Redis"

# Enable Redis on boot (services start automatically by default)
Write-Host "Redis is set to start automatically on boot." -ForegroundColor Cyan

# Wait a moment for Redis to start
Start-Sleep -Seconds 2

# Test Redis
Write-Host "Testing Redis connection..." -ForegroundColor Cyan
try {
    $testResult = & ".\redis-cli.exe" ping 2>$null
    if ($testResult -eq "PONG") {
        Write-Host "Redis is running successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "PONG" -ForegroundColor Green
    } else {
        throw "Unexpected response: $testResult"
    }
} catch {
    Write-Host "Redis connection test failed" -ForegroundColor Red
    Write-Host "Check status with: Get-Service -Name 'Redis'" -ForegroundColor Red
    exit 1
}

# Show Redis info
Write-Host ""
Write-Host "Redis Information:" -ForegroundColor Cyan
$info = & ".\redis-cli.exe" info server 2>$null
$version = $info | Select-String "redis_version" | ForEach-Object { $_.Line.Split(":")[1] }
Write-Host "Redis Version: $version"

$memInfo = & ".\redis-cli.exe" info memory 2>$null
$usedMem = $memInfo | Select-String "used_memory_human" | ForEach-Object { $_.Line.Split(":")[1] }
Write-Host "Used Memory: $usedMem"

# Show status
Write-Host ""
Write-Host "Redis Service Status:" -ForegroundColor Cyan
Get-Service -Name "Redis" | Format-Table -AutoSize

Write-Host ""
Write-Host "Redis setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test with Django: python manage.py shell" -ForegroundColor White
Write-Host "  2. Run: from channels.layers import get_channel_layer" -ForegroundColor White
Write-Host "  3. Run: get_channel_layer()" -ForegroundColor White
Write-Host ""
Write-Host "To manage Redis:" -ForegroundColor Cyan
Write-Host "  - Start:   Start-Service -Name 'Redis'" -ForegroundColor White
Write-Host "  - Stop:    Stop-Service -Name 'Redis'" -ForegroundColor White
Write-Host "  - Restart: Restart-Service -Name 'Redis'" -ForegroundColor White
Write-Host "  - Status:  Get-Service -Name 'Redis'" -ForegroundColor White
Write-Host "  - Monitor: & '$installPath\redis-cli.exe' monitor" -ForegroundColor White