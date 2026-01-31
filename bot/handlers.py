from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Location
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from database import Database
from utils import calculate_distance, calculate_eta, calculate_price, format_price
from keyboards import (
    get_main_keyboard, 
    get_location_keyboard,
    get_tariff_keyboard,
    get_order_confirmation_keyboard,
    get_payment_keyboard,
    get_rating_keyboard,
    get_web_app_keyboard,
    get_settings_keyboard
)

router = Router()

# === STATES ===
class OrderStates(StatesGroup):
    waiting_location = State()
    waiting_destination = State()
    waiting_tariff = State()
    waiting_confirmation = State()

class PaymentStates(StatesGroup):
    waiting_payment = State()

class RatingStates(StatesGroup):
    waiting_rating = State()

# === COMMAND HANDLERS ===
@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
    logger.info(f"User {user.id} started bot")
    
    # Создаем или получаем пользователя
    user_data = await Database.get_or_create_user(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name or "",
        username=user.username or ""
    )
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"🚖 Добро пожаловать в Такси-Сервис!\n\n"
        f"Я помогу вам:\n"
        f"• 🚗 Заказать такси\n"
        f"• 📍 Вызвать водителя к месту\n"
        f"• 💳 Оплатить поездку\n"
        f"• 📊 Посмотреть историю поездок\n\n"
        f"Выберите действие:"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 Помощь по использованию бота:\n\n"
        
        "🔹 Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/order - Заказать такси\n"
        "/history - История поездок\n"
        "/balance - Баланс и оплата\n"
        "/settings - Настройки\n\n"
        
        "🔹 Для водителей:\n"
        "/driver - Регистрация водителя\n\n"
        
        "🔹 Поддержка:\n"
        "По вопросам работы бота обращайтесь:\n"
        "@support_taxi_bot"
    )
    
    await message.answer(help_text)

@router.message(Command("order"))
@router.message(F.text == "🚗 Заказать такси")
async def order_taxi(message: Message, state: FSMContext):
    """Заказ такси"""
    # Проверяем активный заказ
    active_order = await Database.get_active_order(message.from_user.id)
    if active_order:
        await message.answer(
            "⚠️ У вас уже есть активный заказ!\n"
            "Дождитесь завершения текущей поездки.",
            reply_markup=await get_main_keyboard()
        )
        return
    
    await message.answer(
        "📍 Откуда поедем?\n\n"
        "Вы можете:\n"
        "• 📍 Отправить геолокацию\n"
        "• 📝 Ввести адрес вручную",
        reply_markup=get_location_keyboard()
    )
    
    await state.set_state(OrderStates.waiting_location)

@router.message(OrderStates.waiting_location, F.location)
async def handle_location(message: Message, location: Location, state: FSMContext):
    """Обработка геолокации"""
    lat = location.latitude
    lon = location.longitude
    
    await state.update_data(
        pickup_lat=lat,
        pickup_lon=lon,
        pickup_address="Текущее местоположение"
    )
    
    await message.answer(
        "✅ Местоположение получено!\n\n"
        "📍 Теперь введите адрес назначения:",
        reply_markup=None
    )
    
    await state.set_state(OrderStates.waiting_destination)

@router.message(OrderStates.waiting_location, F.text == "📝 Ввести адрес вручную")
async def request_address_manual(message: Message, state: FSMContext):
    """Запрос адреса вручную"""
    await message.answer(
        "Введите ваш адрес (например: ул. Ленина, 10):",
        reply_markup=None
    )

@router.message(OrderStates.waiting_location)
async def handle_manual_address(message: Message, state: FSMContext):
    """Обработка ручного ввода адреса"""
    address = message.text
    
    if len(address) < 5:
        await message.answer("Пожалуйста, введите полный адрес")
        return
    
    # Здесь должна быть геокодировка через API Яндекс.Карт
    # Пока используем тестовые координаты
    await state.update_data(
        pickup_lat=55.7558,
        pickup_lon=37.6176,
        pickup_address=address
    )
    
    await message.answer(
        f"✅ Адрес получен: {address}\n\n"
        "📍 Теперь введите адрес назначения:",
        reply_markup=None
    )
    
    await state.set_state(OrderStates.waiting_destination)

@router.message(OrderStates.waiting_destination)
async def handle_destination(message: Message, state: FSMContext):
    """Обработка адреса назначения"""
    destination = message.text
    
    if len(destination) < 5:
        await message.answer("Пожалуйста, введите полный адрес")
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    pickup_lat = data.get('pickup_lat', 55.7558)
    pickup_lon = data.get('pickup_lon', 37.6176)
    
    # Тестовые координаты назначения
    destination_lat = 55.7602
    destination_lon = 37.6185
    
    # Расчет расстояния и времени
    distance = calculate_distance(pickup_lat, pickup_lon, destination_lat, destination_lon)
    duration = calculate_eta(distance)
    
    await state.update_data(
        destination_address=destination,
        destination_lat=destination_lat,
        destination_lon=destination_lon,
        distance_km=distance,
        duration_minutes=duration
    )
    
    await message.answer(
        f"📍 Откуда: {data.get('pickup_address', 'Ваше местоположение')}\n"
        f"📍 Куда: {destination}\n"
        f"📏 Расстояние: {distance:.1f} км\n"
        f"⏱ Время: ~{duration} мин\n\n"
        f"Выберите тариф:",
        reply_markup=get_tariff_keyboard()
    )
    
    await state.set_state(OrderStates.waiting_tariff)

