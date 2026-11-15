from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions

from keyboards.main import get_start_keyboard

router = Router()

START_TEXT = (
    "Привет! 🍿 Давай найдём фильм под твоё настроение. "
    "Ответь на три коротких вопроса — и я предложу подходящий вариант"
)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        START_TEXT,
        reply_markup=get_start_keyboard(),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
