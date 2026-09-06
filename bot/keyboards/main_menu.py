from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_starosta_main_menu() -> ReplyKeyboardMarkup:
    """Главная клавиатура старосты, которая видна всегда."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Изменить расписание")
            ]
            # Сюда можно будет добавить другие кнопки (например, "📋 Моя группа")
        ],
        resize_keyboard=True,  # Делает кнопки аккуратного размера
        persistent=True        # Кнопка остается на экране постоянно
    )
    return keyboard