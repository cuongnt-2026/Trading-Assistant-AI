@echo off
chcp 65001 >nul
title Backtest MO HINH HAI DINH / HAI DAY (M5-H1)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo LUU Y: mo MT5 va dang nhap truoc.
echo.
set "SYM="
set /p SYM=Chi test 1 ma (vd XAUUSD), Enter=tat ca: 
set "ARGS=--strategy double --tf M5,M15,M30,H1"
if not "%SYM%"=="" set "ARGS=%ARGS% --symbol %SYM%"

echo Dang backtest mo hinh hai dinh/hai day tren M5,M15,M30,H1...
"%PY%" run_backtest.py %ARGS%
echo.
pause
