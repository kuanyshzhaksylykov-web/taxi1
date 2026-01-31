@echo off
chcp 65001 >nul
echo Остановка всех сервисов такси-сервиса...

taskkill /fi "WINDOWTITLE eq Taxi Database" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Taxi Backend" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Taxi Bot" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Driver App" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Nginx" /f >nul 2>&1

nginx -s stop 2>nul

echo Все сервисы остановлены!
pause