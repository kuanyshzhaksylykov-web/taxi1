#!/usr/bin/env python3
"""
Простое создание таблиц через psycopg2
"""

import psycopg2
from psycopg2 import sql

def create_tables():
    """Создание таблиц через psycopg2"""
    
    # Параметры подключения
    db_params = {
        'host': 'localhost',
        'port': '5432',
        'database': 'taxi',
        'user': 'postgres',
        'password': 'StrongPass123!'
    }
    
    # SQL для создания таблиц
    sql_commands = [
        """
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
        """,
        """
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
        """,
        """
        CREATE TABLE IF NOT EXISTS drivers (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id),
            car_model VARCHAR(100),
            car_plate VARCHAR(20),
            status VARCHAR(20) DEFAULT 'offline',
            current_lat DECIMAL(10,6),
            current_lon DECIMAL(10,6),
            is_verified BOOLEAN DEFAULT FALSE,
            rating DECIMAL(3,2) DEFAULT 5.0
        );
        """
    ]
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Выполняем каждый SQL запрос
        for sql_command in sql_commands:
            cursor.execute(sql_command)
            print(f"✅ Выполнен: {sql_command[:50]}...")
        
        cursor.close()
        conn.close()
        
        print("✅ Все таблицы успешно созданы!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

if __name__ == "__main__":
    create_tables()