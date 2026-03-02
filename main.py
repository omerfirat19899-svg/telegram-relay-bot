import os
import sqlite3
import logging
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.info("BOT STARTING...")
logging.info(f"ADMIN_ID loaded: {ADMIN_ID}, BOT_TOKEN present: {bool(BOT_TOKEN)}")

if not BOT_TOKEN or not ADMIN_ID:
    raise RuntimeError("BOT_TOKEN ve/veya ADMIN_ID environment variable eksik.")

DB_PATH = "relay.db"

def db_init():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS relay_map (
            admin_msg_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logging.info("DB initialized.")

def db_put(admin_msg_id: int, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO relay_map (admin_msg_id, user_id) VALUES (?, ?)",
        (admin_msg_id, user_id)
    )
    conn.commit()
    conn.close()
    logging.info(f"Mapped admin_msg_id={admin_msg_id} -> user_id={user_id}")

def db_get(admin_msg_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM relay_map WHERE admin_msg_id = ?", (admin_msg_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WELCOME_TEXT = (
    "👑 isim soyisimden TC KİMLİK İKAMET, aile soy ağacı bilgileri
    👑 Numaradan TC isim soyisim istenilen tüm bilgiler
    👑 Kişiden Tapu Bilgileri (33 il 98 milyon Veri)
👑 Ada Parselden Şahıs Bilgileri (33 il 98 milyon Veri)
👑 Kişiden Güncel ve Geçmiş Adres Bilgileri
👑 Plakadan Şahıs, Numara, Adres, Araç Bilgileri
👑 Kişiden Araç Bilgileri
👑 Kişiden Aynı İkamet Eden Hane Bilgileri
👑 Kişiden Aynı Sokak, Mahalle, Apartman Bilgileri
👑 Kişiden Ehliyet Vesika Bilgileri
👑 Kişiden Detaylı Numara Bilgileri
👑 Numaradan Detaylı Kişi Bilgileri
👑 Kişiden Detaylı Askerlik Durum Bilgileri
👑 Ve burada olmayan +30 özellik (IBAN sorgu, aile vesika sorgu, log çekme vb.)
)"

# 1) Kullanıcı /start -> otomatik cevap + admin'e forward
@dp.message(CommandStart(), F.from_user.id != ADMIN_ID)
async def start_handler(message: Message):
    await message.answer(WELCOME_TEXT)

    forwarded = await bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    db_put(forwarded.message_id, message.from_user.id)

# 2) Kullanıcıdan gelen diğer her şey -> admin'e forward
@dp.message(F.from_user.id != ADMIN_ID)
async def user_to_admin(message: Message):
    forwarded = await bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    db_put(forwarded.message_id, message.from_user.id)

# 3) Admin reply -> kullanıcıya geri gönder
@dp.message((F.from_user.id == ADMIN_ID) & (F.reply_to_message))
async def admin_reply_to_user(message: Message):
    replied_admin_msg_id = message.reply_to_message.message_id
    user_id = db_get(replied_admin_msg_id)

    if not user_id:
        await message.answer("Bu mesaja ait kullanıcı bulunamadı. (Eşleştirme yok)")
        return

    await bot.copy_message(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )

async def main():
    db_init()
    logging.info("Start polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
