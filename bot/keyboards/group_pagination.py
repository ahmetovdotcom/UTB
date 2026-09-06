from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .callbacks import GroupPagination

ITEMS_PER_PAGE = 5  # Сколько групп показывать на одной странице

def get_groups_keyboard(groups: list, page: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Расчет индексов
    start_offset = (page - 1) * ITEMS_PER_PAGE
    end_offset = start_offset + ITEMS_PER_PAGE
    page_groups = groups[start_offset:end_offset]
    
    # Добавляем кнопки групп
    for group in page_groups:
        builder.row(InlineKeyboardButton(
            text=f"👥 {group['title']}",
            callback_data=GroupPagination(
                page=page, 
                action="select", 
                group_id=group['id']
            ).pack()
        ))
        
    # Добавляем навигацию (prev | current_page | next)
    navigation_row = []
    
    # Кнопка Назад
    if page > 1:
        navigation_row.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=GroupPagination(page=page - 1, action="prev").pack()
        ))
    
    # Счетчик страниц
    total_pages = (len(groups) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if total_pages > 1:
        navigation_row.append(InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="ignore"  # Кнопка ничего не делает
        ))

    # Кнопка Вперед
    if page < total_pages:
        navigation_row.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=GroupPagination(page=page + 1, action="next").pack()
        ))
        
    builder.row(*navigation_row)
    return builder.as_markup()