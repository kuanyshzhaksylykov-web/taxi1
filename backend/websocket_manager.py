from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
from loguru import logger
import asyncio

class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        # Словарь для хранения активных соединений
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {
            'drivers': {},
            'passengers': {},
            'admins': {}
        }
        
        # Словарь для подписок на обновления заказов
        self.order_subscriptions: Dict[int, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, user_type: str):
        """Подключение пользователя"""
        await websocket.accept()
        
        user_key = f"{user_type}:{user_id}"
        self.active_connections[user_type][user_key] = websocket
        
        logger.info(f"WebSocket connected: {user_type} {user_id}")
        
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "user_type": user_type,
            "message": "WebSocket connection established"
        })
    
    def disconnect(self, user_id: int, user_type: str):
        """Отключение пользователя"""
        user_key = f"{user_type}:{user_id}"
        if user_key in self.active_connections[user_type]:
            del self.active_connections[user_type][user_key]
            logger.info(f"WebSocket disconnected: {user_type} {user_id}")
    
    async def send_personal_message(self, user_type: str, user_id: int, message: dict):
        """Отправка личного сообщения пользователю"""
        user_key = f"{user_type}:{user_id}"
        if user_key in self.active_connections[user_type]:
            websocket = self.active_connections[user_type][user_key]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_key}: {e}")
                self.disconnect(user_id, user_type)
    
    async def broadcast_to_drivers(self, message: dict, exclude: Optional[List[int]] = None):
        """Трансляция сообщения всем водителям"""
        exclude = exclude or []
        
        for user_key, websocket in self.active_connections['drivers'].items():
            user_id = int(user_key.split(':')[1])
            
            if user_id not in exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to driver {user_id}: {e}")
    
    async def send_order_to_driver(self, order_id: int, driver_id: int, order_data: dict):
        """Отправить заказ конкретному водителю"""
        message = {
            "type": "new_order",
            "order_id": order_id,
            "order": order_data,
            "timeout": 30  # секунд на принятие решения
        }
        
        await self.send_personal_message('drivers', driver_id, message)
    
    async def notify_order_update(self, order_id: int, status: str, user_id: int):
        """Уведомление об обновлении статуса заказа"""
        # Получаем информацию о заказе
        from database import Database
        order = await Database.get_order_by_id(order_id)
        
        if not order:
            return
        
        # Уведомляем пассажира
        if order.get('passenger_id'):
            message = {
                "type": "order_update",
                "order_id": order_id,
                "status": status,
                "order": order
            }
            await self.send_personal_message('passengers', order['passenger_id'], message)
        
        # Уведомляем водителя
        if order.get('driver_id') and order['driver_id'] != user_id:
            message = {
                "type": "order_update",
                "order_id": order_id,
                "status": status,
                "order": order
            }
            await self.send_personal_message('drivers', order['driver_id'], message)
    
    async def subscribe_to_order(self, order_id: int, user_type: str, user_id: int):
        """Подписка на обновления заказа"""
        if order_id not in self.order_subscriptions:
            self.order_subscriptions[order_id] = []
        
        user_key = f"{user_type}:{user_id}"
        if user_key not in self.order_subscriptions[order_id]:
            self.order_subscriptions[order_id].append(user_key)
    
    async def unsubscribe_from_order(self, order_id: int, user_type: str, user_id: int):
        """Отписка от обновлений заказа"""
        if order_id in self.order_subscriptions:
            user_key = f"{user_type}:{user_id}"
            if user_key in self.order_subscriptions[order_id]:
                self.order_subscriptions[order_id].remove(user_key)
    
    def get_online_drivers_count(self) -> int:
        """Получить количество онлайн-водителей"""
        return len(self.active_connections['drivers'])
    
    async def ping_all(self):
        """Пинг всех подключенных клиентов"""
        for user_type in self.active_connections:
            for user_key, websocket in self.active_connections[user_type].items():
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception as e:
                    logger.error(f"Error pinging {user_key}: {e}")
                    # Удаляем отключенное соединение
                    user_id = int(user_key.split(':')[1])
                    self.disconnect(user_id, user_type.split(':')[0])

manager = ConnectionManager()