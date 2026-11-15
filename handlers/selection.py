from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LinkPreviewOptions

from keyboards.selection import (
    get_vibe_keyboard,
    get_duration_keyboard,
    get_context_keyboard,
)
from services.cache import MovieCache
from handlers.recommendations import show_recommendations_step

router = Router()


class SelectionStates(StatesGroup):
    choosing_vibe = State()
    choosing_duration = State()
    choosing_context = State()
    viewing_results = State()


VIBE_STEP_TEXT = "<b>Шаг 1 из 3</b>\n\nКакой у тебя сейчас вайб?"
DURATION_STEP_TEXT = "<b>Шаг 2 из 3</b>\n\nКакой длины хочешь фильм?"
CONTEXT_STEP_TEXT = "<b>Шаг 3 из 3</b>\n\nКак будешь смотреть?"


@router.callback_query(F.data == "start_selection")
async def start_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SelectionStates.choosing_vibe)
    await callback.message.edit_text(
        VIBE_STEP_TEXT,
        reply_markup=get_vibe_keyboard(),
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vibe:"))
async def process_vibe(callback: types.CallbackQuery, state: FSMContext, cache: MovieCache) -> None:
    current_state = await state.get_state()
    if current_state not in {SelectionStates.choosing_vibe.state, SelectionStates.choosing_duration.state}:
        await callback.answer("Подбор устарел. Нажмите /start, чтобы начать заново.", show_alert=True)
        return

    vibe = callback.data.split(":", 1)[1]

    if vibe == "surprise":
        await state.update_data(vibe="surprise", duration="any", watch_context="any", shown_ids=[])
        await state.set_state(SelectionStates.viewing_results)
        await show_recommendations_step(callback, state, cache, is_more=False)
        return

    await state.update_data(vibe=vibe)
    await state.set_state(SelectionStates.choosing_duration)
    await callback.message.edit_text(
        DURATION_STEP_TEXT,
        reply_markup=get_duration_keyboard(),
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dur:"))
async def process_duration(callback: types.CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    data = await state.get_data()
    if current_state not in {SelectionStates.choosing_duration.state, SelectionStates.choosing_context.state} or "vibe" not in data:
        await callback.answer("Подбор устарел. Нажмите /start, чтобы начать заново.", show_alert=True)
        return

    duration = callback.data.split(":", 1)[1]
    await state.update_data(duration=duration)
    await state.set_state(SelectionStates.choosing_context)
    await callback.message.edit_text(
        CONTEXT_STEP_TEXT,
        reply_markup=get_context_keyboard(),
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ctx:"))
async def process_context(callback: types.CallbackQuery, state: FSMContext, cache: MovieCache) -> None:
    current_state = await state.get_state()
    data = await state.get_data()
    if current_state != SelectionStates.choosing_context.state or "vibe" not in data or "duration" not in data:
        await callback.answer("Подбор устарел. Нажмите /start, чтобы начать заново.", show_alert=True)
        return

    watch_context = callback.data.split(":", 1)[1]
    await state.update_data(watch_context=watch_context, shown_ids=[])
    await state.set_state(SelectionStates.viewing_results)
    await show_recommendations_step(callback, state, cache, is_more=False)


@router.callback_query(F.data.startswith("back:"))
async def process_back(callback: types.CallbackQuery, state: FSMContext) -> None:
    target = callback.data.split(":", 1)[1]
    data = await state.get_data()

    if target == "vibe":
        await state.set_state(SelectionStates.choosing_vibe)
        await callback.message.edit_text(
            VIBE_STEP_TEXT,
            reply_markup=get_vibe_keyboard(),
            parse_mode="HTML",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    elif target == "duration":
        if "vibe" not in data:
            await callback.answer("Подбор устарел. Нажмите /start, чтобы начать заново.", show_alert=True)
            return
        await state.set_state(SelectionStates.choosing_duration)
        await callback.message.edit_text(
            DURATION_STEP_TEXT,
            reply_markup=get_duration_keyboard(),
            parse_mode="HTML",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    elif target == "context":
        if "vibe" not in data or "duration" not in data:
            await callback.answer("Подбор устарел. Нажмите /start, чтобы начать заново.", show_alert=True)
            return
        await state.set_state(SelectionStates.choosing_context)
        await callback.message.edit_text(
            CONTEXT_STEP_TEXT,
            reply_markup=get_context_keyboard(),
            parse_mode="HTML",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    await callback.answer()
