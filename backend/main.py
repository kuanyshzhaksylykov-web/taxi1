from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger
from datetime import datetime
from config import settings
from database import Database
from websocket_manager import ConnectionManager
from api import router as api_router

# Настройка логирования
logger.add(
    "logs/backend.log",
    rotation="500 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=settings.LOG_LEVEL
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("=== ЗАПУСК BACKEND API ===")
    
    # Инициализация базы данных
    await Database.initialize()
    logger.info("✅ База данных инициализирована")
    
    yield
    
    # Остановка
    logger.info("=== ОСТАНОВКА BACKEND API ===")
    await Database.close()

# Создание приложения
app = FastAPI(
    title="Taxi Service API",
    description="API для такси-сервиса",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(api_router, prefix="/api")

# Менеджер WebSocket соединений
manager = ConnectionManager()

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Taxi Service API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    # Проверка базы данных
    db_ok = await Database.health_check()
    
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/{user_type}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_type: str,
    user_id: int
):
    """WebSocket эндпоинт для реального времени"""
    await manager.connect(websocket, user_id, user_type)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Обработка различных типов сообщений
            if data.get("type") == "location_update":
                # Обновление местоположения водителя
                await handle_location_update(user_id, data)
                
            elif data.get("type") == "order_update":
                # Обновление статуса заказа
                await handle_order_update(user_id, data)
                
            elif data.get("type") == "message":
                # Текстовое сообщение
                await handle_message(user_id, data)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, user_type)
        logger.info(f"WebSocket disconnected: {user_type} {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(user_id, user_type)

async def handle_location_update(user_id: int, data: dict):
    """Обработка обновления местоположения"""
    lat = data.get("lat")
    lon = data.get("lon")
    
    if lat and lon:
        # Сохраняем в базу данных
        await Database.update_driver_location(
            driver_id=user_id,
            lat=lat,
            lon=lon,
            speed=data.get("speed"),
            heading=data.get("heading")
        )
        
        logger.debug(f"Location updated for driver {user_id}: {lat}, {lon}")

async def handle_order_update(user_id: int, data: dict):
    """Обработка обновления заказа"""
    order_id = data.get("order_id")
    status = data.get("status")
    
    if order_id and status:
        # Обновляем статус заказа
        await Database.update_order_status(order_id, status)
        
        # Уведомляем другую сторону (пассажира/водителя)
        await manager.notify_order_update(order_id, status, user_id)

async def handle_message(user_id: int, data: dict):
    """Обработка сообщений"""
    message = data.get("message")
    recipient_id = data.get("recipient_id")
    
    if message and recipient_id:
        # Отправляем сообщение получателю
        await manager.send_personal_message(
            recipient_id,
            {
                "type": "message",
                "from": user_id,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )