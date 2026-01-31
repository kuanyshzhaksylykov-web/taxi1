import os
import json
from typing import List, Optional
from pathlib import Path

try:
    # Для Pydantic 2.5+
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator
except ImportError:
    # Для старых версий
    from pydantic import BaseSettings, Field, validator
    SettingsConfigDict = None
    field_validator = validator

class Settings(BaseSettings):
    """Настройки такси-бота"""
    
    # === TELEGRAM BOT ===
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    BOT_USERNAME: Optional[str] = Field(None, env="BOT_USERNAME")
    
    # === DATABASE ===
    DB_HOST: str = Field("localhost", env="DB_HOST")
    DB_PORT: int = Field(5432, env="DB_PORT")
    DB_NAME: str = Field("taxi", env="DB_NAME")
    DB_USER: str = Field("postgres", env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    
    # === REDIS ===
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    
    # === YANDEX MAPS ===
    YANDEX_MAPS_API_KEY: Optional[str] = Field(None, env="YANDEX_MAPS_API_KEY")
    
    # === YOOKASSA ===
    YOOKASSA_SHOP_ID: Optional[str] = Field(None, env="YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY: Optional[str] = Field(None, env="YOOKASSA_SECRET_KEY")
    
    # === SERVER CONFIG ===
    SERVER_URL: str = Field("http://localhost:8000", env="SERVER_URL")
    WEBHOOK_PATH: str = Field("/webhook", env="WEBHOOK_PATH")
    WEBHOOK_SECRET: Optional[str] = Field(None, env="WEBHOOK_SECRET")
    API_TIMEOUT: int = Field(30, env="API_TIMEOUT")
    
    # === ADMIN SETTINGS ===
    ADMIN_IDS: List[int] = Field(default_factory=list, env="ADMIN_IDS")
    SUPPORT_CHAT_ID: Optional[int] = Field(None, env="SUPPORT_CHAT_ID")
    
    # === BOT SETTINGS ===
    DEBUG: bool = Field(True, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    MAX_ORDER_SEARCH_TIME: int = Field(120, env="MAX_ORDER_SEARCH_TIME")
    DRIVER_RESPONSE_TIMEOUT: int = Field(30, env="DRIVER_RESPONSE_TIMEOUT")
    
    # Конфигурация для Pydantic 2.5+
    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"  # Игнорировать дополнительные поля в .env
        )
    else:
        # Для старых версий
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            extra = "ignore"  # Игнорировать дополнительные поля
    
    # Валидатор для ADMIN_IDS
    @field_validator('ADMIN_IDS', mode='before')
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            # Убираем пробелы
            v = v.strip()
            
            # Если строка начинается с [ и заканчивается ] - это JSON
            if v.startswith('[') and v.endswith(']'):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            
            # Если есть запятые - разделяем
            if ',' in v:
                # Разделяем по запятым
                parts = [part.strip() for part in v.split(',')]
                # Фильтруем пустые строки и конвертируем в int
                return [int(part) for part in parts if part]
            
            # Если это одно число
            try:
                return [int(v)]
            except ValueError:
                pass
        
        # Если это уже список
        elif isinstance(v, list):
            return v
        
        # По умолчанию пустой список
        return []
    
    @property
    def database_url(self) -> str:
        """URL для подключения к PostgreSQL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_url(self) -> str:
        """URL для подключения к Redis"""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def is_webhook(self) -> bool:
        """Используется ли webhook"""
        return bool(self.WEBHOOK_SECRET)

# Создаем папку для логов
Path("logs").mkdir(exist_ok=True)

# Загружаем настройки
settings = Settings()