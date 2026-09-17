@echo off
chcp 65001 >nul
title Backtest EMA50 Close (chi 1 duong EMA50) - XAUUSD M15/M30/H1
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   EMA50 CLOSE - CHI 1 duong EMA50 (y tuong CuongNT):
echo     Dong cua DUT KHOAT tren EMA50 (than nen tren EMA50) =^> BUY
echo     Dong cua DUT KHOAT duoi EMA50 (than nen duoi EMA50) =^> SELL
echo   Test rieng tren tung khung M15, M30, H1 de xem khung nao
echo   "chay dung xu huong thi truong" tot nhat.
echo   Da them bo loc ADX14 ^>= 20 (thi truong dang trending that) sau khi
echo   lan test 20000 nen dau tien cho PF thap deu ca 3 khung (~1.0-1.13).
echo   Dat EMA50CLOSE_ADX_MIN=0 trong .env de tat bo loc nay, quay lai ban dau.
echo    Chi dung --strategy CLI, KHONG dong tren .env
echo    nen KHONG anh huong bot dang chay that tren cloud.
echo ============================================================
echo LUU Y: mo MT5 va dang nhap truoc.
echo.
set "BARS=5000"
set /p BARS=So nen lich su moi khung, Enter=5000:

echo.
echo ================= XAUUSD (M15, M30, H1) =================
"%PY%" run_backtest.py --strategy ema50_close --symbol XAUUSD --tf M15,M30,H1 --bars %BARS%

echo.
echo ============================================================
echo So sanh AvgR/PF giua 3 khung. So Trades gio se IT hon lan truoc (da
echo loc bot tin hieu luc ADX yeu/sideway) - xem PF co vuot 1.2-1.3 chua.
echo Neu muon test dung 100%% luat goc (tat het bo loc: dem ATR, doi hoi
echo than nen, VA ca ADX), dat trong .env: EMA50CLOSE_BUFFER_ATR=0,
echo EMA50CLOSE_REQUIRE_FULL_BODY=0, EMA50CLOSE_ADX_MIN=0 roi chay lai.
pause
