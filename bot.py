import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config, Config
from services.google_sheets import GoogleSheetsClient
from services.cache import MovieCache
from handlers import start, selection, recommendations, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def periodic_cache_updater(bot: Bot, cache: MovieCache, config: Config) -> None:
    notified_failure = False
    while True:
        await asyncio.sleep(config.update_interval_seconds)
        success, error_msg = await cache.refresh()
        if success:
            notified_failure = False
        elif cache.consecutive_failures >= 3 and not notified_failure:
            notified_failure = True
            alert = (
                "⚠️ <b>Внимание!</b> Автоматическое обновление базы фильмов из Google Таблицы "
                f"завершилось ошибкой {cache.consecutive_failures} раза подряд.\n"
                "Бот продолжает работать на предыдущей версии базы."
            )
            for admin_id in config.admin_ids:
                try:
                    await bot.send_message(admin_id, alert, parse_mode="HTML")
                except Exception as exc:
                    logger.warning("Не удалось отправить уведомление админу %s: %s", admin_id, exc)


async def main() -> None:
    config = load_config()

    sheets_client = GoogleSheetsClient(
        credentials_file=config.google_credentials_file,
        spreadsheet_id=config.spreadsheet_id,
        worksheet_name=config.worksheet_name,
    )
    cache = MovieCache(sheets_client=sheets_client, backup_file=config.backup_file)

    await cache.initialize()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp["config"] = config
    dp["cache"] = cache

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(selection.router)
    dp.include_router(recommendations.router)

    updater_task = asyncio.create_task(periodic_cache_updater(bot, cache, config))

    logger.info("Бот «Что посмотреть?» успешно запущен!")
    try:
        await dp.start_polling(bot)
    finally:
        updater_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
