import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
from loguru import logger
from contextlib import asynccontextmanager

from config import settings

class Database:
    """Класс для работы с базой данных"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def initialize(cls):
        """Инициализация пула соединений"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'search_path': 'public',
                    'application_name': 'taxi-backend'
                }
            )
            logger.info("Database pool initialized")
    
    @classmethod
    async def close(cls):
        """Закрытие пула соединений"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database pool closed")
    
    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Контекстный менеджер для получения соединения"""
        if cls._pool is None:
            await cls.initialize()
        
        async with cls._pool.acquire() as conn:
            yield conn
    
    @classmethod
    async def health_check(cls) -> bool:
        """Проверка здоровья базы данных"""
        try:
            async with cls.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # === ORDER METHODS ===
    
    @classmethod
    async def create_order(cls, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создание нового заказа"""
        async with cls.get_connection() as conn:
            try:
                order = await conn.fetchrow("""
                    INSERT INTO orders (
                        passenger_id, pickup_address, pickup_location,
                        destination_address, destination_location, price,
                        tariff_name, distance_km, duration_minutes
                    ) VALUES ($1, $2, ST_SetSRID(ST_MakePoint($4, $3), 4326),
                              $5, ST_SetSRID(ST_MakePoint($7, $6), 4326),
                              $8, $9, $10, $11)
                    RETURNING *
                """,
                    order_data['passenger_id'],
                    order_data['pickup_address'],
                    order_data['pickup_lat'],
                    order_data['pickup_lon'],
                    order_data['destination_address'],
                    order_data['destination_lat'],
                    order_data['destination_lon'],
                    order_data['price'],
                    order_data['tariff_name'],
                    order_data.get('distance_km', 0),
                    order_data.get('duration_minutes', 0)
                )
                return dict(order) if order else None
            except Exception as e:
                logger.error(f"Error creating order: {e}")
                return None
    
    @classmethod
    async def get_order_by_id(cls, order_id: int) -> Optional[Dict[str, Any]]:
        """Получить заказ по ID"""
        async with cls.get_connection() as conn:
            order = await conn.fetchrow("""
                SELECT o.*, 
                       u.first_name as passenger_name,
                       u.phone as passenger_phone,
                       d.car_model as driver_car,
                       d.car_plate as driver_plate,
                       du.first_name as driver_name
                FROM orders o
                LEFT JOIN users u ON o.passenger_id = u.id
                LEFT JOIN drivers d ON o.driver_id = d.id
                LEFT JOIN users du ON d.user_id = du.id
                WHERE o.id = $1
            """, order_id)
            return dict(order) if order else None
    
    @classmethod
    async def find_nearby_drivers(
        cls,
        lat: float,
        lon: float,
        radius_km: int = 5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Поиск ближайших водителей"""
        async with cls.get_connection() as conn:
            drivers = await conn.fetch("""
                SELECT d.*, u.first_name, u.rating,
                       ST_Distance(
                           ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                           dl.location::geography
                       ) as distance_meters
                FROM drivers d
                JOIN users u ON d.user_id = u.id
                LEFT JOIN LATERAL (
                    SELECT location
                    FROM driver_locations
                    WHERE driver_id = d.id
                    ORDER BY recorded_at DESC
                    LIMIT 1
                ) dl ON true
                WHERE d.status = 'online'
                  AND d.is_verified = true
                  AND dl.location IS NOT NULL
                  AND ST_DWithin(
                        ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                        dl.location::geography,
                        $3 * 1000
                      )
                ORDER BY distance_meters
                LIMIT $4
            """, lat, lon, radius_km, limit)
            
            return [dict(driver) for driver in drivers]
    
    @classmethod
    async def assign_driver_to_order(
        cls,
        order_id: int,
        driver_id: int
    ) -> bool:
        """Назначить водителя на заказ"""
        async with cls.get_connection() as conn:
            try:
                result = await conn.execute("""
                    UPDATE orders 
                    SET driver_id = $1, 
                        status = 'driver_assigned',
                        accepted_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2 AND status = 'searching_driver'
                """, driver_id, order_id)
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Error assigning driver: {e}")
                return False
    
    @classmethod
    async def update_order_status(
        cls,
        order_id: int,
        status: str,
        driver_id: Optional[int] = None
    ) -> bool:
        """Обновить статус заказа"""
        async with cls.get_connection() as conn:
            try:
                query = "UPDATE orders SET status = $1, updated_at = CURRENT_TIMESTAMP"
                params = [status]
                
                if status == 'driver_arrived':
                    query += ", arrived_at = CURRENT_TIMESTAMP"
                elif status == 'in_progress':
                    query += ", started_at = CURRENT_TIMESTAMP"
                elif status == 'completed':
                    query += ", completed_at = CURRENT_TIMESTAMP"
                elif status == 'cancelled':
                    query += ", cancelled_at = CURRENT_TIMESTAMP"
                
                if driver_id:
                    query += ", driver_id = $2"
                    params.append(driver_id)
                
                query += " WHERE id = $" + str(len(params) + 1)
                params.append(order_id)
                
                result = await conn.execute(query, *params)
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Error updating order status: {e}")
                return False
    
    # === DRIVER METHODS ===
    
    @classmethod
    async def update_driver_location(
        cls,
        driver_id: int,
        lat: float,
        lon: float,
        speed: Optional[float] = None,
        heading: Optional[int] = None
    ) -> bool:
        """Обновить местоположение водителя"""
        async with cls.get_connection() as conn:
            try:
                await conn.execute("""
                    INSERT INTO driver_locations 
                    (driver_id, location, speed, heading)
                    VALUES ($1, ST_SetSRID(ST_MakePoint($3, $2), 4326), $4, $5)
                """, driver_id, lat, lon, speed, heading)
                
                # Обновляем текущее местоположение в таблице drivers
                await conn.execute("""
                    UPDATE drivers 
                    SET current_location = ST_SetSRID(ST_MakePoint($2, $1), 4326),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                """, lat, lon, driver_id)
                
                return True
            except Exception as e:
                logger.error(f"Error updating driver location: {e}")
                return False
    
    @classmethod
    async def update_driver_status(
        cls,
        driver_id: int,
        status: str
    ) -> bool:
        """Обновить статус водителя"""
        async with cls.get_connection() as conn:
            try:
                result = await conn.execute("""
                    UPDATE drivers 
                    SET status = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """, status, driver_id)
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Error updating driver status: {e}")
                return False
    
    @classmethod
    async def get_driver_active_order(cls, driver_id: int) -> Optional[Dict[str, Any]]:
        """Получить активный заказ водителя"""
        async with cls.get_connection() as conn:
            order = await conn.fetchrow("""
                SELECT * FROM orders 
                WHERE driver_id = $1 
                AND status IN ('driver_assigned', 'driver_arrived', 'in_progress')
                ORDER BY created_at DESC
                LIMIT 1
            """, driver_id)
            return dict(order) if order else None
    
    # === USER METHODS ===
    
    @classmethod
    async def get_user_by_telegram_id(cls, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID"""
        async with cls.get_connection() as conn:
            user = await conn.fetchrow("""
                SELECT * FROM users WHERE telegram_id = $1
            """, telegram_id)
            return dict(user) if user else None
    
    # === ANALYTICS ===
    
    @classmethod
    async def get_system_stats(cls) -> Dict[str, Any]:
        """Получить статистику системы"""
        async with cls.get_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT id) as total_users,
                    COUNT(DISTINCT CASE WHEN user_type = 'driver' THEN id END) as total_drivers,
                    COUNT(DISTINCT CASE WHEN user_type = 'passenger' THEN id END) as total_passengers,
                    COUNT(DISTINCT CASE WHEN status = 'online' THEN id END) as online_drivers,
                    COUNT(DISTINCT CASE WHEN status = 'completed' THEN id END) as completed_orders,
                    COUNT(DISTINCT CASE WHEN status IN ('created', 'searching_driver') THEN id END) as active_orders,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN price END), 0) as total_revenue
                FROM (
                    SELECT u.id, u.user_type, d.status as driver_status
                    FROM users u
                    LEFT JOIN drivers d ON u.id = d.user_id
                ) users_stats
                CROSS JOIN (
                    SELECT 
                        COUNT(*) as total_orders,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                        COUNT(CASE WHEN status IN ('created', 'searching_driver') THEN 1 END) as active_orders,
                        SUM(CASE WHEN status = 'completed' THEN price END) as total_revenue
                    FROM orders
                ) orders_stats
            """)
            
            return dict(stats) if stats else {}
    
    @classmethod
    async def get_recent_orders(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить последние заказы"""
        async with cls.get_connection() as conn:
            orders = await conn.fetch("""
                SELECT 
                    o.*,
                    u.first_name as passenger_name,
                    du.first_name as driver_name,
                    d.car_model
                FROM orders o
                LEFT JOIN users u ON o.passenger_id = u.id
                LEFT JOIN drivers d ON o.driver_id = d.id
                LEFT JOIN users du ON d.user_id = du.id
                ORDER BY o.created_at DESC
                LIMIT $1
            """, limit)
            
            return [dict(order) for order in orders]