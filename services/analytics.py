import asyncio
import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone, timedelta
import gspread
from google.oauth2.service_account import Credentials
from config import Config

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_stats_worksheet(config: Config):
    creds_json = (
        getattr(config, "google_credentials_json", "")
        or os.getenv("GOOGLE_CREDENTIALS_JSON", "")
        or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    ).strip()

    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            config.google_credentials_file, scopes=SCOPES
        )

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(config.spreadsheet_id)
    return sh.worksheet("Stats")


def _append_row_sync(config: Config, row: list) -> None:
    try:
        ws = _get_stats_worksheet(config)
        ws.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.warning(f"Не удалось записать событие в Stats: {e}")


async def log_event(
    config: Config,
    user_id: int,
    username: str | None,
    event: str,
    vibe: str = "",
    duration: str = "",
    movie_title: str = "",
) -> None:
    now_str = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M:%S")
    uname = f"@{username}" if username else ""
    row = [now_str, str(user_id), uname, event, vibe, duration, movie_title]
    asyncio.create_task(asyncio.to_thread(_append_row_sync, config, row))


def _fetch_all_stats_sync(config: Config) -> list[dict]:
    ws = _get_stats_worksheet(config)
    return ws.get_all_records()


async def build_stats_report(config: Config) -> str:
    try:
        records = await asyncio.to_thread(_fetch_all_stats_sync, config)
    except Exception as e:
        return f"⚠️ Ошибка чтения листа Stats: {e}"

    if not records:
        return "📊 Пока нет данных в листе <b>Stats</b>. Сделай пару подборов в боте и проверь снова!"

    users = {str(r.get("user_id")) for r in records if r.get("user_id")}
    starts = sum(1 for r in records if r.get("event") == "start")
    recs = sum(1 for r in records if r.get("event") == "recommend")
    rerolls = sum(1 for r in records if r.get("event") == "reroll")

    vibe_counts = Counter(
        r.get("vibe") for r in records if r.get("vibe") and r.get("event") in {"recommend", "reroll"}
    )
    top_vibes = "\n".join(f"  • {v}: {cnt}" for v, cnt in vibe_counts.most_common(5)) or "  • пока нет"

    movie_counts = Counter(
        r.get("movie_title") for r in records if r.get("movie_title")
    )
    top_movies = "\n".join(f"  • {m} ({cnt})" for m, cnt in movie_counts.most_common(5)) or "  • пока нет"

    return (
        "📊 <b>Статистика пользователей</b>\n\n"
        f"👤 Уникальных пользователей: <b>{len(users)}</b>\n"
        f"🚀 Запусков (/start): <b>{starts}</b>\n"
        f"🎬 Выдано подборок: <b>{recs}</b>\n"
        f"🔄 Нажатий «Ещё вариант»: <b>{rerolls}</b>\n\n"
        f"🔥 <b>Топ вайбов:</b>\n{top_vibes}\n\n"
        f"🏆 <b>Чаще всего выпадали:</b>\n{top_movies}"
    )
