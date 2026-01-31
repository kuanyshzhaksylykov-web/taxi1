import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

class Settings:
    """Простые настройки без pydantic"""
    
    def __init__(self):
        self.DEBUG = os.getenv("DEBUG", "True").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        self.DB_NAME = os.getenv("DB_NAME", "taxi")
        self.DB_USER = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "StrongPass123!")
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    
    @property
    def database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Создаем настройки
settings = Settings()

# Создаем папку logs
Path("logs").mkdir(exist_ok=True)

print("✅ Настройки загружены успешно!")