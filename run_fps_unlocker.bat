@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check for Admin rights and self-elevate
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process -Verb RunAs '%~0'"
    exit /b
)

if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    .\venv\Scripts\python -m pip install pymem
)

:: Launch the script as a background process and exit the batch immediately
start "" /b ".\venv\Scripts\python.exe" "fps_unlocker.py"
exit
