@echo off
chcp 65001 >nul
setlocal
pushd "%~dp0"
set "PYTHONUTF8=1"
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo Chua co moi truong Python. Hay chay bootstrap.ps1 theo README.
    popd
    pause
    exit /b 1
)
if /I "%~1"=="--check" goto check
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0desktop.py"
set "result=%errorlevel%"
popd
exit /b %result%
:check
"%~dp0.venv\Scripts\python.exe" -c "from pathlib import Path; import tkinter; from animal_knn.common import ROOT; assert ROOT == Path.cwd(); assert (ROOT / 'desktop.py').is_file(); assert (ROOT / 'models/best.joblib').is_file(); print('Windows launcher OK:', ROOT)"
set "result=%errorlevel%"
popd
exit /b %result%
