@echo off
chcp 65001 >nul
title Trading Assistant AI - Backtest
cd /d "%~dp0"

set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
"%PY%" -c "import MetaTrader5, pandas, ta" 1>nul 2>nul || (
    echo [i] Cai thu vien...
    "%PY%" -m pip install -r requirements.txt
)

echo LUU Y: Hay mo MT5 va dang nhap truoc.
echo.
set "MC="
set "SYM="
set /p SYM=Chi test 1 ma (vd XAUUSD), Enter=tat ca: 
set /p MC=Nguong MIN_CONFIDENCE (vd 70), Enter=theo .env: 
echo.
echo Dang chay backtest...
echo.
set "ARGS="
if not "%SYM%"=="" set "ARGS=%ARGS% --symbol %SYM%"
if not "%MC%"=="" set "ARGS=%ARGS% --minconf %MC%"
"%PY%" run_backtest.py%ARGS%

echo.
pause
