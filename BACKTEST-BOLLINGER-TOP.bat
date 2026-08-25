@echo off
chcp 65001 >nul
title Backtest BOLLINGER - TOP 3 TO HOP TOT NHAT (~100-120 lenh)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   BOLLINGER - CHI GIU LAI TOP 3 TO HOP CHAT LUONG NHAT
echo   (xep hang theo Profit Factor tu ket qua BACKTEST-BOLLINGER-BEST.bat,
echo    khong dong tren .env nen KHONG anh huong bot dang chay that tren cloud)
echo.
echo   Xep hang 8 to hop da test (PF = Profit Factor):
echo     1. EURUSD H4   PF 2.04  36 lenh  -^> GIU
echo     2. USDJPY H4   PF 1.81  48 lenh  -^> GIU
echo     3. EURUSD M15  PF 1.80  17 lenh  -^> GIU
echo     4. USDJPY M15  PF 1.54  35 lenh  -^> BO (them vao se qua 120 lenh)
echo     5. EURUSD M30  PF 1.38  29 lenh  -^> BO
echo     6. USDJPY M30  PF 1.30  22 lenh  -^> BO
echo     7. XAUUSD M30  PF 1.21  47 lenh  -^> BO
echo     8. XAUUSD H1   PF 1.19  44 lenh  -^> BO
echo.
echo   TONG GIU LAI: 36 + 48 + 17 = 101 lenh (dung trong khoang 100-120 yeu cau)
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
set "BARS=5000"
set /p BARS=So nen lich su moi khung, Enter=5000: 

echo.
echo ================= EURUSD (H4) =================
"%PY%" run_backtest.py --strategy bollinger --symbol EURUSD --tf H4 --bars %BARS%

echo.
echo ================= USDJPY (H4) =================
"%PY%" run_backtest.py --strategy bollinger --symbol USDJPY --tf H4 --bars %BARS%

echo.
echo ================= EURUSD (M15) =================
"%PY%" run_backtest.py --strategy bollinger --symbol EURUSD --tf M15 --bars %BARS%

echo.
echo ============================================================
echo LUU Y: file nay chay 3 lan run_backtest.py rieng le nen reports/backtest.json
echo chi con luu lai KET QUA CUA LAN CHAY CUOI (EURUSD M15). Doc ket qua tren man hinh la du.
pause
