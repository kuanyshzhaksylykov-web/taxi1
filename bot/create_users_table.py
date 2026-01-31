# Создайте файл bot/create_users_table.py
import asyncio
import asyncpg

async def create_tables():
    DATABASE_URL = "postgresql://postgres:StrongPass123!@localhost:5432/taxi"
    
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        phone VARCHAR(20) UNIQUE,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        user_type VARCHAR(20) DEFAULT 'passenger',
        rating DECIMAL(3,2) DEFAULT 5.0,
        is_blocked BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        pickup_address TEXT,
        pickup_lat DECIMAL(10,6),
        pickup_lon DECIMAL(10,6),
        destination_address TEXT,
        destination_lat DECIMAL(10,6),
        destination_lon DECIMAL(10,6),
        price DECIMAL(10,2),
        status VARCHAR(50) DEFAULT 'pending',
        driver_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(sql)
    await conn.close()
    print("✅ Таблицы созданы!")

asyncio.run(create_tables())