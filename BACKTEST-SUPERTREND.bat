@echo off
chcp 65001 >nul
title Backtest SUPERTREND - chon he so + nhom
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   BACKTEST SUPERTREND (chu ky co dinh = 10)
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
set "MULT=3"
set /p MULT=Nhap he so (so sau, vd 3 / 4 / 5), Enter=3: 
set "ST_MULT=%MULT%"

echo.
echo   1 = XAU (vang)
echo   2 = FX (7 cap USD major)
echo   3 = Tat ca (XAU + FX)
set "GRP=3"
set /p GRP=Chon nhom (1/2/3), Enter=3: 

set "SYMS=XAUUSD,EURUSD,GBPUSD,USDJPY,USDCHF,AUDUSD,USDCAD,NZDUSD"
if "%GRP%"=="1" set "SYMS=XAUUSD"
if "%GRP%"=="2" set "SYMS=EURUSD,GBPUSD,USDJPY,USDCHF,AUDUSD,USDCAD,NZDUSD"

echo.
echo === Backtest Supertrend (10, %MULT%) - nhom %GRP% - M5/M15/M30/H1 ===
"%PY%" backtest_supertrend.py --symbols %SYMS% --tf M5,M15,M30,H1
echo.
echo Nhin AvgR / PF / TotalR: duong = co edge.
pause
