@echo off
chcp 65001 >nul
echo ========================================
echo ЗАПУСК NGINX ДЛЯ ТАКСИ-СЕРВИСА
echo ========================================

REM Проверяем установлен ли Nginx
where nginx >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Nginx не установлен!
    echo Скачайте Nginx с https://nginx.org/en/download.html
    echo и добавьте в PATH
    pause
    exit /b 1
)

REM Создаем папки для логов
if not exist "logs" mkdir logs

echo Останавливаем старый Nginx...
nginx -s stop 2>nul
timeout /t 2 /nobreak >nul

echo Запускаем Nginx...
nginx -c "%~dp0nginx.conf"

echo.
echo Nginx запущен!
echo API доступно по адресу: http://localhost/api
echo Driver App: http://localhost/driver/
echo.
echo Для остановки выполните: nginx -s stop
echo.

REM Проверяем запуск
timeout /t 2 /nobreak >nul
tasklist | findstr nginx >nul
if errorlevel 1 (
    echo ОШИБКА: Nginx не запустился!
    pause
    exit /b 1
)

echo Нажмите любую клавишу для просмотра логов...
pause >nul

REM Показываем логи в реальном времени
echo Логи доступа (Ctrl+C для выхода):
echo ========================================
type "logs\access.log" 2>nul || echo Логи отсутствуют
echo.
echo Нажмите любую клавишу для остановки Nginx...
pause >nul

echo Останавливаем Nginx...
nginx -s stop
echo Готово!
pause