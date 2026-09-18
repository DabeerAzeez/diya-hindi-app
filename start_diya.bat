@echo off
title DIYA - Hindi Learning Hub Launcher
cd /d "%~dp0"

echo ========================================================
echo   ?? DIYA ? Personal Hindi Language Hub Launcher
echo ========================================================
echo.

:: Check if frontend is built
if not exist "frontend\dist\index.html" (
    echo Building frontend production assets...
    cd frontend
    call npm run build
    cd ..
)

echo Starting local server and launching browser...
echo (The server will automatically terminate when you close the browser tab.)
echo.

python diya\server.py

