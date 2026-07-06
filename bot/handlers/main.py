import os
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from app.database.db import AsyncSessionLocal
from app.repositories.repos import ExerciseRepo, ServiceRepo, GalleryRepo, UserRepo
from bot.keyboards.menus import main_menu_kb, exercises_kb, exercise_detail_kb, services_kb, service_detail_kb, gallery_kb, contact_kb

router = Router()
logger = logging.getLogger(__name__)
TRAINER_USERNAME = "Papa_Kult"
WELCOME_PHOTO = "AgACAgIAAxkBAAMHakVxscTYsjrnVGqjQkZI95rCE-cAAgoZaxtmVTBKPYdOqk_QJtcBAAMCAAN4AAM8BA"
USDT_ADDRESS = "TES8Z2VYduByHczLBj87vTqJDECGbFdEyH"

SERVICE_DESCRIPTIONS = {
    "consultation": "Консультация\n\nПерсональная онлайн-консультация.\n\nДлительность: 60 минут\n\nСтоимость: ${price} USDT",
    "program": "Программа тренировок\n\nИндивидуальная программа под твои цели.\n\nПрограмма на 8-12 недель\n\nСтоимость: ${price} USDT",
    "diet": "Составление диеты\n\nПерсональный план питания.\n\nРасчёт КБЖУ, меню на неделю\n\nСтоимость: ${price} USDT",
    "analyses": "Разбор анализов\n\nДетальный анализ результатов крови.\n\nСтоимость: ${price} USDT",
    "online": "Онлайн-ведение месяц. Каждый день на связи. Разбор тренировок, контроль питания, корректировка программы. Стоимость: 250 USDT",
    "steroids": "Курс стероидов\n\nИндивидуально подобранный курс.\n\nПодбор препаратов, ПКТ включена\n\nТолько для совершеннолетних\n\nСтоимость: ${price} USDT",
}

DEFAULTS = {"consultation": 125, "program": 150, "diet": 125, "analyses": 150, "steroids": 125, "online": 250}

@router.message(CommandStart())
async def cmd_start(message: Message):
    async with AsyncSessionLocal() as session:
        await UserRepo(session).get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "Пользователь",
        )
    text = "Привет, " + message.from_user.first_name + "! 👋\n\nЖми на кнопку ниже 👇"
    await message.answer_photo(photo=WELCOME_PHOTO, caption=text, reply_markup=main_menu_kb())

@router.callback_query(F.data.startswith("back:"))
async def cb_back(call: CallbackQuery):
    target = call.data.split(":")[1]
    if target == "main":
        await call.message.delete()
        await call.message.answer_photo(photo=WELCOME_PHOTO, caption="Выбери раздел:", reply_markup=main_menu_kb())
    elif target == "exercises":
        await show_exercises(call)
    elif target == "services":
        await call.message.delete()
        await call.message.answer("Платные услуги\n\nВыбери услугу:", reply_markup=services_kb())

@router.callback_query(F.data == "section:exercises")
async def cb_section_exercises(call: CallbackQuery):
    await show_exercises(call)

async def show_exercises(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        exercises = await ExerciseRepo(session).get_all()
    await call.message.delete()
    if not exercises:
        await call.message.answer("Упражнения\n\nПока упражнений нет!", reply_markup=main_menu_kb())
        return
    await call.message.answer("Упражнения\n\nВыбери упражнение:", reply_markup=exercises_kb(exercises))

@router.callback_query(F.data.startswith("exercise:"))
async def cb_exercise_detail(call: CallbackQuery):
    exercise_id = int(call.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        ex = await ExerciseRepo(session).get_by_id(exercise_id)
    if not ex:
        await call.answer("Упражнение не найдено", show_alert=True)
        return
    caption = ex.name
    if ex.description:
        caption += "\n\n" + ex.description
    await call.message.delete()
    if ex.video_file_id:
        await call.message.answer_video(video=ex.video_file_id, caption=caption, reply_markup=exercise_detail_kb(exercise_id))
    else:
        await call.message.answer(caption, reply_markup=exercise_detail_kb(exercise_id))

@router.callback_query(F.data == "section:services")
async def cb_section_services(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("Платные услуги\n\nВыбери услугу:", reply_markup=services_kb())

@router.callback_query(F.data.startswith("service:"))
async def cb_service_detail(call: CallbackQuery):
    service_key = call.data.split(":")[1]
    async with AsyncSessionLocal() as session:
        svc = await ServiceRepo(session).get_by_key(service_key)
    template = SERVICE_DESCRIPTIONS.get(service_key, "Описание услуги")
    price = svc.price_usd if svc else DEFAULTS.get(service_key, "?")
    text = template.replace("${price}", str(price))
    await call.message.delete()
    await call.message.answer(text, reply_markup=service_detail_kb(service_key))

@router.callback_query(F.data.startswith("buy:"))
async def cb_buy_service(call: CallbackQuery):
    text = "Оплата в USDT TRC-20\n\nОтправь нужную сумму на адрес:\n\n" + USDT_ADDRESS + "\n\nСеть: Tron TRC-20\nОтправляй только USDT в сети TRC-20\n\nПосле оплаты напиши тренеру для подтверждения:"
    await call.message.answer(text, reply_markup=contact_kb(TRAINER_USERNAME))

@router.callback_query(F.data == "section:gallery")
async def cb_section_gallery(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        photos = await GalleryRepo(session).get_all()
    await call.message.delete()
    if not photos:
        await call.message.answer("Фотогалерея\n\nФото скоро появятся!", reply_markup=gallery_kb())
        return
    chunk = photos[:10]
    media_group = [InputMediaPhoto(media=p.file_id, caption=p.caption or ("Галерея" if i == 0 else None)) for i, p in enumerate(chunk)]
    await call.message.answer_media_group(media=media_group)
    await call.message.answer("Фотогалерея", reply_markup=gallery_kb())

@router.callback_query(F.data == "section:contact")
async def cb_section_contact(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("Написать тренеру\n\nНажми кнопку ниже:", reply_markup=contact_kb(TRAINER_USERNAME))
