import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Открыть Papa_Kult", web_app=WebAppInfo(url="https://papakult-app.vercel.app"))],
        [InlineKeyboardButton(text="✉️ Написать в личку", callback_data="section:contact")],
    ])

def exercises_kb(exercises: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=ex.name, callback_data=f"exercise:{ex.id}")] for ex in exercises]
    buttons.append([back_btn("main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def exercise_detail_kb(exercise_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[back_btn("exercises")]])

def services_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗣 Консультация", callback_data="service:consultation")],
        [InlineKeyboardButton(text="📋 Программа тренировок", callback_data="service:program")],
        [InlineKeyboardButton(text="🥗 Составление диеты", callback_data="service:diet")],
        [InlineKeyboardButton(text="🧪 Разбор анализов", callback_data="service:analyses")],
        [InlineKeyboardButton(text="💊 Курс стероидов", callback_data="service:steroids")],
        [InlineKeyboardButton(text="🎯 Онлайн-ведение", callback_data="service:online")],
        [back_btn("main")],
    ])

def service_detail_kb(service_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить в USDT", callback_data=f"buy:{service_key}")],
        [InlineKeyboardButton(text="✉️ Написать тренеру", callback_data="section:contact")],
        [back_btn("services")],
    ])

def gallery_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[back_btn("main")]])

def contact_kb(trainer_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✉️ @{trainer_username}", url=f"https://t.me/{trainer_username}")],
        [back_btn("main")],
    ])

def back_btn(target: str) -> InlineKeyboardButton:
    labels = {"main": "⬅️ Главное меню", "exercises": "⬅️ К упражнениям", "services": "⬅️ К услугам"}
    return InlineKeyboardButton(text=labels.get(target, "⬅️ Назад"), callback_data=f"back:{target}")
