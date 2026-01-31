@echo off
chcp 65001 >nul
echo ========================================
echo УПРОЩЕННЫЙ ЗАПУСК БАЗЫ ДАННЫХ
echo ========================================

echo 1. Удаляем старые контейнеры...
docker-compose down

echo 2. Очищаем данные (опционально)...
echo Удалить данные? (y/n)
choice /c yn /n
if errorlevel 2 goto skip_clean
rmdir /s /q data
mkdir data
mkdir data\postgres
mkdir data\redis
mkdir data\pgadmin
:skip_clean

echo 3. Запускаем контейнеры...
docker-compose up -d

echo 4. Ждем запуска PostgreSQL...
timeout /t 20 /nobreak >nul

echo 5. Проверяем статус...
docker-compose ps

echo.
echo ========================================
if errorlevel 1 (
    echo ОШИБКА: Сервисы не запущены!
    echo Проверьте логи: docker-compose logs postgres
) else (
    echo ✅ Сервисы запущены успешно!
    echo.
    echo PostgreSQL: localhost:5432
    echo Redis:      localhost:6379
    echo pgAdmin:    http://localhost:5050
    echo.
    echo Email: admin@taxi.local
    echo Пароль: PgAdminPass123!
)

pause