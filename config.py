import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int]
    spreadsheet_id: str
    worksheet_name: str
    google_credentials_file: str
    update_interval_seconds: int
    backup_file: str = "data/movies_backup.json"
    update_cooldown_seconds: int = 30


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("Не задан BOT_TOKEN в файле .env")

    raw_admins = os.getenv("ADMIN_IDS", "")
    admin_ids = []
    for item in raw_admins.split(","):
        item = item.strip()
        if item.isdigit():
            admin_ids.append(int(item))

    spreadsheet_id = os.getenv("SPREADSHEET_ID", "").strip()
    worksheet_name = os.getenv("WORKSHEET_NAME", "Movies").strip() or "Movies"
    google_credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json").strip()

    try:
        update_interval = int(os.getenv("UPDATE_INTERVAL_SECONDS", "600"))
    except ValueError:
        update_interval = 600

    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name,
        google_credentials_file=google_credentials_file,
        update_interval_seconds=max(60, update_interval),
    )
