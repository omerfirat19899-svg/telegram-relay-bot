import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Kullanıcıdan gelen mesajı admin'e ilet
@dp.message_handler(lambda message: message.from_user.id != ADMIN_ID)
async def forward_to_admin(message: Message):
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

# Admin reply yaparsa kullanıcıya geri gönder
@dp.message_handler(lambda message: message.from_user.id == ADMIN_ID and message.reply_to_message)
async def reply_to_user(message: Message):
    original = message.reply_to_message
    if original.forward_from:
        user_id = original.forward_from.id
        await bot.send_message(user_id, message.text)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
