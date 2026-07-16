@echo off
chcp 65001 >nul
title Day code len GitHub (cloud)
cd /d "%~dp0"

echo Dang dong bo (pull) va day (push) code len GitHub...
echo (Lan dau co the mo trinh duyet de dang nhap GitHub)
echo.

:: Luu thay doi cuc bo
git add -A
git commit -m "Cloud update: lich chay + cau hinh"

:: Keo ve truoc (uu tien ban tren GitHub cho file trang thai tu dong)
git config pull.rebase false
git pull --no-edit -X theirs origin main

:: Day len
git push

echo.
echo Neu KHONG con dong mau do "rejected/error" o tren la THANH CONG.
echo Vao GitHub - tab Actions de kiem tra.
pause
