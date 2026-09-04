@echo off
chcp 65001 >nul
title Backtest HEDGE tai khang cu (XAUUSD)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   BACKTEST HEDGE tai khang cu manh - XAUUSD
echo   - Uptrend (day sau cao hon) + khang cu cham >=4 lan
echo   - Mo dong thoi BUY (TP+20/SL-20) va SELL (TP+10/SL-20)
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
set "BARS=8000"
set /p BARS=So nen lich su (--bars), Enter=8000:
pause
"%PY%" backtest_hedge.py --tf M5,M15,M30,H1 --bars %BARS%
echo.
echo Nhin cot Total$ va Avg$/hg: duong = lai, am = lo.
pause
