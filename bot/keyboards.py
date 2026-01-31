from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from typing import List, Dict, Any

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура главного меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚗 Заказать такси")],
            [KeyboardButton(text="📊 Мои поездки")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🆘 Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_location_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки местоположения"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="📝 Ввести адрес вручную")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_tariff_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора тарифа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚗 Эконом - от 150₽", callback_data="tariff_economy"),
                InlineKeyboardButton(text="🚙 Комфорт - от 250₽", callback_data="tariff_comfort")
            ],
            [
                InlineKeyboardButton(text="⭐ Бизнес - от 400₽", callback_data="tariff_business"),
                InlineKeyboardButton(text="🚐 Доставка - от 300₽", callback_data="tariff_delivery")
            ]
        ]
    )

def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")
            ]
        ]
    )

def get_driver_keyboard() -> ReplyKeyboardMarkup:
    """Меню для водителей"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Выйти на линию"), KeyboardButton(text="🔴 Уйти с линии")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="📦 Активные заказы"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🆘 Поддержка")]
        ],
        resize_keyboard=True
    )

def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора способа оплаты"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💵 Наличные", callback_data="payment_cash"),
                InlineKeyboardButton(text="💳 Карта", callback_data="payment_card")
            ],
            [
                InlineKeyboardButton(text="📱 ЮMoney", callback_data="payment_yoomoney"),
                InlineKeyboardButton(text="🏦 СБП", callback_data="payment_sbp")
            ]
        ]
    )

def get_rating_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для оценки поездки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1⭐", callback_data="rate_1"),
                InlineKeyboardButton(text="2⭐", callback_data="rate_2"),
                InlineKeyboardButton(text="3⭐", callback_data="rate_3"),
                InlineKeyboardButton(text="4⭐", callback_data="rate_4"),
                InlineKeyboardButton(text="5⭐", callback_data="rate_5")
            ]
        ]
    )

def get_web_app_keyboard(url: str) -> ReplyKeyboardMarkup:
    """Клавиатура с веб-приложением для водителей"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚗 Открыть приложение для водителей", web_app=WebAppInfo(url=url))]
        ],
        resize_keyboard=True
    )

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications")],
            [InlineKeyboardButton(text="💳 Способ оплаты", callback_data="settings_payment")],
            [InlineKeyboardButton(text="🌐 Язык", callback_data="settings_language")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="settings_profile")]
        ]
    )