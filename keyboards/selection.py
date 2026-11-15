from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_vibe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🤩 Вдохновиться", callback_data="vibe:inspire"),
                InlineKeyboardButton(text="😧 Удивиться", callback_data="vibe:amaze"),
            ],
            [
                InlineKeyboardButton(text="🥸 Пофантазировать", callback_data="vibe:imagine"),
                InlineKeyboardButton(text="😁 Поржать", callback_data="vibe:fun"),
            ],
            [
                InlineKeyboardButton(text="😭 Погрустить", callback_data="vibe:sad"),
                InlineKeyboardButton(text="🤔 Подумать", callback_data="vibe:think"),
            ],
            [
                InlineKeyboardButton(text="🥹 Почувствовать", callback_data="vibe:feel"),
                InlineKeyboardButton(text="🫣 Испугаться", callback_data="vibe:scary"),
            ],
            [
                InlineKeyboardButton(text="🎲 Удиви меня", callback_data="vibe:surprise"),
            ],
        ]
    )


def get_duration_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Короткий (до 2 часов)", callback_data="dur:short")],
            [InlineKeyboardButton(text="🍿 Длинный (от 2 часов)", callback_data="dur:long")],
            [InlineKeyboardButton(text="🎲 Неважно", callback_data="dur:any")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:vibe")],
        ]
    )


def get_context_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍕 Под еду", callback_data="ctx:food"),
                InlineKeyboardButton(text="🎧 На фоне", callback_data="ctx:background"),
            ],
            [
                InlineKeyboardButton(text="🛋 Расслабиться", callback_data="ctx:relax"),
                InlineKeyboardButton(text="👯 В компании", callback_data="ctx:company"),
            ],
            [
                InlineKeyboardButton(text="🎯 Погрузиться", callback_data="ctx:focus"),
                InlineKeyboardButton(text="🎲 Без разницы", callback_data="ctx:any"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back:duration"),
            ],
        ]
    )


def get_recommendations_keyboard(is_surprise: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✨ Ещё вариант", callback_data="rec:more")],
    ]
    if not is_surprise:
        buttons.append([InlineKeyboardButton(text="⬅️ Изменить ответы", callback_data="back:context")])
    buttons.append([InlineKeyboardButton(text="🔄 Начать заново", callback_data="rec:restart")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_empty_recommendations_keyboard(is_surprise: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not is_surprise:
        buttons.append([InlineKeyboardButton(text="⬅️ Изменить ответы", callback_data="back:context")])
    buttons.append([InlineKeyboardButton(text="🔄 Начать заново", callback_data="rec:restart")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
