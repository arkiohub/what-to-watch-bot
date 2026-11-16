from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import LinkPreviewOptions

from config import Config
from keyboards.main import get_start_keyboard
from services.analytics import log_event

router = Router()

START_TEXT = (
    "🍿 Давай найдем фильм под твоё настроение. "
    "Ответь на три коротких вопроса – я предложу подходящий вариант."
)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, config: Config) -> None:
    await state.clear()
    await message.answer(
        START_TEXT,
        reply_markup=get_start_keyboard(),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    if message.from_user:
        await log_event(config, message.from_user.id, message.from_user.username, "start")
