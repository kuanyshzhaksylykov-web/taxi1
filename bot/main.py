import asyncio
import sys
from pathlib import Path
from loguru import logger

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand
from aiogram.utils.markdown import hbold
import aiohttp
from aiogram.client.default import DefaultBotProperties
from config import settings
from database import Database
from handlers import router

# Настройка логирования
logger.add(
    "logs/bot.log",
    rotation="500 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=settings.LOG_LEVEL
)

class TaxiBot:
    """Современный бот такси-сервиса для aiogram 3.x"""
    
    def __init__(self):
        self.bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        
        # Регистрируем роутеры
        self.dp.include_router(router)
        
        # Регистрируем middleware
        self.setup_middleware()
        
    def setup_middleware(self):
        """Настройка middleware"""
        # Здесь можно добавить middleware для ограничения запросов, логирования и т.д.
        pass
    
    async def set_bot_commands(self):
        """Установка команд меню бота"""
        commands = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="order", description="Заказать такси"),
            BotCommand(command="history", description="История поездок"),
            BotCommand(command="settings", description="Настройки"),
            BotCommand(command="driver", description="Для водителей"),
            BotCommand(command="balance", description="Баланс")
        ]
        
        await self.bot.set_my_commands(commands)
    
    async def notify_admins(self, message: str):
        """Уведомление администраторов"""
        for admin_id in settings.ADMIN_IDS:
            try:
                await self.bot.send_message(admin_id, message)
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    async def health_check(self):
        """Проверка здоровья всех компонентов"""
        logger.info("Проверка подключений...")
        
        # Проверка базы данных
        db_ok = await Database.health_check()
        if db_ok:
            logger.info("✅ База данных доступна")
        else:
            logger.error("❌ База данных недоступна")
        
        # Проверка Telegram API
        try:
            me = await self.bot.get_me()
            logger.info(f"✅ Telegram API доступен: @{me.username}")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram API недоступен: {e}")
            return False
    
    async def on_startup(self):
        """Действия при запуске бота"""
        logger.info("=" * 50)
        logger.info("🚀 ТАКСИ-БОТ ЗАПУСКАЕТСЯ")
        logger.info(f"Версия: Python {sys.version}")
        logger.info("=" * 50)
        
        # Установка команд бота
        await self.set_bot_commands()
        
        # Проверка подключений
        if not await self.health_check():
            logger.error("❌ Не удалось подключиться ко всем сервисам")
            return False
        
        # Отправка уведомления администраторам
        await self.notify_admins("🤖 Такси-бот запущен и готов к работе!")
        
        logger.info("✅ Бот успешно запущен")
        return True
    
    async def on_shutdown(self):
        """Действия при остановке бота"""
        logger.info("=== ОСТАНОВКА БОТА ===")
        
        # Закрытие пула соединений с БД
        await Database.close_pool()
        
        # Отправка уведомления администраторам
        await self.notify_admins("⚠️ Такси-бот остановлен")
        
        # Закрытие сессии бота
        await self.bot.session.close()
    
    async def run(self):
        """Запуск бота"""
        # Действия при запуске
        if not await self.on_startup():
            logger.error("Не удалось запустить бота")
            return
        
        try:
            # Запуск бота
            logger.info("🤖 Бот запущен. Ожидание сообщений...")
            await self.dp.start_polling(self.bot)
            
        except KeyboardInterrupt:
            logger.info("⏹ Остановка бота по запросу пользователя")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            
        finally:
            # Действия при остановке
            await self.on_shutdown()

async def test_connections():
    """Тестирование подключений"""
    logger.info("Тестирование подключений...")
    
    # Проверка настроек
    try:
        from config import settings
        logger.info(f"✅ Настройки загружены: BOT_TOKEN={bool(settings.BOT_TOKEN)}")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки настроек: {e}")
        return False
    
    # Проверка базы данных
    try:
        db_ok = await Database.health_check()
        if db_ok:
            logger.info("✅ База данных доступна")
        else:
            logger.error("❌ База данных недоступна")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False
    
    return True

async def main():
    """Основная функция"""
    # Создаем папку для логов
    Path("logs").mkdir(exist_ok=True)
    
    # Тестовый режим
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = await test_connections()
        if success:
            logger.info("✅ Все тесты пройдены успешно!")
        else:
            logger.error("❌ Тесты не пройдены")
        sys.exit(0 if success else 1)
    
    # Основной запуск
    try:
        bot = TaxiBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("⏹ Остановка бота")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())