@echo off
chcp 65001 >nul
title Backtest LONDON - CHI TO HOP DA LOC (bo cac cap lo/yeu)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   LONDON BREAKOUT - CHI CHAY CAC TO HOP DA CHUNG MINH CO LOI
echo   (dua tren backtest 5000 nen truoc, khong dong tren .env
echo    nen KHONG anh huong bot dang chay that tren cloud)
echo.
echo   XAUUSD  : BO HOAN TOAN -^> M30 lo, H1 gan hoa von, M15 mau qua nho
echo   EURUSD  : M30, H1       -^> ca 2 deu dep (PF 2.84 va 1.55)
echo   USDJPY  : H1            -^> M15/M30 lo hoac hoa von, chi H1 tot (PF 1.51)
echo   NZDUSD  : M30           -^> M15/H1 lo, chi M30 tot (PF 1.48)
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
set "BARS=5000"
set /p BARS=So nen lich su moi khung, Enter=5000: 

echo.
echo ================= EURUSD (M30, H1) =================
"%PY%" run_backtest.py --strategy london --symbol EURUSD --tf M30,H1 --bars %BARS%

echo.
echo ================= USDJPY (H1) =================
"%PY%" run_backtest.py --strategy london --symbol USDJPY --tf H1 --bars %BARS%

echo.
echo ================= NZDUSD (M30) =================
"%PY%" run_backtest.py --strategy london --symbol NZDUSD --tf M30 --bars %BARS%

echo.
echo ============================================================
echo Da bo XAUUSD hoan toan. Neu muon kiem tra lai voi nhieu nen hon
echo (vi mot vai to hop tren mau con nho, vd EURUSD M30 chi 18 lenh):
echo   %PY% run_backtest.py --strategy london --symbol EURUSD --tf M30,H1 --bars 15000
echo.
echo LUU Y: file nay chay 3 lan run_backtest.py rieng le nen reports/backtest.json
echo chi con luu KET QUA LAN CHAY CUOI (NZDUSD). Doc ket qua tren man hinh la du.
pause
