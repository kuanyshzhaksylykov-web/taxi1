@echo off
chcp 65001 >nul
echo ========================================
echo ПОЛНЫЙ ЗАПУСК ТАКСИ-СЕРВИСА
echo ========================================
echo.

echo 1. ЗАПУСК БАЗЫ ДАННЫХ...
cd /d "database"
start "Taxi Database" cmd /c "start-db.bat"
cd /d ".."
timeout /t 5 /nobreak >nul

echo 2. ЗАПУСК BACKEND API...
cd /d "backend"
start "Taxi Backend" cmd /c "run.bat"
cd /d ".."
timeout /t 5 /nobreak >nul

echo 3. ЗАПУСК TELEGRAM БОТА...
cd /d "bot"
start "Taxi Bot" cmd /c "run.bat"
cd /d ".."
timeout /t 3 /nobreak >nul

echo 4. ЗАПУСК DRIVER APP...
cd /d "driver-app"
start "Driver App" cmd /c "run.bat"
cd /d ".."
timeout /t 3 /nobreak >nul

echo 5. ЗАПУСК NGINX (опционально)...
cd /d "nginx"
start "Nginx" cmd /c "start-nginx.bat"
cd /d ".."

echo.
echo ========================================
echo ВСЕ СЕРВИСЫ ЗАПУЩЕНЫ!
echo ========================================
echo.
echo СЕРВИСЫ:
echo 1. База данных: localhost:5432
echo 2. pgAdmin: localhost:5050
echo 3. Backend API: localhost:8000
echo 4. Telegram бот: работает в консоли
echo 5. Driver App: http://localhost:8080
echo 6. Nginx: http://localhost
echo.
echo ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ:
echo - БД: taxi / postgres / StrongPass123!
echo - pgAdmin: admin@taxi.local / PgAdminPass123!
echo.
echo Нажмите любую клавишу для остановки всех сервисов...
pause >nul

echo.
echo ОСТАНОВКА ВСЕХ СЕРВИСОВ...
echo.

taskkill /fi "WINDOWTITLE eq Taxi Database" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Taxi Backend" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Taxi Bot" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Driver App" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Nginx" /f >nul 2>&1

echo Останавливаем Nginx...
nginx -s stop 2>nul

echo.
echo Все сервисы остановлены!
pause