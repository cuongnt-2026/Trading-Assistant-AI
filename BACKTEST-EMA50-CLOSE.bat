@echo off
chcp 65001 >nul
title Backtest EMA50 Close (chi 1 duong EMA50) - XAUUSD M15/M30/H1
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo ============================================================
echo   EMA50 CLOSE - CHI 1 duong EMA50 (y tuong CuongNT, cap nhat lan 2):
echo     Nen tu DUOI EMA50 CAT LEN TREN (dut khoat, than nen tren) =^> BUY
echo     Nen tu TREN EMA50 CAT XUONG DUOI (dut khoat, than nen duoi) =^> SELL
echo   (CHI tinh luc VUA CAT QUA - nen tiep theo van o cung phia se KHONG
echo    con tinh la tin hieu moi, tranh lap tin hieu luc dang trending on dinh)
echo   Test rieng tren tung khung M15, M30, H1 de xem khung nao
echo   "chay dung xu huong thi truong" tot nhat.
echo   Da THU bo loc ADX (thu nghiem truoc khong hieu qua ro ret, CuongNT
echo   yeu cau bo) - doi sang huong "chi tinh luc cat" nhu tren thay the.
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
echo So sanh AvgR/PF giua 3 khung. So Trades gio se IT hon han cac lan
echo truoc (chi tinh luc vua cat, khong con tinh moi nen luc dang trending
echo on dinh) - xem PF co vuot 1.2-1.3 chua.
echo Neu muon tat bo loc dem ATR/doi hoi than nen (chi con giu dung dieu
echo kien "vua cat qua"), dat trong .env: EMA50CLOSE_BUFFER_ATR=0,
echo EMA50CLOSE_REQUIRE_FULL_BODY=0 roi chay lai.
pause
