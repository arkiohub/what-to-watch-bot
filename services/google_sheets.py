import asyncio
import json
import logging
import os
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class GoogleSheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_id: str, worksheet_name: str):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name

    def _fetch_sync(self) -> list[dict]:
        if not self.spreadsheet_id:
            raise RuntimeError("SPREADSHEET_ID не указан в настройках.")

        creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
        if creds_json_str:
            info = json.loads(creds_json_str, strict=False)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"Файл ключей Google не найден: {self.credentials_file}")
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=SCOPES)

        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        worksheet = spreadsheet.worksheet(self.worksheet_name)
        return worksheet.get_all_records(default_blank="")

    async def fetch_rows(self) -> list[dict]:
        return await asyncio.to_thread(self._fetch_sync)
