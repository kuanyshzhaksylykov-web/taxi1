@echo off
chcp 65001 >nul
echo ========================================
echo УСТАНОВКА ТАКСИ-БОТА (aiogram 3.x)
echo ========================================

cd /d "%~dp0"

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не установлен!
    echo Скачайте Python 3.12+ с https://python.org
    pause
    exit /b 1
)

REM Создаем виртуальное окружение
if not exist "..\venv" (
    echo Создание виртуального окружения...
    python -m venv ..\venv
)

REM Активируем окружение
call ..\venv\Scripts\activate.bat

REM Обновляем pip
python -m pip install --upgrade pip

REM Устанавливаем зависимости
echo Установка зависимостей...
pip install -r requirements.txt

if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости!
    echo Попробуйте установить вручную:
    echo   pip install aiogram==3.18.0
    pause
    exit /b 1
)

REM Проверяем .env файл
if not exist ".env" (
    echo.
    echo ВНИМАНИЕ: Файл .env не найден!
    echo Создайте файл .env с вашим BOT_TOKEN
    echo Пример содержимого:
    echo BOT_TOKEN=ваш_токен_бота
    echo ADMIN_IDS=777777777
    echo.
)

echo.
echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo Создайте файл .env с вашим BOT_TOKEN
echo Запустите бота: python main.py
echo.
pause