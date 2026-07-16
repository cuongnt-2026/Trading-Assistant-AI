@echo off
chcp 65001 >nul
title Day code len GitHub (cloud)
cd /d "%~dp0"

echo Dang day code len GitHub: cuongnt-2026/Trading-Assistant-AI ...
echo (Lan dau co the mo trinh duyet de dang nhap GitHub)
echo.
git add -A
git commit -m "Cloud runner: GitHub Actions + Twelve Data (chay khi tat may)"
git branch -M main
git push -u origin main
echo.
echo Xong. Vao GitHub - tab Actions de xem/chay workflow.
pause
