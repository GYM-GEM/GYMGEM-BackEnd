@echo off
REM GymGem Services Stop Script for Windows (CMD)
REM Run as: stop.bat

echo.
echo Stopping GymGem services...
echo.

REM Kill by window title
taskkill /FI "WINDOWTITLE eq Daphne*" /F >NUL 2>&1
taskkill /FI "WINDOWTITLE eq CeleryWorker*" /F >NUL 2>&1
taskkill /FI "WINDOWTITLE eq CeleryBeat*" /F >NUL 2>&1

REM Also try to kill by process name with specific arguments
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>NUL | find "daphne" >NUL && taskkill /PID %%a /F >NUL 2>&1
    wmic process where "ProcessId=%%a" get CommandLine 2>NUL | find "celery" >NUL && taskkill /PID %%a /F >NUL 2>&1
)

echo Done. All GymGem services stopped.
echo.
echo Note: Redis may still be running.
echo To stop Redis: taskkill /IM redis-server.exe /F
echo.
pause

