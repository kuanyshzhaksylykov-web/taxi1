@echo off
chcp 65001 >nul
echo Остановка базы данных такси-сервиса...
docker-compose down
echo Готово!
pause