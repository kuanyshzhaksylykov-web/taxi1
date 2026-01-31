import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
import math
from loguru import logger

from database import Database
from config import settings
from websocket_manager import manager
import utils

router = APIRouter()

# === MODELS ===

class OrderCreate(BaseModel):
    passenger_id: int
    pickup_address: str
    pickup_lat: float
    pickup_lon: float
    destination_address: str
    destination_lat: float
    destination_lon: float
    tariff_id: int = 1
    
    @validator('pickup_lat', 'destination_lat')
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('pickup_lon', 'destination_lon')
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class DriverLocationUpdate(BaseModel):
    lat: float
    lon: float
    speed: Optional[float] = None
    heading: Optional[int] = None
    accuracy: Optional[float] = None

class OrderStatusUpdate(BaseModel):
    status: str
    driver_id: Optional[int] = None

# === ORDER ENDPOINTS ===

@router.post("/orders", response_model=Dict[str, Any])
async def create_order(order: OrderCreate):
    """Создать новый заказ"""
    
    # Расчет расстояния и времени
    distance = utils.calculate_distance(
        order.pickup_lat, order.pickup_lon,
        order.destination_lat, order.destination_lon
    )
    
    duration = utils.calculate_eta(distance)
    
    # Расчет стоимости
    price = await Database.calculate_price(
        distance_km=distance,
        duration_minutes=duration,
        tariff_id=order.tariff_id
    )
    
    # Получаем информацию о тарифе
    tariffs = await Database.get_tariffs()
    tariff = next((t for t in tariffs if t['id'] == order.tariff_id), None)
    
    if not tariff:
        raise HTTPException(status_code=400, detail="Invalid tariff")
    
    # Создаем заказ
    order_data = {
        'passenger_id': order.passenger_id,
        'pickup_address': order.pickup_address,
        'pickup_lat': order.pickup_lat,
        'pickup_lon': order.pickup_lon,
        'destination_address': order.destination_address,
        'destination_lat': order.destination_lat,
        'destination_lon': order.destination_lon,
        'price': price,
        'tariff_name': tariff['name'],
        'distance_km': distance,
        'duration_minutes': duration
    }
    
    created_order = await Database.create_order(order_data)
    
    if not created_order:
        raise HTTPException(status_code=500, detail="Failed to create order")
    
    # Запускаем поиск водителя в фоне
    asyncio.create_task(find_driver_for_order(created_order['id']))
    
    return {
        "success": True,
        "order_id": created_order['id'],
        "order_uuid": created_order['order_uuid'],
        "price": price,
        "estimated_duration": duration,
        "message": "Order created successfully"
    }

