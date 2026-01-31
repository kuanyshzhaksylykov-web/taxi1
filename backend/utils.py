import math
from datetime import datetime
from typing import Tuple, Optional
import aiohttp
import asyncio
from loguru import logger

from config import settings

async def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """Геокодирование адреса с помощью Яндекс.Карт"""
    if not settings.YANDEX_GEOCODER_API_KEY:
        logger.warning("Yandex Geocoder API key not set")
        return None
    
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": settings.YANDEX_GEOCODER_API_KEY,
        "geocode": address,
        "format": "json",
        "lang": "ru_RU"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Парсим координаты
                    try:
                        pos = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
                        lon, lat = map(float, pos.split())
                        return lat, lon
                    except (KeyError, IndexError, ValueError):
                        logger.error(f"Failed to parse geocoding response: {data}")
                        return None
                else:
                    logger.error(f"Geocoding failed: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None

async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """Обратное геокодирование координат в адрес"""
    if not settings.YANDEX_GEOCODER_API_KEY:
        logger.warning("Yandex Geocoder API key not set")
        return None
    
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": settings.YANDEX_GEOCODER_API_KEY,
        "geocode": f"{lon},{lat}",
        "format": "json",
        "lang": "ru_RU",
        "kind": "house"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    try:
                        address = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
                        return address
                    except (KeyError, IndexError):
                        logger.error(f"Failed to parse reverse geocoding response")
                        return f"{lat:.6f}, {lon:.6f}"
                else:
                    logger.error(f"Reverse geocoding failed: {response.status}")
                    return f"{lat:.6f}, {lon:.6f}"
    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        return f"{lat:.6f}, {lon:.6f}"

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расчет расстояния между двумя точками в км"""
    R = 6371.0  # Радиус Земли в км
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return round(R * c, 2)

def calculate_eta(distance_km: float, traffic_level: float = 1.0) -> int:
    """Расчет времени прибытия в минутах"""
    average_speed_kmh = 40.0 / traffic_level
    time_hours = distance_km / average_speed_kmh
    eta_minutes = int(math.ceil(time_hours * 60))
    return max(3, eta_minutes)

def format_duration(seconds: int) -> str:
    """Форматирование длительности"""
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} мин"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ч {minutes} мин"

def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Форматирование даты и времени"""
    return dt.strftime(format_str)

def calculate_fare(
    distance_km: float,
    duration_minutes: int,
    base_fee: float = 50.0,
    per_km: float = 15.0,
    per_minute: float = 5.0,
    min_price: float = 100.0,
    surge: float = 1.0
) -> float:
    """Расчет стоимости поездки"""
    fare = base_fee + (distance_km * per_km) + (duration_minutes * per_minute)
    fare *= surge
    fare = max(fare, min_price)
    return math.ceil(fare)

async def get_traffic_level(lat: float, lon: float) -> float:
    """Получить уровень трафика (заглушка)"""
    # В реальном проекте можно использовать API Яндекс.Пробки
    hour = datetime.now().hour
    
    if 7 <= hour < 10 or 17 <= hour < 20:
        return 1.8  # Час пик
    elif 0 <= hour < 5:
        return 0.9  # Ночь
    else:
        return 1.2  # Обычное время