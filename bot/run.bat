@echo off
chcp 65001 >nul
echo ========================================
echo ЗАПУСК ТАКСИ-БОТА (aiogram 3.x)
echo ========================================

cd /d "%~dp0"

REM Проверяем наличие виртуального окружения
if not exist "..\venv\Scripts\python.exe" (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo Выполните: install.bat
    pause
    exit /b 1
)

REM Активируем виртуальное окружение
call ..\venv\Scripts\activate.bat

REM Проверяем .env файл
if not exist ".env" (
    echo ОШИБКА: Файл .env не найден!
    echo Создайте файл .env с вашим BOT_TOKEN
    echo Пример:
    echo BOT_TOKEN=ваш_токен_бота
    echo ADMIN_IDS=777777777
    pause
    exit /b 1
)

echo.
echo Проверка подключений...
python main.py --test

if errorlevel 1 (
    echo.
    echo ОШИБКА: Проверка не пройдена!
    echo Убедитесь что:
    echo 1. База данных запущена
    echo 2. BOT_TOKEN указан в .env файле
    pause
    exit /b 1
)

echo.
echo Запуск бота...
echo Для остановки нажмите Ctrl+C
echo.

REM Запускаем бота
python main.py

if errorlevel 1 (
    echo.
    echo ОШИБКА: Бот завершился с ошибкой!
    pause
    exit /b 1
)

echo.
echo Бот остановлен.
pause