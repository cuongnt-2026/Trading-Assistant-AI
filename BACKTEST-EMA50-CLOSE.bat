@echo off
chcp 65001 >nul
title Backtest EMA50 Close (chi 1 duong EMA50) - XAUUSD M15/M30/H1
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   EMA50 CLOSE - CHI 1 duong EMA50 (y tuong CuongNT):
echo     Dong cua DUT KHOAT tren EMA50 (than nen tren EMA50) => BUY
echo     Dong cua DUT KHOAT duoi EMA50 (than nen duoi EMA50) => SELL
echo   Test rieng tren tung khung M15, M30, H1 de xem khung nao
echo   "chay dung xu huong thi truong" tot nhat.
echo   (chien luoc MOI, CHUA bao gio chay backtest hay bat len that -
echo    day la lan dau kiem tra y tuong.)
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
echo So sanh AvgR/PF giua 3 khung. Doc them cot Trades - vi day la
echo luat "dong cua vuot EMA50" nen o thi truong sideway se ra RAT
echo NHIEU lenh (dut khoat lien tuc 2 chieu) - neu Trades qua nhieu
echo ma AvgR/PF kem, co the can bao Claude bo sung bo loc (vd ADX xac
echo nhan dang trending) truoc khi thu lai.
echo Neu muon test dung 100%% luat goc (khong dem/khong doi hoi than
echo nen), dat trong .env: EMA50CLOSE_BUFFER_ATR=0 va
echo EMA50CLOSE_REQUIRE_FULL_BODY=0 roi chay lai file nay.
pause
