import logging, sqlite3, time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ====== SOZLAMALAR ======
API_TOKEN = "8594052857:AAHpfMGhVnq56g2a-QlgWOWID5NvsfIDU8E"          # BotFather token
ADMIN_ID = 5662756526            # Admin ID
CHANNEL = "@uzkinoos"          # Majburiy obuna kanali
POST_CHANNEL = "@uzkinoos"     # Auto-post kanali
PROTECT_CONTENT = film

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ====== DATABASE ======
db = sqlite3.connect("kino.db", check_same_thread=False)
sql = db.cursor()

# Users table
sql.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
vip_until INTEGER DEFAULT 0,
favorites TEXT DEFAULT ''
)""")

# Movies table
sql.execute("""CREATE TABLE IF NOT EXISTS movies(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
code TEXT UNIQUE,
file_id TEXT,
views INTEGER DEFAULT 0,
vip INTEGER DEFAULT 0
)""")

# Series table
sql.execute("""CREATE TABLE IF NOT EXISTS series(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)""")

# Episodes table
sql.execute("""CREATE TABLE IF NOT EXISTS episodes(
id INTEGER PRIMARY KEY AUTOINCREMENT,
series_id INTEGER,
title TEXT,
file_id TEXT
)""")
db.commit()

# ====== MENYULAR ======
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔎 Qidiruv", callback_data="search"),
        InlineKeyboardButton("🔥 Top 10", callback_data="top"),
        InlineKeyboardButton("📺 Seriallar", callback_data="series"),
        InlineKeyboardButton("❤️ Sevimlilar", callback_data="fav")
    )
    return kb

def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Kino", callback_data="add_movie"),
        InlineKeyboardButton("➕ Serial", callback_data="add_series"),
        InlineKeyboardButton("➕ Qism", callback_data="add_episode"),
        InlineKeyboardButton("⭐ VIP", callback_data="vip"),
        InlineKeyboardButton("📢 Auto-post", callback_data="autopost"),
        InlineKeyboardButton("📊 Statistika", callback_data="stats"),
        InlineKeyboardButton("⬅️ Chiqish", callback_data="exit")
    )
    return kb

# ====== UTILS ======
async def check_sub(uid):
    try:
        m = await bot.get_chat_member(CHANNEL, uid)
        return m.status != "left"
    except:
        return False

def is_vip(uid):
    r = sql.execute("SELECT vip_until FROM users WHERE id=?",(uid,)).fetchone()
    return r and r[0] > int(time.time())

# ====== START ======
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    sql.execute("INSERT OR IGNORE INTO users(id) VALUES(?)",(m.from_user.id,))
    db.commit()
    if not await check_sub(m.from_user.id):
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 Obuna", url=f"https://t.me/{CHANNEL[1:]}"),
            InlineKeyboardButton("✅ Tekshirish", callback_data="check")
        )
        return await m.answer("❗ Avval kanalga obuna bo‘ling", reply_markup=kb)
    await m.answer("🎬 ULTRA PRO KINO BOT", reply_markup=main_menu())

@dp.callback_query_handler(text="check")
async def recheck(c: types.CallbackQuery):
    if await check_sub(c.from_user.id):
        await c.message.edit_text("✅ Tayyor", reply_markup=main_menu())
    else:
        await c.answer("❌ Obuna yo‘q", show_alert=True)

# ====== QIDIRUV ======
@dp.message_handler(lambda m: m.text and m.text.isdigit())
async def by_code(m: types.Message):
    r = sql.execute("SELECT file_id,name,vip FROM movies WHERE code=?",(m.text,)).fetchone()
    if not r: return await m.answer("❌ Topilmadi")
    if r[2]==1 and not is_vip(m.from_user.id):
        return await m.answer("🔒 VIP kino")
    sql.execute("UPDATE movies SET views=views+1 WHERE code=?",(m.text,))
    db.commit()
    await m.answer_video(r[0], caption=f"🎬 {r[1]}", protect_content=PROTECT_CONTENT)

@dp.callback_query_handler(text="search")
async def ask(c: types.CallbackQuery):
    await c.message.answer("🔎 Kino nomini yozing:")

@dp.message_handler(lambda m: m.text and not m.text.isdigit())
async def search(m: types.Message):
    rows = sql.execute("SELECT name,code FROM movies WHERE name LIKE ? LIMIT 10",(f"%{m.text}%",)).fetchall()
    if rows:
        await m.answer("🔎 Natija:\n"+"\n".join([f"{n} — `{c}`" for n,c in rows]), parse_mode="Markdown")

# ====== TOP 10 ======
@dp.callback_query_handler(text="top")
async def top(c: types.CallbackQuery):
    rows = sql.execute("SELECT name,code,views FROM movies ORDER BY views DESC LIMIT 10").fetchall()
    await c.message.answer("🔥 Top 10:\n"+"\n".join([f"{i+1}. {n} ({v}) — `{c}`" for i,(n,c,v) in enumerate(rows)]), parse_mode="Markdown")

# ====== SERIAL ======
@dp.callback_query_handler(text="series")
async def series_list(c: types.CallbackQuery):
    rows = sql.execute("SELECT id,name FROM series").fetchall()
    if not rows: return await c.message.answer("📺 Serial yo‘q")
    kb = InlineKeyboardMarkup()
    for i,n in rows:
        kb.add(InlineKeyboardButton(n, callback_data=f"s_{i}"))
    await c.message.answer("📺 Seriallar:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("s_"))
async def episodes(c: types.CallbackQuery):
    sid = int(c.data.split("_")[1])
    rows = sql.execute("SELECT title,file_id FROM episodes WHERE series_id=?",(sid,)).fetchall()
    for t,f in rows:
        await c.message.answer_video(f, caption=t, protect_content=PROTECT_CONTENT)

# ====== ADMIN ======
@dp.message_handler(commands=["admin"])
async def admin(m: types.Message):
    if m.from_user.id==ADMIN_ID:
        await m.answer("🧑‍💼 ADMIN PANEL", reply_markup=admin_menu())

@dp.callback_query_handler(text="exit")
async def exit_admin(c: types.CallbackQuery):
    await c.message.edit_text("🎬 KINO BOT", reply_markup=main_menu())

# Admin funksiyalar: add_movie, add_series, add_episode, vip, autopost, stats
# Siz kodni shunga moslab davom ettirishingiz mumkin

# ====== RUN ======
if __name__=="__main__":
    executor.start_polling(dp, skip_updates=True)
