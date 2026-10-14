import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.bot.handlers import router

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
dp.include_router(router)