import asyncpg
from loguru import logger
from typing import Optional, List, Dict, Any
from datetime import datetime
from config import settings

class Database:
    """Класс для работы с базой данных (асинхронный)"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Получение пула соединений"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'search_path': 'public',
                    'application_name': 'taxi-bot'
                }
            )
            logger.info("✅ Пул соединений с БД создан")
        return cls._pool
    
    @classmethod
    async def close_pool(cls):
        """Закрытие пула соединений"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("✅ Пул соединений с БД закрыт")
    
    @classmethod
    async def health_check(cls) -> bool:
        """Проверка здоровья базы данных"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            return False
    
    # === USER METHODS ===
    
    @classmethod
    async def get_or_create_user(
        cls,
        telegram_id: int,
        first_name: str,
        last_name: str = "",
        username: str = ""
    ) -> Dict[str, Any]:
        """Получить или создать пользователя"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                user = await conn.fetchrow("""
                    INSERT INTO users (telegram_id, first_name, last_name, username)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (telegram_id) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        username = EXCLUDED.username,
                        last_seen_at = CURRENT_TIMESTAMP
                    RETURNING *
                """, telegram_id, first_name, last_name, username)
                
                return dict(user) if user else {}
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя: {e}")
            return {}
    
    @classmethod
    async def get_user_by_id(cls, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                user = await conn.fetchrow("""
                    SELECT * FROM users WHERE telegram_id = $1
                """, telegram_id)
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя: {e}")
            return None
    
    @classmethod
    async def update_user_phone(cls, telegram_id: int, phone: str) -> bool:
        """Обновить телефон пользователя"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE users 
                    SET phone = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = $2
                """, phone, telegram_id)
                return "UPDATE 1" in result
        except Exception as e:
            logger.error(f"❌ Ошибка обновления телефона: {e}")
            return False
    
    # === ORDER METHODS ===
    
    @classmethod
    async def create_order(
        cls,
        passenger_id: int,
        pickup_address: str,
        pickup_lat: float,
        pickup_lon: float,
        destination_address: str,
        destination_lat: float,
        destination_lon: float,
        price: float,
        tariff_name: str = "economy"
    ) -> Optional[Dict[str, Any]]:
        """Создать новый заказ"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                order = await conn.fetchrow("""
                    INSERT INTO orders (
                        passenger_id, 
                        pickup_address, 
                        pickup_location,
                        destination_address,
                        destination_location,
                        price,
                        tariff_name,
                        status
                    ) VALUES ($1, $2, ST_SetSRID(ST_MakePoint($4, $3), 4326), 
                              $5, ST_SetSRID(ST_MakePoint($7, $6), 4326), 
                              $8, $9, 'searching_driver')
                    RETURNING *
                """, 
                    passenger_id, pickup_address, pickup_lat, pickup_lon,
                    destination_address, destination_lat, destination_lon,
                    price, tariff_name
                )
                
                return dict(order) if order else None
        except Exception as e:
            logger.error(f"❌ Ошибка создания заказа: {e}")
            return None
    
    @classmethod
    async def get_user_orders(cls, telegram_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить заказы пользователя"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                orders = await conn.fetch("""
                    SELECT o.* 
                    FROM orders o
                    JOIN users u ON o.passenger_id = u.id
                    WHERE u.telegram_id = $1
                    ORDER BY o.created_at DESC
                    LIMIT $2
                """, telegram_id, limit)
                
                return [dict(order) for order in orders]
        except Exception as e:
            logger.error(f"❌ Ошибка получения заказов: {e}")
            return []
    
    @classmethod
    async def get_active_order(cls, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить активный заказ пользователя"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                order = await conn.fetchrow("""
                    SELECT o.* 
                    FROM orders o
                    JOIN users u ON o.passenger_id = u.id
                    WHERE u.telegram_id = $1 
                    AND o.status IN ('searching_driver', 'driver_assigned', 'in_progress')
                    ORDER BY o.created_at DESC
                    LIMIT 1
                """, telegram_id)
                
                return dict(order) if order else None
        except Exception as e:
            logger.error(f"❌ Ошибка получения активного заказа: {e}")
            return None
    
    # === TARIFF METHODS ===
    
    @classmethod
    async def get_tariffs(cls) -> List[Dict[str, Any]]:
        """Получить все тарифы"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                tariffs = await conn.fetch("""
                    SELECT * FROM tariffs 
                    WHERE is_active = TRUE 
                    ORDER BY base_fee
                """)
                return [dict(tariff) for tariff in tariffs]
        except Exception as e:
            logger.error(f"❌ Ошибка получения тарифов: {e}")
            return []
    
    # === STATISTICS ===
    
    @classmethod
    async def get_user_stats(cls, telegram_id: int) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        try:
            pool = await cls.get_pool()
            async with pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(o.id) as total_rides,
                        COALESCE(SUM(o.price), 0) as total_spent,
                        AVG(o.passenger_rating) as avg_rating
                    FROM orders o
                    JOIN users u ON o.passenger_id = u.id
                    WHERE u.telegram_id = $1 
                    AND o.status = 'completed'
                """, telegram_id)
                
                return dict(stats) if stats else {
                    'total_rides': 0,
                    'total_spent': 0,
                    'avg_rating': 0
                }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                'total_rides': 0,
                'total_spent': 0,
                'avg_rating': 0
            }