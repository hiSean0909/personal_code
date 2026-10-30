@echo off
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo Set up the project virtual environment first. See README.md.
    pause
    exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app.py"
