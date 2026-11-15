import random
from dataclasses import dataclass
from services.movie_loader import Movie

VIBE_LABELS = {
    "inspire": "Вдохновиться",
    "amaze": "Удивиться",
    "imagine": "Пофантазировать",
    "fun": "Поржать",
    "sad": "Погрустить",
    "think": "Подумать",
    "feel": "Почувствовать",
    "scary": "Испугаться",
    "surprise": "Удиви меня",
}

DURATION_LABELS = {
    "short": "Короткий (до 2 часов)",
    "long": "Длинный (от 2 часов)",
    "any": "Неважно",
}

CONTEXT_LABELS = {
    "food": "Под еду",
    "background": "На фоне",
    "relax": "Расслабиться",
    "company": "В компании",
    "focus": "Погрузиться",
    "any": "Без разницы",
}


@dataclass
class RecommendedMovie:
    movie: Movie
    score: int
    is_exact: bool


def get_recommendations(
    movies: list[Movie],
    vibe: str,
    duration: str,
    watch_context: str,
    shown_ids: set[str],
    limit: int = 1,
) -> list[RecommendedMovie]:
    """
    Подбирает до `limit` фильмов:
    - Если выбрано 'surprise' (Удиви меня): случайный активный фильм из непоказанных.
    - Иначе балльная система:
      * Вайб: +5 баллов
      * Хронометраж: +4 балла (если выбрано 'any', не учитывается)
      * Сценарий просмотра: +3 балла (если выбрано 'any', не учитывается)
    """
    available = [m for m in movies if m.is_active and m.id not in shown_ids]
    if not available:
        return []

    if vibe == "surprise":
        chosen = random.sample(available, k=min(limit, len(available)))
        return [
            RecommendedMovie(movie=m, score=12, is_exact=True)
            for m in chosen
        ]

    exact_matches: list[RecommendedMovie] = []
    partial_matches: list[RecommendedMovie] = []

    for movie in available:
        score = 0
        is_exact = True

        if movie.vibe == vibe:
            score += 5
        else:
            is_exact = False

        if duration != "any":
            if movie.duration_category == duration:
                score += 4
            else:
                is_exact = False

        if watch_context != "any":
            if movie.watch_context == watch_context:
                score += 3
            else:
                is_exact = False

        if score == 0:
            continue

        item = RecommendedMovie(
            movie=movie,
            score=score,
            is_exact=is_exact,
        )

        if is_exact:
            exact_matches.append(item)
        else:
            partial_matches.append(item)

    random.shuffle(exact_matches)
    random.shuffle(partial_matches)
    partial_matches.sort(key=lambda x: x.score, reverse=True)

    combined = exact_matches + partial_matches
    return combined[:limit]
