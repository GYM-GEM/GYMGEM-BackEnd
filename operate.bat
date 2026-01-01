@echo off
REM GymGem Services Startup Script for Windows (CMD)
REM Run as: operate.bat

echo.
echo ========================================
echo   GymGem Services Startup
echo ========================================
echo.

REM Get script directory
cd /d "%~dp0"

REM Activate virtualenv
echo [1/5] Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    echo Please create it with: python -m venv venv
    pause
    exit /b 1
)

REM Environment variables
set DJANGO_SETTINGS_MODULE=GymGem.settings
set PYTHONUNBUFFERED=1

REM Check Redis
echo [2/5] Checking Redis...
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo        Redis is already running.
) else (
    echo        Redis not running.
    echo        Please start Redis manually or use Docker:
    echo        docker run -d -p 6379:6379 redis:alpine
    echo.
    
    REM Try to start Redis if available
    where redis-server >NUL 2>&1
    if "%ERRORLEVEL%"=="0" (
        echo        Found Redis, starting...
        start /B "" redis-server
        timeout /t 2 >NUL
    )
)

timeout /t 1 >NUL

REM Start Daphne
echo [3/5] Starting Daphne (ASGI Server)...
start /B "Daphne" cmd /c "python -m daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application"
timeout /t 2 >NUL

REM Start Celery Worker
echo [4/5] Starting Celery Worker...
start /B "CeleryWorker" cmd /c "python -m celery -A GymGem worker -l info --pool=solo"
timeout /t 2 >NUL

REM Start Celery Beat
echo [5/5] Starting Celery Beat...
start /B "CeleryBeat" cmd /c "python -m celery -A GymGem beat -l info"

echo.
echo ========================================
echo   All services started!
echo ========================================
echo.
echo   Daphne:       http://localhost:8000
echo   Health Check: http://localhost:8000/api/health/
echo.
echo   To stop services, close this window or run stop.bat
echo.

REM Keep window open
echo Press any key to stop all services and exit...
pause >NUL

REM Cleanup
echo.
echo Stopping services...
taskkill /FI "WINDOWTITLE eq Daphne*" /F >NUL 2>&1
taskkill /FI "WINDOWTITLE eq CeleryWorker*" /F >NUL 2>&1
taskkill /FI "WINDOWTITLE eq CeleryBeat*" /F >NUL 2>&1

echo Done.

