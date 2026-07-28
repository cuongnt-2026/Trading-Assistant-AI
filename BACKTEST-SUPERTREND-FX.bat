@echo off
chcp 65001 >nul
title Backtest SUPERTREND (10,3) - cac cap FX major
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
echo ============================================================
echo   SUPERTREND (10,3) tren 7 cap USD major - M5/M15/M30/H1
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
pause
"%PY%" backtest_supertrend.py --symbols EURUSD,GBPUSD,USDJPY,USDCHF,AUDUSD,USDCAD,NZDUSD --tf M5,M15,M30,H1
echo.
echo Nhin AvgR / PF / TotalR: duong = co edge.
pause
