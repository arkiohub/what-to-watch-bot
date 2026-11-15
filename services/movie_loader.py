import logging
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "id",
    "title",
    "year",
    "duration_min",
    "vibe",
    "watch_context",
    "description",
    "is_active",
}

VALID_VIBES = {"inspire", "amaze", "imagine", "fun", "sad", "think", "feel", "scary"}
VALID_CONTEXTS = {"food", "background", "relax", "company", "focus"}


class Movie(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    year: int = Field(..., ge=1888, le=2100)
    duration_min: int = Field(..., ge=1, le=400)
    vibe: Literal["inspire", "amaze", "imagine", "fun", "sad", "think", "feel", "scary"]
    watch_context: Literal["food", "background", "relax", "company", "focus"]
    genre: str = ""
    description: str = Field(..., min_length=1)
    hook: str = ""
    poster_url: Optional[str] = None
    watch_url: Optional[str] = None
    age_rating: str = ""
    is_active: bool = True

    @property
    def duration_category(self) -> str:
        return "short" if self.duration_min < 120 else "long"

    @field_validator("vibe", mode="before")
    @classmethod
    def normalize_vibe(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("watch_context", mode="before")
    @classmethod
    def normalize_context(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("is_active", mode="before")
    @classmethod
    def parse_is_active(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            val = v.strip().upper()
            if val in {"TRUE", "1", "YES", "ДА", "+"}:
                return True
            if val in {"FALSE", "0", "NO", "НЕТ", "-"}:
                return False
        raise ValueError(f"Некорректное значение is_active: {v!r}")

    @field_validator("poster_url", "watch_url", mode="before")
    @classmethod
    def validate_optional_url(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        if s.startswith(("http://", "https://")) and "." in s:
            return s
        logger.warning("Некорректная ссылка в таблице пропущена: %s", s)
        return None


def parse_and_validate_rows(rows: list[dict]) -> list[Movie]:
    if not rows:
        raise ValueError("Таблица пуста или не содержит строк с данными.")

    headers = {str(k).strip() for k in rows[0].keys()}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"В таблице отсутствуют обязательные столбцы: {', '.join(sorted(missing))}")

    valid_movies: list[Movie] = []
    seen_ids: set[str] = set()

    for idx, raw_row in enumerate(rows, start=2):
        cleaned = {str(k).strip(): (str(v).strip() if v is not None else "") for k, v in raw_row.items()}

        if not any(cleaned.values()):
            continue

        try:
            movie = Movie(**cleaned)
            if movie.id in seen_ids:
                logger.warning("Строка %d: дубликат id '%s', строка пропущена.", idx, movie.id)
                continue
            seen_ids.add(movie.id)
            valid_movies.append(movie)
        except Exception as exc:
            logger.warning("Строка %d пропущена из-за ошибки валидации: %s", idx, exc)

    active_count = sum(1 for m in valid_movies if m.is_active)
    if active_count == 0:
        raise ValueError("После проверки в таблице не осталось ни одного корректного активного фильма.")

    return valid_movies
