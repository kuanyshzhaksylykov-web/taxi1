@echo off
chcp 65001 >nul
echo ========================================
echo ЗАПУСК DRIVER APP
echo ========================================

REM Простой HTTP сервер для разработки
echo Запуск локального сервера на порту 8080...
echo.
echo Откройте браузер и перейдите по адресу:
echo http://localhost:8080
echo.
echo Для остановки нажмите Ctrl+C
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не установлен!
    echo Скачайте Python с https://python.org
    pause
    exit /b 1
)

REM Запускаем простой HTTP сервер
python -m http.server 8080