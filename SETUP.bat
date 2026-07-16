@echo off
chcp 65001 >nul
title Trading Assistant AI - Setup
cd /d "%~dp0"

echo ============================================
echo    CAI DAT THU VIEN (chay 1 lan)
echo ============================================
echo.

REM Tao .venv neu chua co
if not exist ".venv\Scripts\python.exe" (
    echo Dang tao moi truong .venv...
    python -m venv .venv
)

if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Chua cai Python tren may, hoac Python chua vao PATH.
    echo Hay cai Python 3.10+ tu python.org (nho tick "Add to PATH").
    pause
    exit /b
)

echo Dang cai thu vien tu requirements.txt...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo Kiem tra MetaTrader5...
".venv\Scripts\python.exe" -c "import MetaTrader5, pandas, ta; print('[OK] Du thu vien.')"

echo.
echo Xong. Gio co the chay START-BOT.bat
pause
