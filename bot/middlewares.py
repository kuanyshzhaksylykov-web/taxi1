from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from datetime import datetime, timedelta
import asyncio
from loguru import logger

class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения запросов"""
    
    def __init__(self, limit: float = 0.5, key_prefix: str = "antiflood_"):
        self.limit = limit
        self.key_prefix = key_prefix
        super().__init__()
    
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Проверка на флуд
        user_id = message.from_user.id
        
        # Игнорируем админов
        from config import settings
        if user_id in settings.ADMIN_IDS:
            return
        
        # Простая защита от флуда
        # Можно добавить Redis для распределенной системы
        
        # Логируем все сообщения
        logger.debug(f"User {user_id}: {message.text}")

class UserMiddleware(BaseMiddleware):
    """Middleware для работы с пользователями"""
    
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Добавляем информацию о пользователе в data
        from database import Database
        
        user = await Database.get_or_create_user(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name or "",
            username=message.from_user.username or ""
        )
        
        data['user'] = user