@echo off
chcp 65001 >nul
echo ========================================
echo ЗАПУСК БАЗЫ ДАННЫХ ТАКСИ-СЕРВИСА
echo ========================================

REM Проверяем установлен ли Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Docker не установлен!
    echo Скачайте с https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Создаем папки для данных
if not exist "data" mkdir data
if not exist "data\postgres" mkdir data\postgres
if not exist "data\redis" mkdir data\redis
if not exist "data\pgadmin" mkdir data\pgadmin

echo.
echo 1. Останавливаем старые контейнеры...
docker-compose down

echo.
echo 2. Скачиваем образы...
docker-compose pull

echo.
echo 3. Запускаем базу данных...
docker-compose up -d

echo.
echo 4. Ждем запуска сервисов...
timeout /t 10 /nobreak >nul

echo.
echo 5. Проверяем статус...
docker-compose ps

echo.
echo ========================================
echo СЕРВИСЫ ЗАПУЩЕНЫ:
echo.
echo PostgreSQL:     localhost:5432
echo Redis:          localhost:6379
echo pgAdmin:        localhost:5050
echo.
echo Данные для подключения:
echo - База: taxi
echo - Пользователь: postgres
echo - Пароль: StrongPass123!
echo.
echo pgAdmin:
echo - Email: admin@taxi.local
echo - Пароль: PgAdminPass123!
echo ========================================
echo.

echo Нажмите любую клавишу для открытия pgAdmin...
pause >nul
start http://localhost:5050

echo Нажмите любую клавишу для остановки сервисов...
pause >nul

echo.
echo Останавливаем сервисы...
docker-compose down