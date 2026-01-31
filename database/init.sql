-- Инициализация базы данных такси

-- Расширения
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ENUM типы
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'blocked');
CREATE TYPE user_type AS ENUM ('passenger', 'driver', 'admin');
CREATE TYPE order_status AS ENUM (
    'created', 
    'searching_driver',
    'driver_assigned',
    'driver_arrived',
    'in_progress',
    'completed',
    'cancelled',
    'failed'
);
CREATE TYPE driver_status AS ENUM ('offline', 'online', 'busy', 'break');
CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'failed', 'refunded');
CREATE TYPE payment_method AS ENUM ('cash', 'card', 'yoomoney', 'sbp');

-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    username VARCHAR(100),
    user_type user_type DEFAULT 'passenger',
    status user_status DEFAULT 'active',
    rating DECIMAL(3,2) DEFAULT 5.0,
    total_rides INTEGER DEFAULT 0,
    language_code VARCHAR(10) DEFAULT 'ru',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_rating_range CHECK (rating >= 1 AND rating <= 5)
);

-- Таблица водителей
CREATE TABLE drivers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    car_brand VARCHAR(50),
    car_model VARCHAR(50),
    car_year INTEGER,
    car_color VARCHAR(30),
    car_plate VARCHAR(20) UNIQUE,
    license_number VARCHAR(50) UNIQUE,
    license_expiry DATE,
    insurance_number VARCHAR(50),
    insurance_expiry DATE,
    status driver_status DEFAULT 'offline',
    current_location GEOMETRY(Point, 4326),
    balance DECIMAL(12,2) DEFAULT 0.00,
    total_earnings DECIMAL(12,2) DEFAULT 0.00,
    total_rides INTEGER DEFAULT 0,
    acceptance_rate DECIMAL(5,2) DEFAULT 100.00,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_reason TEXT,
    verified_at TIMESTAMP WITH TIME ZONE,
    documents JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{"notifications": true, "sound": true}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица заказов
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    passenger_id INTEGER REFERENCES users(id),
    driver_id INTEGER REFERENCES drivers(id),
    
    -- Локации
    pickup_address TEXT NOT NULL,
    pickup_location GEOMETRY(Point, 4326),
    destination_address TEXT NOT NULL,
    destination_location GEOMETRY(Point, 4326),
    
    -- Детали поездки
    distance_km DECIMAL(8,2),
    duration_minutes INTEGER,
    price DECIMAL(10,2) NOT NULL,
    tariff_name VARCHAR(50) DEFAULT 'economy',
    
    -- Статусы
    status order_status DEFAULT 'created',
    payment_status payment_status DEFAULT 'pending',
    payment_method payment_method,
    
    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP WITH TIME ZONE,
    arrived_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Отмена
    cancelled_by INTEGER REFERENCES users(id),
    cancellation_reason VARCHAR(100),
    
    -- Рейтинги
    passenger_rating INTEGER CHECK (passenger_rating >= 1 AND passenger_rating <= 5),
    driver_rating INTEGER CHECK (driver_rating >= 1 AND driver_rating <= 5),
    passenger_comment TEXT,
    driver_comment TEXT,
    
    -- Метаданные
    metadata JSONB DEFAULT '{}',
    route_polyline TEXT,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица транзакций
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_uuid UUID DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id),
    order_id INTEGER REFERENCES orders(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    type VARCHAR(50) NOT NULL, -- 'ride_payment', 'driver_payout', 'refund', 'bonus'
    status VARCHAR(20) DEFAULT 'pending',
    payment_system VARCHAR(50),
    payment_id VARCHAR(100),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Таблица геолокаций водителей
CREATE TABLE driver_locations (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER REFERENCES drivers(id) ON DELETE CASCADE,
    location GEOMETRY(Point, 4326) NOT NULL,
    accuracy DECIMAL(5,2),
    speed DECIMAL(5,2),
    heading INTEGER,
    altitude DECIMAL(8,2),
    battery_level INTEGER,
    is_moving BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица тарифов
CREATE TABLE tariffs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    base_fee DECIMAL(10,2) NOT NULL,
    per_km_fee DECIMAL(10,2) NOT NULL,
    per_minute_fee DECIMAL(10,2) NOT NULL,
    min_price DECIMAL(10,2) NOT NULL,
    max_price DECIMAL(10,2),
    surge_multiplier DECIMAL(3,2) DEFAULT 1.00,
    is_active BOOLEAN DEFAULT TRUE,
    icon VARCHAR(50),
    car_types VARCHAR(200)[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица адресов пользователей
CREATE TABLE user_addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL, -- 'дом', 'работа', 'мама'
    address TEXT NOT NULL,
    location GEOMETRY(Point, 4326),
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица настроек
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ИНДЕКСЫ для производительности

-- Индексы для users
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_status ON users(status);

-- Индексы для drivers
CREATE INDEX idx_drivers_user_id ON drivers(user_id);
CREATE INDEX idx_drivers_status ON drivers(status);
CREATE INDEX idx_drivers_verified ON drivers(is_verified) WHERE is_verified = TRUE;
CREATE INDEX idx_drivers_location ON drivers USING GIST(current_location);

-- Индексы для orders
CREATE INDEX idx_orders_passenger_id ON orders(passenger_id);
CREATE INDEX idx_orders_driver_id ON orders(driver_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_uuid ON orders(order_uuid);
CREATE INDEX idx_orders_pickup_location ON orders USING GIST(pickup_location);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);

-- Индексы для driver_locations
CREATE INDEX idx_driver_locations_driver_id ON driver_locations(driver_id);
CREATE INDEX idx_driver_locations_recorded_at ON driver_locations(recorded_at DESC);
CREATE INDEX idx_driver_locations_geo ON driver_locations USING GIST(location);

-- Индексы для транзакций
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_order_id ON transactions(order_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);

-- ТРИГГЕРЫ для обновления updated_at

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drivers_updated_at 
    BEFORE UPDATE ON drivers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_addresses_updated_at 
    BEFORE UPDATE ON user_addresses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ФУНКЦИИ

-- Функция для поиска ближайших водителей
CREATE OR REPLACE FUNCTION find_nearby_drivers(
    search_point GEOMETRY(Point, 4326),
    radius_km INTEGER DEFAULT 5,
    max_drivers INTEGER DEFAULT 10,
    car_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    driver_id INTEGER,
    user_id INTEGER,
    distance_meters DECIMAL,
    car_brand VARCHAR,
    car_model VARCHAR,
    rating DECIMAL,
    estimated_arrival_minutes INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id as driver_id,
        u.id as user_id,
        ST_Distance(
            search_point::geography,
            dl.location::geography
        ) as distance_meters,
        d.car_brand,
        d.car_model,
        u.rating,
        CEILING(
            ST_Distance(
                search_point::geography,
                dl.location::geography
            ) / 500.0  -- предполагаем 500 метров в минуту
        )::INTEGER as estimated_arrival_minutes
    FROM drivers d
    JOIN users u ON d.user_id = u.id
    JOIN (
        SELECT DISTINCT ON (driver_id) driver_id, location
        FROM driver_locations
        WHERE recorded_at > NOW() - INTERVAL '2 minutes'
        ORDER BY driver_id, recorded_at DESC
    ) dl ON dl.driver_id = d.id
    WHERE d.status = 'online'
      AND d.is_verified = TRUE
      AND u.status = 'active'
      AND ST_DWithin(
            search_point::geography,
            dl.location::geography,
            radius_km * 1000
          )
      AND (car_type IS NULL OR d.car_model ILIKE '%' || car_type || '%')
    ORDER BY distance_meters ASC
    LIMIT max_drivers;
END;
$$ LANGUAGE plpgsql;

-- Функция для расчета стоимости поездки
CREATE OR REPLACE FUNCTION calculate_ride_price(
    distance_km DECIMAL,
    duration_minutes INTEGER,
    tariff_id INTEGER DEFAULT 1
)
RETURNS DECIMAL AS $$
DECLARE
    base_fee DECIMAL;
    per_km_fee DECIMAL;
    per_minute_fee DECIMAL;
    min_price DECIMAL;
    total_price DECIMAL;
BEGIN
    SELECT t.base_fee, t.per_km_fee, t.per_minute_fee, t.min_price
    INTO base_fee, per_km_fee, per_minute_fee, min_price
    FROM tariffs t
    WHERE t.id = tariff_id AND t.is_active = TRUE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Тариф не найден или неактивен';
    END IF;
    
    total_price := base_fee + (distance_km * per_km_fee) + (duration_minutes * per_minute_fee);
    
    IF total_price < min_price THEN
        total_price := min_price;
    END IF;
    
    RETURN ROUND(total_price, 2);
END;
$$ LANGUAGE plpgsql;

-- Функция для обновления рейтинга
CREATE OR REPLACE FUNCTION update_user_rating(user_id_param INTEGER)
RETURNS VOID AS $$
DECLARE
    avg_rating DECIMAL;
BEGIN
    SELECT AVG(rating) INTO avg_rating
    FROM (
        SELECT driver_rating as rating
        FROM orders 
        WHERE passenger_id = user_id_param 
          AND driver_rating IS NOT NULL
        UNION ALL
        SELECT passenger_rating as rating
        FROM orders 
        WHERE driver_id = user_id_param 
          AND passenger_rating IS NOT NULL
    ) ratings;
    
    IF avg_rating IS NOT NULL THEN
        UPDATE users 
        SET rating = ROUND(avg_rating::DECIMAL, 2)
        WHERE id = user_id_param;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ВСТАВКА НАЧАЛЬНЫХ ДАННЫХ

-- Тарифы
INSERT INTO tariffs (name, description, base_fee, per_km_fee, per_minute_fee, min_price, icon) VALUES
('Эконом', 'Бюджетный вариант', 50.00, 15.00, 5.00, 100.00, '💰'),
('Комфорт', 'Комфортабельный автомобиль', 100.00, 25.00, 8.00, 200.00, '🚗'),
('Бизнес', 'Премиум класс', 200.00, 40.00, 12.00, 400.00, '⭐'),
('Доставка', 'Перевозка грузов', 150.00, 20.00, 6.00, 250.00, '📦');

-- Настройки системы
INSERT INTO settings (key, value, description) VALUES
('system_name', '"Такси Сервис"', 'Название системы'),
('commission_rate', '0.20', 'Комиссия сервиса (20%)'),
('driver_search_radius_km', '5', 'Радиус поиска водителей'),
('driver_response_timeout_sec', '30', 'Время на ответ водителя'),
('max_order_search_time_min', '2', 'Максимальное время поиска'),
('min_payout_amount', '500', 'Минимальная сумма вывода'),
('support_phone', '"+78001234567"', 'Телефон поддержки'),
('emergency_phone', '"+78009876543"', 'Экстренный телефон'),
('currency', '"RUB"', 'Основная валюта'),
('timezone', '"Europe/Moscow"', 'Часовой пояс');

-- Тестовый администратор
INSERT INTO users (telegram_id, phone, first_name, last_name, user_type) 
VALUES (777777777, '+79167777777', 'Админ', 'Системы', 'admin');

-- Сообщение об успешном создании
DO $$
BEGIN
    RAISE NOTICE 'База данных такси-сервиса успешно создана!';
    RAISE NOTICE 'Таблицы: users, drivers, orders, transactions, tariffs';
    RAISE NOTICE 'Созданы тестовые данные и функции';
END $$;