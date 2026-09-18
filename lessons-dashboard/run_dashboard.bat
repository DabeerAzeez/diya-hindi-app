@echo off
title Hindi Lessons Dashboard Launcher
cd /d "%~dp0"
echo ===================================================
echo   Starting Hindi Lessons Dashboard Server...
echo ===================================================
echo.
echo Launching local server and opening browser...
echo (This window will automatically close when you close the dashboard tab/window in your browser.)
echo.
python run_dashboard.py
