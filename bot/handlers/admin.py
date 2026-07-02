import os
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app.database.db import AsyncSessionLocal
from app.repositories.repos import ExerciseRepo, GalleryRepo, ServiceRepo

router = Router()
logger = logging.getLogger(__name__)

def is_admin(telegram_id: int) -> bool:
    ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    return telegram_id in ids

class AddExercise(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_video = State()

class AddPhoto(StatesGroup):
    waiting_photo = State()
    waiting_caption = State()

class SetPrice(StatesGroup):
    waiting_service = State()
    waiting_price = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔧 <b>Панель администратора</b>\n\n/add_exercise — добавить упражнение\n/list_exercises — список упражнений\n/add_photo — добавить фото в галерею\n/set_price — установить цену на услугу")

@router.message(Command("add_exercise"))
async def cmd_add_exercise(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddExercise.waiting_name)
    await message.answer("📝 Введи название упражнения:")

@router.message(AddExercise.waiting_name)
async def add_exercise_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddExercise.waiting_description)
    await message.answer("📝 Введи описание упражнения:")

@router.message(AddExercise.waiting_description)
async def add_exercise_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AddExercise.waiting_video)
    await message.answer("🎥 Отправь видео упражнения (или напиши пропустить):")

@router.message(AddExercise.waiting_video)
async def add_exercise_video(message: Message, state: FSMContext):
    data = await state.get_data()
    video_file_id = None
    if message.video:
        video_file_id = message.video.file_id
    elif message.text and message.text.lower() in ("пропустить", "skip", "-"):
        video_file_id = None
    else:
        await message.answer("Отправь видео или напиши пропустить")
        return
    async with AsyncSessionLocal() as session:
        ex = await ExerciseRepo(session).create(name=data["name"], description=data["description"], video_file_id=video_file_id)
    await state.clear()
    await message.answer(f"✅ Упражнение {ex.name} добавлено!")

@router.message(Command("list_exercises"))
async def cmd_list_exercises(message: Message):
    if not is_admin(message.from_user.id):
        return
    async with AsyncSessionLocal() as session:
        exercises = await ExerciseRepo(session).get_all()
    if not exercises:
        await message.answer("Упражнений пока нет. Добавь через /add_exercise")
        return
    lines = [f"{i+1}. [{ex.id}] {ex.name}" for i, ex in enumerate(exercises)]
    await message.answer("📋 <b>Список упражнений:</b>\n\n" + "\n".join(lines) + "\n\nУдалить: /del_exercise {id}")

@router.message(Command("del_exercise"))
async def cmd_del_exercise(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /del_exercise {id}")
        return
    async with AsyncSessionLocal() as session:
        await ExerciseRepo(session).delete(int(parts[1]))
    await message.answer(f"✅ Упражнение {parts[1]} удалено.")

@router.message(Command("add_photo"))
async def cmd_add_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddPhoto.waiting_photo)
    await message.answer("📸 Отправь фото для галереи:")

@router.message(AddPhoto.waiting_photo, F.photo)
async def add_photo_file(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(file_id=file_id)
    await state.set_state(AddPhoto.waiting_caption)
    await message.answer("📝 Введи подпись к фото (или напиши пропустить):")

@router.message(AddPhoto.waiting_caption)
async def add_photo_caption(message: Message, state: FSMContext):
    data = await state.get_data()
    caption = "" if message.text.lower() in ("пропустить", "skip", "-") else message.text.strip()
    async with AsyncSessionLocal() as session:
        await GalleryRepo(session).add_photo(data["file_id"], caption)
    await state.clear()
    await message.answer("✅ Фото добавлено в галерею!")

@router.message(Command("set_price"))
async def cmd_set_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(SetPrice.waiting_service)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗣 Консультация", callback_data="setprice:consultation")],
        [InlineKeyboardButton(text="📋 Программа", callback_data="setprice:program")],
        [InlineKeyboardButton(text="🥗 Диета", callback_data="setprice:diet")],
        [InlineKeyboardButton(text="🧪 Анализы", callback_data="setprice:analyses")],
        [InlineKeyboardButton(text="💊 Курс стероидов", callback_data="setprice:steroids")],
    ])
    await message.answer("Выбери услугу:", reply_markup=kb)

@router.callback_query(F.data.startswith("setprice:"), SetPrice.waiting_service)
async def set_price_service(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[1]
    await state.update_data(service_key=key)
    await state.set_state(SetPrice.waiting_price)
    await call.message.edit_text(f"Введи новую цену в USDT для {key}:")

@router.message(SetPrice.waiting_price)
async def set_price_value(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Введи число, например: 25")
        return
    data = await state.get_data()
    key = data["service_key"]
    names = {"consultation": "Консультация", "program": "Программа тренировок", "diet": "Диета", "analyses": "Анализы", "steroids": "Курс стероидов"}
    async with AsyncSessionLocal() as session:
        await ServiceRepo(session).upsert(key=key, name=names.get(key, key), description="", price_usd=price)
    await state.clear()
    await message.answer(f"✅ Цена на {key} установлена: {price} USDT")

@router.message(F.photo)
async def get_photo_id(message: Message):
    if not is_admin(message.from_user.id):
        return
    file_id = message.photo[-1].file_id
    await message.answer(f"file_id фото:\n<code>{file_id}</code>")

@router.message(F.video)
async def get_video_id(message: Message):
    if not is_admin(message.from_user.id):
        return
    file_id = message.video.file_id
    await message.answer(f"file_id видео:\n<code>{file_id}</code>")
