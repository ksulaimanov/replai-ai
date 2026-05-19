import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from services.llm_service import get_ai_response

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BOT_ID = "telegram_default"


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer("Привет! Я Алина, менеджер по продажам. Чем могу помочь? 😊")


@dp.message()
async def handle_message(message: types.Message):
    chat_id = str(message.chat.id)
    text = message.text or ""

    reply = get_ai_response(BOT_ID, chat_id, text)

    parts = [p.strip() for p in reply.split("|||") if p.strip()]

    for i, part in enumerate(parts):
        await message.answer(part)
        if i < len(parts) - 1:
            await asyncio.sleep(1)


async def start_polling():
    await dp.start_polling(bot)
