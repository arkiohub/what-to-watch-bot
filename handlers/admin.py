import time
from aiogram import Router, types
from aiogram.filters import Command

from config import Config
from services.cache import MovieCache

router = Router()

_last_manual_update: float = 0.0


def is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids


@router.message(Command("update"))
async def cmd_update(message: types.Message, config: Config, cache: MovieCache) -> None:
    global _last_manual_update

    if not message.from_user or not is_admin(message.from_user.id, config):
        await message.answer("⛔ У вас нет прав для выполнения этой команды.")
        return

    now = time.monotonic()
    elapsed = now - _last_manual_update
    if elapsed < config.update_cooldown_seconds:
        wait_sec = int(config.update_cooldown_seconds - elapsed) + 1
        await message.answer(f"⏳ Слишком частые запросы. Попробуйте снова через {wait_sec} сек.")
        return

    _last_manual_update = now
    success, _ = await cache.refresh()

    if success:
        total = len(cache.all_movies)
        active = len(cache.active_movies)
        updated_str = cache.last_updated.strftime("%H:%M") if cache.last_updated else "--:--"
        text = (
            "✅ База фильмов успешно обновлена!\n\n"
            f"Загружено фильмов: {total}\n"
            f"Активных фильмов: {active}\n"
            f"Время обновления: {updated_str}"
        )
        await message.answer(text)
    else:
        text = (
            "⚠️ Не удалось обновить базу.\n\n"
            "Продолжаю работать на последней успешно загруженной версии"
        )
        await message.answer(text)


@router.message(Command("stats"))
async def cmd_stats(message: types.Message, config: Config, cache: MovieCache) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        await message.answer("⛔ У вас нет прав для выполнения этой команды.")
        return

    total = len(cache.all_movies)
    active = len(cache.active_movies)
    updated_str = cache.last_updated.strftime("%d.%m.%Y %H:%M") if cache.last_updated else "неизвестно"

    text = (
        "📊 <b>Статистика базы фильмов</b>\n\n"
        f"Всего строк загружено: <b>{total}</b>\n"
        f"Активных фильмов (is_active=TRUE): <b>{active}</b>\n"
        f"Источник: <b>{cache.source}</b>\n"
        f"Последнее обновление: <b>{updated_str}</b>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: types.Message, config: Config) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        await message.answer(
            "🎬 Чтобы подобрать фильм под настроение, нажмите /start"
        )
        return

    text = (
        "🛠 <b>Команды администратора</b>\n\n"
        "/update — принудительно обновить базу фильмов из Google Таблицы\n"
        "/stats — показать статистику загруженной базы\n"
        "/help — показать эту справку\n"
        "/start — запустить пользовательский сценарий подбора"
    )
    await message.answer(text, parse_mode="HTML")