@router.get("/orders/{order_id}")
async def get_order(order_id: int):
    """Получить информацию о заказе"""
    order = await Database.get_order_by_id(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate
):
    """Обновить статус заказа"""
    
    success = await Database.update_order_status(
        order_id=order_id,
        status=status_update.status,
        driver_id=status_update.driver_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or status update failed")
    
    # Уведомляем через WebSocket
    await manager.notify_order_update(order_id, status_update.status, status_update.driver_id or 0)
    
    return {"success": True, "message": "Order status updated"}

@router.get("/orders/{order_id}/nearby-drivers")
async def get_nearby_drivers_for_order(order_id: int):
    """Получить ближайших водителей для заказа"""
    
    order = await Database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Извлекаем координаты из геометрии
    # В реальном проекте нужно парсить WKB геометрию
    lat = order.get('pickup_lat') or 55.7558
    lon = order.get('pickup_lon') or 37.6176
    
    drivers = await Database.find_nearby_drivers(lat, lon)
    
    return {
        "order_id": order_id,
        "pickup_location": {"lat": lat, "lon": lon},
        "drivers": drivers,
        "count": len(drivers)
    }

# === DRIVER ENDPOINTS ===

@router.post("/drivers/{driver_id}/location")
async def update_driver_location(
    driver_id: int,
    location: DriverLocationUpdate
):
    """Обновить местоположение водителя"""
    
    success = await Database.update_driver_location(
        driver_id=driver_id,
        lat=location.lat,
        lon=location.lon,
        speed=location.speed,
        heading=location.heading
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    return {"success": True, "message": "Location updated"}

@router.put("/drivers/{driver_id}/status")
async def update_driver_status(
    driver_id: int,
    status: str = Body(..., embed=True)
):
    """Обновить статус водителя"""
    
    if status not in ['online', 'offline', 'busy', 'break']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    success = await Database.update_driver_status(driver_id, status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    return {"success": True, "message": "Driver status updated"}

@router.get("/drivers/{driver_id}/active-order")
async def get_driver_active_order(driver_id: int):
    """Получить активный заказ водителя"""
    
    order = await Database.get_driver_active_order(driver_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="No active order")
    
    return order

@router.post("/drivers/{driver_id}/accept-order/{order_id}")
async def accept_order(
    driver_id: int,
    order_id: int
):
    """Принять заказ водителем"""
    
    success = await Database.assign_driver_to_order(order_id, driver_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Cannot accept this order")
    
    # Обновляем статус водителя
    await Database.update_driver_status(driver_id, 'busy')
    
    # Уведомляем пассажира
    await manager.notify_order_update(order_id, 'driver_assigned', driver_id)
    
    return {"success": True, "message": "Order accepted"}

# === TARIFF ENDPOINTS ===

@router.get("/tariffs")
async def get_tariffs():
    """Получить список тарифов"""
    tariffs = await Database.get_tariffs()
    return tariffs

@router.get("/calculate-price")
async def calculate_price(
    distance_km: float = Query(..., gt=0),
    duration_minutes: int = Query(..., gt=0),
    tariff_id: int = Query(1, gt=0)
):
    """Рассчитать стоимость поездки"""
    
    price = await Database.calculate_price(
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        tariff_id=tariff_id
    )
    
    return {
        "distance_km": distance_km,
        "duration_minutes": duration_minutes,
        "tariff_id": tariff_id,
        "price": price
    }

# === STATISTICS ===

@router.get("/stats")
async def get_stats():
    """Получить статистику системы"""
    stats = await Database.get_system_stats()
    
    # Добавляем WebSocket статистику
    stats['online_drivers_ws'] = manager.get_online_drivers_count()
    
    return stats

@router.get("/recent-orders")
async def get_recent_orders(limit: int = Query(10, ge=1, le=100)):
    """Получить последние заказы"""
    orders = await Database.get_recent_orders(limit)
    return orders

# === UTILITY FUNCTIONS ===

async def find_driver_for_order(order_id: int):
    """Алгоритм поиска водителя для заказа"""
    
    order = await Database.get_order_by_id(order_id)
    if not order:
        return
    
    # Обновляем статус заказа на поиск водителя
    await Database.update_order_status(order_id, 'searching_driver')
    
    lat = order.get('pickup_lat') or 55.7558
    lon = order.get('pickup_lon') or 37.6176
    
    start_time = datetime.now()
    search_radius = settings.DRIVER_SEARCH_RADIUS_KM
    
    while (datetime.now() - start_time).seconds < settings.MAX_ORDER_SEARCH_TIME_SEC:
        # Ищем ближайших водителей
        drivers = await Database.find_nearby_drivers(lat, lon, search_radius)
        
        if drivers:
            # Отправляем заказ каждому водителю
            for driver in drivers:
                driver_id = driver['id']
                
                # Отправляем через WebSocket
                await manager.send_order_to_driver(
                    order_id=order_id,
                    driver_id=driver_id,
                    order_data=order
                )
                
                # Ждем ответа
                # В реальном проекте нужно реализовать механизм ожидания
                await asyncio.sleep(settings.DRIVER_RESPONSE_TIMEOUT_SEC)
                
                # Проверяем, не принял ли уже кто-то заказ
                current_order = await Database.get_order_by_id(order_id)
                if current_order and current_order['status'] != 'searching_driver':
                    return  # Заказ уже принят
        
        # Увеличиваем радиус поиска
        search_radius = min(search_radius * 1.5, 50)  # Максимум 50 км
        
        # Ждем перед следующим кругом поиска
        await asyncio.sleep(10)
    
    # Если не нашли водителя
    await Database.update_order_status(order_id, 'cancelled')
    await manager.notify_order_update(order_id, 'cancelled', 0)
    
    logger.warning(f"Order {order_id} cancelled - no drivers found")