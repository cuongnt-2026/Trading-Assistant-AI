@echo off
chcp 65001 >nul
title Backtest MO HINH GIA (double / flag) tren M5-H1
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo LUU Y: mo MT5 va dang nhap truoc.
echo.
echo Cac mo hinh: double = hai dinh/hai day ; flag = la co/co duoi nheo ;
echo              structure = cau truc HH/HL ; meanrev = danh nguoc trung binh ;
echo              breakout = pha vo ; divergence = phan ky gia/RSI (bat dao chieu SOM) ;
echo              squeeze = Bollinger that co lai roi no bien (theo huong pha vo)
set "PAT=double"
set /p PAT=Mo hinh (double/flag/structure/meanrev/breakout/divergence/squeeze), Enter=double:
set "SYM="
set /p SYM=Chi test 1 ma (vd XAUUSD), Enter=tat ca:
set "BARS=8000"
set /p BARS=So nen lich su (--bars), Enter=8000:
set "ARGS=--strategy %PAT% --tf M5,M15,M30,H1 --bars %BARS%"
if not "%SYM%"=="" set "ARGS=%ARGS% --symbol %SYM%"

echo Dang backtest mo hinh "%PAT%" tren M5,M15,M30,H1 (%BARS% nen)...
"%PY%" run_backtest.py %ARGS%
echo.
pause
