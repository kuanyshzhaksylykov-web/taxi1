@echo off
chcp 65001 >nul
echo ========================================
echo УСТАНОВКА BACKEND API
echo ========================================

REM Переходим в папку backend
cd /d "%~dp0"

echo 1. Активация виртуального окружения...
call ..\venv\Scripts\activate.bat

echo.
echo 2. Установка зависимостей...
pip install -r requirements.txt

echo.
echo 3. Создание папок...
if not exist "logs" mkdir logs

echo.
echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo Для запуска выполните: python main.py
echo или запустите run.bat
echo.
pause