@router.callback_query(OrderStates.waiting_tariff, F.data.startswith("tariff_"))
async def handle_tariff_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора тарифа"""
    tariff_type = callback.data.split("_")[1]
    
    tariffs = {
        "economy": {"name": "🚗 Эконом", "base_fee": 50, "per_km": 15, "per_minute": 5},
        "comfort": {"name": "🚙 Комфорт", "base_fee": 100, "per_km": 25, "per_minute": 8},
        "business": {"name": "⭐ Бизнес", "base_fee": 200, "per_km": 40, "per_minute": 12},
        "delivery": {"name": "🚐 Доставка", "base_fee": 150, "per_km": 20, "per_minute": 6}
    }
    
    tariff = tariffs.get(tariff_type, tariffs["economy"])
    
    # Получаем данные из состояния
    data = await state.get_data()
    distance = data.get('distance_km', 5)
    duration = data.get('duration_minutes', 15)
    
    # Расчет цены
    price = calculate_price(distance, duration, tariff)
    
    await state.update_data(
        tariff_name=tariff["name"],
        price=price
    )
    
    await callback.message.edit_text(
        f"📋 Детали заказа:\n\n"
        f"📍 Откуда: {data.get('pickup_address', 'Ваше местоположение')}\n"
        f"📍 Куда: {data.get('destination_address', 'Адрес назначения')}\n"
        f"📏 Расстояние: {distance:.1f} км\n"
        f"⏱ Время: ~{duration} мин\n"
        f"🚗 Тариф: {tariff['name']}\n"
        f"💰 Стоимость: {format_price(price)}\n\n"
        f"Подтверждаете заказ?",
        reply_markup=get_order_confirmation_keyboard()
    )
    
    await state.set_state(OrderStates.waiting_confirmation)
    await callback.answer()

@router.callback_query(OrderStates.waiting_confirmation, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение заказа"""
    data = await state.get_data()
    
    # Получаем пользователя
    user = await Database.get_user_by_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text("❌ Ошибка: пользователь не найден")
        await state.clear()
        return
    
    # Создаем заказ
    order = await Database.create_order(
        passenger_id=user['id'],
        pickup_address=data.get('pickup_address', ''),
        pickup_lat=data.get('pickup_lat'),
        pickup_lon=data.get('pickup_lon'),
        destination_address=data.get('destination_address', ''),
        destination_lat=data.get('destination_lat'),
        destination_lon=data.get('destination_lon'),
        price=data.get('price', 0),
        tariff_name=data.get('tariff_name', 'Эконом')
    )
    
    if order:
        order_id = order['id']
        
        await callback.message.edit_text(
            f"✅ Заказ #{order_id} создан!\n\n"
            f"Ищем ближайшего водителя...\n"
            f"Обычно это занимает 1-2 минуты.\n\n"
            f"Статус заказа можно проверить в разделе 'Мои поездки'",
            reply_markup=await get_main_keyboard()
        )
        
        logger.info(f"Order #{order_id} created for user {callback.from_user.id}")
        
    else:
        await callback.message.edit_text(
            "❌ Ошибка при создании заказа\n"
            "Пожалуйста, попробуйте еще раз",
            reply_markup=await get_main_keyboard()
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(OrderStates.waiting_confirmation, F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена заказа"""
    await callback.message.edit_text(
        "❌ Заказ отменен\n\n"
        "Чтобы создать новый заказ, нажмите 'Заказать такси'",
        reply_markup=await get_main_keyboard()
    )
    
    await state.clear()
    await callback.answer()

@router.message(Command("driver"))
async def cmd_driver(message: Message):
    """Команда для водителей"""
    await message.answer(
        "🚗 Для водителей:\n\n"
        "Откройте веб-приложение для управления заказами:",
        reply_markup=get_web_app_keyboard("http://localhost:8080")
    )

@router.message(F.text == "📊 Мои поездки")
@router.message(Command("history"))
async def show_history(message: Message):
    """Показать историю поездок"""
    orders = await Database.get_user_orders(message.from_user.id, limit=5)
    
    if not orders:
        await message.answer(
            "📊 У вас пока нет поездок.\n"
            "Совершите первую поездку!",
            reply_markup=await get_main_keyboard()
        )
        return
    
    text = "📊 Ваши последние поездки:\n\n"
    
    for order in orders[:5]:
        status_emoji = {
            'completed': '✅',
            'cancelled': '❌',
            'in_progress': '🔄',
            'searching_driver': '🔍'
        }.get(order['status'], '📝')
        
        text += (
            f"{status_emoji} Заказ #{order['id']}\n"
            f"📅 {format_datetime(order['created_at'], 'short')}\n"
            f"📍 {format_address(order['pickup_address'], 20)} → {format_address(order['destination_address'], 20)}\n"
            f"💰 {format_price(order['price'])}\n"
            f"───\n"
        )
    
    await message.answer(text, reply_markup=await get_main_keyboard())

@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def show_settings(message: Message):
    """Показать настройки"""
    await message.answer(
        "⚙️ Настройки:\n\n"
        "Выберите настройку для изменения:",
        reply_markup=get_settings_keyboard()
    )

@router.message(F.text == "🆘 Помощь")
async def show_help(message: Message):
    """Показать помощь"""
    await cmd_help(message)

@router.message()
async def handle_unknown(message: Message):
    """Обработка неизвестных сообщений"""
    await message.answer(
        "Я не понял ваше сообщение.\n"
        "Используйте кнопки меню или команды.\n"
        "Для начала работы нажмите /start",
        reply_markup=get_main_keyboard()
    )