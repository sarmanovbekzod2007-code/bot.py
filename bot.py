import asyncio
import logging
import sqlite3
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# ================== SOZLAMALAR ==================
BOT_TOKEN = os.getenv("8535096708:AAHSyrXWQJPDmw9BiiL4jqm2s-1vqejH8to") or "BOT_TOKEN_BU_YERGA"
ADMIN_ID = 5662756526

CHANNEL_USERNAME = "@uzkinoos"
CHANNEL_LINK = "https://t.me/uzkinoos"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ================== DATABASE ==================
conn = sqlite3.connect("kino.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    title TEXT,
    file_id TEXT,
    likes INTEGER DEFAULT 0
)
""")

conn.commit()

# ================== FSM ==================
class AddMovie(StatesGroup):
    code = State()
    title = State()
    video = State()

# ================== KEYBOARDS ==================
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Qidiruv"), KeyboardButton(text="🔥 Top 10")],
        [KeyboardButton(text="📺 Seriallar")]
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Kino qo‘shish")],
        [KeyboardButton(text="📊 Statistika")]
    ],
    resize_keyboard=True
)

subscribe_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ]
)

# ================== TEXTS ==================
USER_START_TEXT = (
    "🎬 <b>Uz Kino botga xush kelibsiz!</b>\n\n"
    "🔎 Kino nomi yoki kodi (masalan: <b>125</b>) yuboring\n"
    "🔥 Eng mashhur kinolar\n"
    "📺 Sifatli kontent\n\n"
    "👇 Menyudan foydalaning"
)

ADMIN_START_TEXT = (
    "👑 <b>Admin panel</b>\n\n"
    "🎬 Kino qo‘shish\n"
    "📊 Statistika"
)

# ================== HELPERS ==================
async def check_subscription(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def save_user(user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()

# ================== START ==================
@dp.message(CommandStart())
async def start(message: types.Message):
    save_user(message.from_user.id)

    if not await check_subscription(message.from_user.id):
        await message.answer(
            "❗ Botdan foydalanish uchun kanalga obuna bo‘ling:",
            reply_markup=subscribe_keyboard
        )
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer(ADMIN_START_TEXT, reply_markup=admin_keyboard)
    else:
        await message.answer(USER_START_TEXT, reply_markup=user_keyboard)

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        await start(callback.message)
    else:
        await callback.answer("❌ Hali obuna emassiz", show_alert=True)

# ================== ADMIN: STATISTIKA ==================
@dp.message(F.text == "📊 Statistika")
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM movies")
    movies = cursor.fetchone()[0]

    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{users}</b>\n"
        f"🎬 Kinolar: <b>{movies}</b>"
    )

# ================== ADMIN: KINO QO‘SHISH ==================
@dp.message(F.text == "🎬 Kino qo‘shish")
async def add_movie_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AddMovie.code)
    await message.answer("🎬 Kino kodini yuboring (masalan: 125)")

@dp.message(AddMovie.code)
async def add_movie_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await state.set_state(AddMovie.title)
    await message.answer("🎬 Kino nomini yuboring")

@dp.message(AddMovie.title)
async def add_movie_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovie.video)
    await message.answer("🎥 Endi kino videosini yuboring")

@dp.message(AddMovie.video, F.video)
async def add_movie_video(message: types.Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute(
        "INSERT INTO movies (code, title, file_id) VALUES (?, ?, ?)",
        (data["code"], data["title"], message.video.file_id)
    )
    conn.commit()

    await state.clear()
    await message.answer("✅ Kino muvaffaqiyatli qo‘shildi")

# ================== QIDIRUV (NOM + KOD) ==================
@dp.message()
async def search_movie(message: types.Message):
    text = message.text.strip()

    if text.isdigit():
        cursor.execute(
            "SELECT title, file_id FROM movies WHERE code = ?",
            (text,)
        )
    else:
        cursor.execute(
            "SELECT title, file_id FROM movies WHERE title LIKE ?",
            (f"%{text}%",)
        )

    movie = cursor.fetchone()

    if movie:
        await message.answer_video(
            video=movie[1],
            caption=f"🎬 <b>{movie[0]}</b>",
            protect_content=True
        )
    else:
        await message.answer("❌ Kino topilmadi")

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
