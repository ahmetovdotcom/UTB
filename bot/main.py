import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from handlers import schedule, admin, start


logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()


    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(schedule.router)

    logging.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())