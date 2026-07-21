@echo off
chcp 65001 >nul
title Backtest MO HINH GIA (double / flag) tren M5-H1
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo LUU Y: mo MT5 va dang nhap truoc.
echo.
echo Cac mo hinh: double = hai dinh/hai day ; flag = la co/co duoi nheo ; breakout = pha vo
set "PAT=double"
set /p PAT=Mo hinh (double / flag / breakout), Enter=double: 
set "SYM="
set /p SYM=Chi test 1 ma (vd XAUUSD), Enter=tat ca: 
set "ARGS=--strategy %PAT% --tf M5,M15,M30,H1"
if not "%SYM%"=="" set "ARGS=%ARGS% --symbol %SYM%"

echo Dang backtest mo hinh "%PAT%" tren M5,M15,M30,H1...
"%PY%" run_backtest.py %ARGS%
echo.
pause
