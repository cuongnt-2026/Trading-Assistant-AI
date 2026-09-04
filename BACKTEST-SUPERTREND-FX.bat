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
set "OFFSET=0"
set /p OFFSET=Server MT5 lech UTC bao nhieu gio? Enter=0:
set "MT5_UTC_OFFSET_HOURS=%OFFSET%"
pause
"%PY%" backtest_supertrend.py --symbols EURUSD,GBPUSD,USDJPY,USDCHF,AUDUSD,USDCAD,NZDUSD --tf M5,M15,M30,H1
echo.
echo Nhin AvgR / PF / TotalR: duong = co edge.
echo Phan tich chi tiet gio/phien/thu + 2 file reports/backtest_supertrend_detail.(json/csv)
echo o cuoi ket qua - gui cho Claude de phan tich sau.
pause
