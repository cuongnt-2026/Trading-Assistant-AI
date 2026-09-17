@echo off
chcp 65001 >nul
title Backtest EMA Pullback (H1 xu huong + M15 hoi ve EMA20/50/100) - XAUUSD
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   EMA PULLBACK - H1 xac dinh xu huong (thu tu EMA20/50/100/200
echo   + doc EMA20 + khoang cach EMA20-EMA50), M15 cho gia hoi ve
echo   EMA20/50/100 + nen xac nhan dao chieu (engulfing/pin bar) - XAUUSD
echo   (chien luoc MOI, dang BAT tren cloud nhung CHUA chay backtest
echo    lan nao tren du lieu that - dung ket qua nay de quyet dinh
echo    co nen giu EMAPULLBACK_ENABLED=1 khong truoc khi tin lenh that.)
echo    Chi dung --strategy CLI, KHONG dong tren .env
echo    nen KHONG anh huong bot dang chay that tren cloud.
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
set "BARS=5000"
set /p BARS=So nen lich su M15, Enter=5000:

echo.
echo ================= XAUUSD (M15, H1 lay them lam xu huong) =================
"%PY%" run_backtest.py --strategy ema_pullback --symbol XAUUSD --tf M15 --bars %BARS%

echo.
echo ============================================================
echo Doc cot AvgR va PF (Profit Factor). AvgR ^> 0 va PF ^> 1.2-1.3 voi
echo it nhat vai chuc lenh moi dang tin cay (giong quy uoc da dung cho
echo Bollinger/London truoc khi bat len cloud).
echo Neu ket qua kem: mo .github\workflows\signals.yml, dat
echo EMAPULLBACK_ENABLED = "0" de tat canh bao/lenh that tam thoi,
echo roi bao lai de dieu chinh tham so (EMAPULLBACK_* trong .env hoac
echo config.py) truoc khi bat lai.
pause
