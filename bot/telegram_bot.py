# Dev-only test script. Run manually: python bot/telegram_bot.py
# Never imported by the server. Not for production use.

import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from services.llm_service import get_ai_response

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Set TEST_BOT_ID in .env to test a specific bot's knowledge base
BOT_ID = os.getenv("TEST_BOT_ID", "test")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(f"[DEV] bot_id={BOT_ID}\nПривет! Я Алина, менеджер по продажам. Чем могу помочь? 😊")


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


if __name__ == "__main__":
    print(f"[DEV] Starting test bot with bot_id='{BOT_ID}'")
    asyncio.run(dp.start_polling(bot))
