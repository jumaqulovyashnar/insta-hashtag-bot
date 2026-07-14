from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# Button label constants with custom visual padding spaces
BTN_SEND_LINK = "  🔗 Havola yuborish  "
BTN_REFERRAL = "  👥 Taklif havolasi  "
BTN_GUIDE = "  📚 Qo'llanma  "
BTN_SUPPORT = "  ☎️ Qo'llab-quvvatlash  "

def get_subscribe_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """
    Build subscribe inline keyboard.
    Accepts list of channel dictionaries (with channel_id and channel_link).
    """
    buttons = []

    for channel in channels:
        buttons.append([
            InlineKeyboardButton(
                text="📢 Kanalga o'tish",
                url=channel['channel_link'],
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="✅ Obuna bo'ldim",
            callback_data="check_subscription",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Build the persistent main menu reply keyboard at the bottom of the chat.
    Displays buttons side-by-side (flex alignment) with a user icon for the invite link.
    """
    keyboard = [
        [
            KeyboardButton(text=BTN_SEND_LINK),
            KeyboardButton(text=BTN_REFERRAL),
        ],
        [
            KeyboardButton(text=BTN_GUIDE),
            KeyboardButton(text=BTN_SUPPORT)
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Quyidagi menyudan birini tanlang..."
    )
