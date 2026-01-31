@echo off
chcp 65001 >nul
echo ========================================
echo ЗАПУСК BACKEND API
echo ========================================

REM Переходим в папку backend
cd /d "%~dp0"

REM Проверяем наличие виртуального окружения в корне проекта
if exist "..\venv\Scripts\activate.bat" (
    echo Активация виртуального окружения...
    call "..\venv\Scripts\activate.bat"
) else (
    echo ВНИМАНИЕ: Виртуальное окружение не найдено в корне проекта!
    echo Создайте его: python -m venv ..\venv
    echo.
    echo Продолжаем без активации (только если Python уже в PATH)...
)

REM Проверяем наличие .env файла
if not exist ".env" (
    echo ВНИМАНИЕ: Файл .env не найден!
    echo Создаю минимальный .env файл...
    
    echo # Настройки базы данных> .env
    echo DEBUG=True>> .env
    echo LOG_LEVEL=INFO>> .env
    echo DB_HOST=localhost>> .env
    echo DB_PORT=5432>> .env
    echo DB_NAME=taxi>> .env
    echo DB_USER=postgres>> .env
    echo DB_PASSWORD=StrongPass123!>> .env
    echo REDIS_HOST=localhost>> .env
    echo REDIS_PORT=6379>> .env
    
    echo Файл .env создан с настройками по умолчанию.
    echo.
)

echo.
echo Запуск сервера...
echo API будет доступно по адресу: http://localhost:8000
echo Документация: http://localhost:8000/docs
echo.

REM Запускаем сервер
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo Сервер остановлен.
pause