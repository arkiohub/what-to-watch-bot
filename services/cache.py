import json
import logging
import os
from datetime import datetime
from typing import Optional

from services.google_sheets import GoogleSheetsClient
from services.movie_loader import Movie, parse_and_validate_rows

logger = logging.getLogger(__name__)


class MovieCache:
    def __init__(self, sheets_client: GoogleSheetsClient, backup_file: str):
        self.sheets_client = sheets_client
        self.backup_file = backup_file
        self._movies: list[Movie] = []
        self.last_updated: Optional[datetime] = None
        self.source: str = "Не загружено"
        self.consecutive_failures: int = 0

    @property
    def all_movies(self) -> list[Movie]:
        return self._movies

    @property
    def active_movies(self) -> list[Movie]:
        return [m for m in self._movies if m.is_active]

    def _save_backup(self, movies: list[Movie]) -> None:
        os.makedirs(os.path.dirname(self.backup_file) or ".", exist_ok=True)
        payload = [m.model_dump() for m in movies]
        tmp_path = f"{self.backup_file}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.backup_file)

    def _load_backup(self) -> list[Movie]:
        if not os.path.exists(self.backup_file):
            raise FileNotFoundError(f"Резервная копия не найдена: {self.backup_file}")
        with open(self.backup_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return parse_and_validate_rows(raw_data)

    async def initialize(self) -> None:
        try:
            rows = await self.sheets_client.fetch_rows()
            movies = parse_and_validate_rows(rows)
            self._movies = movies
            self.last_updated = datetime.now()
            self.source = "Google Таблица"
            self.consecutive_failures = 0
            self._save_backup(movies)
            logger.info(
                "База успешно загружена из Google Таблицы: всего %d, активных %d.",
                len(movies),
                len(self.active_movies),
            )
        except Exception as exc:
            logger.warning("Не удалось загрузить данные из Google при запуске (%s). Пробую резервную копию...", exc)
            try:
                movies = self._load_backup()
                self._movies = movies
                self.last_updated = datetime.now()
                self.source = "Резервная копия (movies_backup.json)"
                logger.info(
                    "База восстановлена из резервной копии: всего %d, активных %d.",
                    len(movies),
                    len(self.active_movies),
                )
            except Exception as backup_exc:
                logger.critical("КРИТИЧЕСКАЯ ОШИБКА: ни Google Таблица, ни резервная копия недоступны: %s", backup_exc)
                raise RuntimeError("Не удалось загрузить базу фильмов ни из одного источника.") from backup_exc

    async def refresh(self) -> tuple[bool, str]:
        try:
            rows = await self.sheets_client.fetch_rows()
            movies = parse_and_validate_rows(rows)
            self._movies = movies
            self.last_updated = datetime.now()
            self.source = "Google Таблица"
            self.consecutive_failures = 0
            self._save_backup(movies)
            logger.info(
                "База успешно обновлена: всего %d, активных %d.",
                len(movies),
                len(self.active_movies),
            )
            return True, "OK"
        except Exception as exc:
            self.consecutive_failures += 1
            logger.error("Ошибка обновления базы из Google Таблицы (попытка #%d): %s", self.consecutive_failures, exc)
            return False, str(exc)
