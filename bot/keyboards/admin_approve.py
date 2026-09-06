from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_approve_keyboard(telegram_id: int, group_id: int) -> InlineKeyboardMarkup:
    # callback_data формата: "action_teleid_groupid"
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Принять", 
                callback_data=f"adm_app_{telegram_id}_{group_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить", 
                callback_data=f"adm_rej_{telegram_id}_{group_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)