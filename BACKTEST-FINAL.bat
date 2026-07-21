@echo off
chcp 65001 >nul
title Backtest CAU HINH CUOI (XAU M15/M30/H1 + FX M30)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   BACKTEST CAU HINH DANG CHAY TREN CLOUD:
echo   - XAUUSD: breakout M15 + M30 + H1
echo   - EURUSD / USDJPY / NZDUSD: trend M30
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
pause
"%PY%" run_backtest.py
echo.
echo Xem cot AvgR va PF (duong + PF^>1.2 = co edge). Winrate bo qua.
pause
