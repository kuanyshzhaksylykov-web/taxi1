@echo off
chcp 65001 >nul
title УСТАНОВКА ТАКСИ-БОТА - ПРОСТОЙ СПОСОБ
echo ========================================
echo УСТАНОВКА БЕЗ C++ КОМПИЛЯТОРА
echo ========================================

cd /d "%~dp0"

echo 1. Очистка...
if exist "..\venv" rmdir /s /q "..\venv"

echo 2. Создание окружения...
python -m venv ..\venv
call ..\venv\Scripts\activate.bat

echo 3. Установка pip...
python -m pip install --upgrade pip --no-warn-script-location

echo 4. Установка aiohttp БЕЗ компиляции...
echo    Скачиваем готовую версию...
pip install "aiohttp==3.7.4" --only-binary :all:

echo 5. Установка aiogram...
pip install "aiogram==2.25.2"

echo 6. Установка остального...
pip install python-dotenv loguru

echo.
echo ========================================
echo ПРОВЕРКА...
echo ========================================

python -c "
try:
    import aiogram, aiohttp
    print('✅ ВСЕ УСТАНОВЛЕНО!')
    print(f'   Aiogram: {aiogram.__version__}')
    print(f'   Aiohttp: {aiohttp.__version__}')
    print('')
    print('👉 Запустите run.bat после настройки .env файла')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"

echo.
pause