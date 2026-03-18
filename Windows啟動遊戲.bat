@echo off
chcp 65001 >nul
title 小精靈 Pac-Man 啟動器

cd /d "%~dp0"

echo ==========================================
echo   小精靈 Pac-Man 啟動器
echo ==========================================

python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [X] 找不到 Python
        echo 請先安裝 Python：https://www.python.org/downloads/
        echo 安裝時記得勾選 "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
    set PY=py
) else (
    set PY=python
)

for /f "tokens=*" %%i in ('%PY% --version') do echo [OK] %%i

echo [*] 檢查並安裝依賴套件（首次需要網路，之後不用）...
%PY% -m pip install --quiet --upgrade pygame numpy

echo [OK] 依賴套件就緒
echo.
echo [Game] 啟動遊戲...
echo   方向鍵移動  ^|  ESC 離開  ^|  R 重玩
echo.

%PY% 遊戲主程式.py

echo.
echo 遊戲已結束。
pause
