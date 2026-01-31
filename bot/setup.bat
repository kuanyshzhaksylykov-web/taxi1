@echo off
chcp 65001 >nul
echo ========================================
echo УСТАНОВКА ТАКСИ-БОТА
echo ========================================

REM Переходим в папку бота
cd /d "%~dp0"

echo 1. Создание виртуального окружения...
if exist "..\venv" (
    echo Виртуальное окружение уже существует. Удаляем...
    rmdir /s /q "..\venv"
)
python -m venv ..\venv

echo.
echo 2. Активация виртуального окружения...
call ..\venv\Scripts\activate.bat

echo.
echo 3. Обновление pip...
python -m pip install --upgrade pip

echo.
echo 4. Установка зависимостей...
pip install --no-cache-dir -r requirements.txt

if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось установить зависимости!
    echo Попробуйте установить вручную:
    echo   pip install aiogram==3.24.0
    pause
    exit /b 1
)

echo.
echo 5. Копирование файла конфигурации...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo Файл .env создан.
        echo ОТРЕДАКТИРУЙТЕ ФАЙЛ .env и укажите ваш BOT_TOKEN!
    ) else (
        echo ВНИМАНИЕ: Файл .env.example не найден!
        echo Создайте .env файл вручную.
    )
) else (
    echo Файл .env уже существует.
)

echo.
echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo ✅ Виртуальное окружение создано
echo ✅ Зависимости установлены
echo.
echo Дальнейшие шаги:
echo 1. Отредактируйте файл .env (укажите BOT_TOKEN)
echo 2. Настройте базу данных (если нужно)
echo 3. Запустите run.bat
echo.
pause