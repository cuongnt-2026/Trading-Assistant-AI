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
if "%GRP%"=="1" echo (Nhom 1 = dung y Supertrend dang chay that tren cloud: chi XAUUSD)

echo.
echo Server MT5 cua ban lech UTC bao nhieu gio? (vd broker UTC+3 -^> nhap 3)
echo Enter = 0 (coi server = UTC luon, cot Gio/Phien co the lech thuc te vai gio)
set "OFFSET=0"
set /p OFFSET=Lech gio server so voi UTC, Enter=0:
set "MT5_UTC_OFFSET_HOURS=%OFFSET%"

echo.
echo So nen lich su muon lay (cang nhieu cang chac, nhung MT5 co the gioi han
echo do sau lich su - neu loi/thieu du lieu thi thu giam lai).
echo Enter = 8000 (M30 ~ 8000 nen = tam vai thang; muon test dai hon thi tang len).
set "BARS=8000"
set /p BARS=So nen (--bars), Enter=8000:

echo.
echo === Backtest Supertrend (10, %MULT%) - nhom %GRP% - M5/M15/M30/H1 - %BARS% nen ===
"%PY%" backtest_supertrend.py --symbols %SYMS% --tf M5,M15,M30,H1 --bars %BARS%
echo.
echo Nhin AvgR / PF / TotalR: duong = co edge.
echo Phan tich chi tiet gio/phien/thu o cuoi ket qua, va 2 file trong thu muc reports/
echo (backtest_supertrend_detail.json + .csv) - gui 2 file do cho Claude de phan tich sau.
pause
