import html
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions

from config import Config
from keyboards.selection import (
    get_vibe_keyboard,
    get_recommendations_keyboard,
    get_empty_recommendations_keyboard,
)
from services.analytics import log_event
from services.cache import MovieCache
from services.recommendation import get_recommendations, RecommendedMovie

router = Router()

# Защита от двойных нажатий одним пользователем
_processing_users: set[int] = set()


def format_movie_card(item: RecommendedMovie) -> str:
    m = item.movie
    title = html.escape(m.title)
    desc = html.escape(m.description)

    hours = m.duration_min // 60
    mins = m.duration_min % 60
    if hours > 0 and mins > 0:
        duration_str = f"{hours} ч {mins} мин"
    elif hours > 0:
        duration_str = f"{hours} ч"
    else:
        duration_str = f"{mins} мин"

    # Невидимая ссылка встраивает крупный постер внутри текстового сообщения, если poster_url заполнен
    invisible_poster = f'<a href="{html.escape(m.poster_url)}">&#8203;</a>' if m.poster_url else ""

    lines = [f"{invisible_poster}<b>{title} ({m.year})</b>", ""]
    lines.append(f"⏱ {duration_str}")
    if m.genre:
        lines.append(f"🎭 {html.escape(m.genre)}")
    lines.append("")
    lines.append(f"<blockquote>{desc}</blockquote>")

    return "\n".join(lines)


async def show_recommendations_step(
    callback: types.CallbackQuery,
    state: FSMContext,
    cache: MovieCache,
    config: Config,
    is_more: bool = False,
) -> None:
    user_id = callback.from_user.id
    if user_id in _processing_users:
        await callback.answer()
        return

    _processing_users.add(user_id)
    try:
        data = await state.get_data()
        vibe = data.get("vibe")
        duration = data.get("duration")
        watch_context = data.get("watch_context")
        is_surprise = vibe == "surprise"

        if not (vibe and duration and watch_context):
            await callback.answer("Подбор устарел. Нажмите /start, чтобы начать заново.", show_alert=True)
            return

        shown_ids: set[str] = set(data.get("shown_ids", []))
        recommendations = get_recommendations(
            movies=cache.active_movies,
            vibe=vibe,
            duration=duration,
            watch_context=watch_context,
            shown_ids=shown_ids,
            limit=1,
        )

        if not recommendations:
            if is_more:
                text = (
                    "🎬 Подходящие фильмы по этим параметрам закончились.\n\n"
                    "Попробуй изменить ответы или начни подбор заново!"
                )
            else:
                text = (
                    "😔 По выбранным параметрам пока не нашлось подходящих фильмов.\n\n"
                    "Попробуй изменить ответы или начни подбор заново!"
                )
            await callback.message.edit_text(
                text,
                reply_markup=get_empty_recommendations_keyboard(is_surprise=is_surprise),
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
            await callback.answer()
            return

        item = recommendations[0]
        new_shown_ids = shown_ids | {item.movie.id}
        await state.update_data(shown_ids=list(new_shown_ids))

        response_text = format_movie_card(item)
        poster_url = item.movie.poster_url

        preview_options = (
            LinkPreviewOptions(
                url=poster_url,
                prefer_large_media=True,
                show_above_text=False,
            )
            if poster_url
            else LinkPreviewOptions(is_disabled=True)
        )

        try:
            await callback.message.edit_text(
                response_text,
                reply_markup=get_recommendations_keyboard(is_surprise=is_surprise),
                parse_mode="HTML",
                link_preview_options=preview_options,
            )
        except Exception:
            await callback.message.edit_text(
                response_text,
                reply_markup=get_recommendations_keyboard(is_surprise=is_surprise),
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )

        event_name = "reroll" if is_more else "recommend"
        await log_event(
            config=config,
            user_id=user_id,
            username=callback.from_user.username,
            event=event_name,
            vibe=vibe,
            duration=duration,
            movie_title=item.movie.title,
        )
        await callback.answer()
    finally:
        _processing_users.discard(user_id)


@router.callback_query(F.data == "rec:more")
async def process_more_recommendations(
    callback: types.CallbackQuery,
    state: FSMContext,
    cache: MovieCache,
    config: Config,
) -> None:
    await show_recommendations_step(callback, state, cache, config, is_more=True)


@router.callback_query(F.data == "rec:restart")
async def process_restart(callback: types.CallbackQuery, state: FSMContext) -> None:
    from handlers.selection import SelectionStates, VIBE_STEP_TEXT

    await state.clear()
    await state.set_state(SelectionStates.choosing_vibe)
    await callback.message.edit_text(
        VIBE_STEP_TEXT,
        reply_markup=get_vibe_keyboard(),
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    await callback.answer()
