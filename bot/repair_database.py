import asyncpg
import asyncio
import sys
import os
from loguru import logger
from config import settings

async def repair_database():
    """Ремонт структуры базы данных"""
    print("🔧 Начинаем ремонт структуры базы данных...")
    
    try:
        # Подключаемся к базе данных используя URL из настроек
        print(f"Подключение к базе данных...")
        conn = await asyncpg.connect(settings.database_url)
        
        # 1. Исправляем таблицу users
        print("\n1. Проверяем таблицу 'users'...")
        
        # Проверяем существование таблицы
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """)
        
        if not table_exists:
            print("   Таблица 'users' не существует! Создаем...")
            await conn.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(100),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) DEFAULT '',
                    phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("   ✅ Таблица 'users' создана")
        else:
            print("   ✅ Таблица 'users' существует")
            
            # Проверяем и добавляем недостающие колонки
            columns_to_check = [
                ('username', 'VARCHAR(100)'),
                ('last_seen_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                ('telegram_id', 'BIGINT UNIQUE NOT NULL')  # Проверяем, что есть telegram_id
            ]
            
            for column_name, column_type in columns_to_check:
                column_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users' 
                        AND column_name = $1
                    )
                """, column_name)
                
                if not column_exists:
                    print(f"   Добавляем колонку '{column_name}'...")
                    try:
                        if column_name == 'telegram_id':
                            # Если нет telegram_id, добавляем её
                            await conn.execute(f"""
                                ALTER TABLE users 
                                ADD COLUMN {column_name} {column_type}
                            """)
                        else:
                            await conn.execute(f"""
                                ALTER TABLE users 
                                ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                            """)
                        print(f"   ✅ Колонка '{column_name}' добавлена")
                    except Exception as e:
                        print(f"   ⚠️ Ошибка при добавлении {column_name}: {e}")
        
        # 2. Исправляем таблицу orders
        print("\n2. Проверяем таблицу 'orders'...")
        
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'orders'
            )
        """)
        
        if not table_exists:
            print("   Таблица 'orders' не существует! Создаем...")
            await conn.execute("""
                CREATE TABLE orders (
                    id SERIAL PRIMARY KEY,
                    passenger_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    pickup_address TEXT NOT NULL,
                    pickup_location GEOGRAPHY(Point, 4326),
                    destination_address TEXT NOT NULL,
                    destination_location GEOGRAPHY(Point, 4326),
                    price DECIMAL(10, 2) NOT NULL,
                    tariff_name VARCHAR(50) DEFAULT 'economy',
                    status VARCHAR(50) DEFAULT 'searching_driver',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    driver_id INTEGER,
                    driver_name VARCHAR(100),
                    car_model VARCHAR(100),
                    car_number VARCHAR(20),
                    estimated_arrival INTEGER,
                    passenger_rating INTEGER CHECK (passenger_rating >= 1 AND passenger_rating <= 5)
                )
            """)
            print("   ✅ Таблица 'orders' создана")
        else:
            print("   ✅ Таблица 'orders' существует")
            
            # Проверяем и добавляем колонку passenger_id если её нет
            column_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'orders' 
                    AND column_name = 'passenger_id'
                )
            """)
            
            if not column_exists:
                print("   Добавляем колонку 'passenger_id'...")
                await conn.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN IF NOT EXISTS passenger_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                """)
                print("   ✅ Колонка 'passenger_id' добавлена")
            
            # Создаем индекс для ускорения поиска
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_passenger_status 
                ON orders(passenger_id, status)
            """)
            print("   ✅ Индекс создан")
        
        # 3. Проверяем таблицу tariffs (если нужна)
        print("\n3. Проверяем таблицу 'tariffs'...")
        
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'tariffs'
            )
        """)
        
        if not table_exists:
            print("   Таблица 'tariffs' не существует! Создаем...")
            await conn.execute("""
                CREATE TABLE tariffs (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    base_fee DECIMAL(10, 2) NOT NULL,
                    per_km_rate DECIMAL(10, 2) NOT NULL,
                    per_minute_rate DECIMAL(10, 2) NOT NULL,
                    min_fare DECIMAL(10, 2) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    car_class VARCHAR(50),
                    icon VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Добавляем базовые тарифы
            await conn.execute("""
                INSERT INTO tariffs (name, description, base_fee, per_km_rate, per_minute_rate, min_fare, car_class, icon)
                VALUES 
                    ('economy', 'Эконом', 100, 30, 5, 200, 'B', '🚗'),
                    ('comfort', 'Комфорт', 150, 40, 7, 300, 'C', '🚙'),
                    ('business', 'Бизнес', 250, 60, 10, 500, 'E', '🚘'),
                    ('minivan', 'Минивэн', 200, 50, 8, 400, 'V', '🚐')
                ON CONFLICT (name) DO NOTHING
            """)
            print("   ✅ Таблица 'tariffs' создана с базовыми данными")
        
        # 4. Показываем итоговую структуру
        print("\n" + "="*50)
        print("📊 ТЕКУЩАЯ СТРУКТУРА БАЗЫ ДАННЫХ:")
        print("="*50)
        
        # Структура users
        print("\n📋 Таблица 'users':")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            null_info = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']:20} {col['data_type']:20} {null_info:15} {default}")
        
        # Структура orders
        print("\n📋 Таблица 'orders':")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'orders'
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            null_info = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']:20} {col['data_type']:20} {null_info:15} {default}")
        
        # Проверяем данные
        print("\n📊 ДАННЫЕ В БАЗЕ:")
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        orders_count = await conn.fetchval("SELECT COUNT(*) FROM orders")
        print(f"   👤 Пользователей: {users_count}")
        print(f"   🚕 Заказов: {orders_count}")
        
        print("\n✅ РЕМОНТ БАЗЫ ДАННЫХ ЗАВЕРШЕН!")
        
    except Exception as e:
        print(f"❌ Ошибка при ремонте базы данных: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await conn.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(repair_database())