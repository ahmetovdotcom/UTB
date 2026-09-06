from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from api_client import api_client
from aiogram.filters import Command

router = Router()

# Фильтр, чтобы этот роутер слушал только администратора
router.callback_query.filter(F.from_user.id == settings.ADMIN_ID)


# Вспомогательная функция проверки прав
def is_admin(user_id: int) -> bool:
    return user_id == settings.ADMIN_ID



# --- Обработка ОДОБРЕНИЯ заявки ---
@router.callback_query(F.data.startswith("adm_app_"))
async def admin_approve_user(callback: CallbackQuery, bot: Bot):
    # Разделяем дату: adm_app_{teleid}_{groupid}
    parts = callback.data.split("_")
    telegram_id = int(parts[2])
    group_id = int(parts[3])

    # 1. Отправляем запрос в API на одобрение
    success = await api_client.approve_user(telegram_id, group_id, is_approved=True)
    
    if not success:
        await callback.answer("❌ Ошибка при обновлении прав в API.", show_alert=True)
        return

    # 2. Обновляем сообщение у админа
    new_text = callback.message.text + "\n\n✅ **ЗАЯВКА ОДОБРЕНА**"
    await callback.message.edit_text(new_text, reply_markup=None, parse_mode="Markdown")
    await callback.answer("Права выданы")

    # 3. Уведомляем старосту
    await bot.send_message(
        chat_id=telegram_id,
        text="🎉 **Поздравляем! Администратор одобрил вашу заявку.**\n\n"
             "Теперь вы можете управлять расписанием своей группы через меню.\n" \
             "Нажмите /start",
        parse_mode="Markdown"
    )

# --- Обработка ОТКЛОНЕНИЯ заявки ---
@router.callback_query(F.data.startswith("adm_rej_"))
async def admin_reject_user(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    telegram_id = int(parts[2])
    
    # 1. Отправляем запрос в API на отклонение (удаляем пользователя или ставим approved=False)
    # Предположим, API роутер на delete мы уже написали
    success = await api_client.delete_user(telegram_id)
    
    if not success:
        await callback.answer("❌ Ошибка при удалении пользователя из API.", show_alert=True)
        return

    # 2. Обновляем сообщение у админа
    new_text = callback.message.text + "\n\n❌ **ЗАЯВКА ОТКЛОНЕНА (Пользователь удален)**"
    await callback.message.edit_text(new_text, reply_markup=None, parse_mode="Markdown")
    await callback.answer("Заявка отклонена")

    # 3. Уведомляем старосту (вежливо)
    await bot.send_message(
        chat_id=telegram_id,
        text="😔 **Извините, ваша заявка на доступ к функциям старосты была отклонена администратором.**\n\n"
             "Если вы считаете, что это ошибка, свяжитесь с администрацией.",
        parse_mode="Markdown"
    )





# 1. СОЗДАНИЕ ГРУППЫ (Команда /add_group <имя>)
@router.message(Command("add_group"))
async def cmd_add_group(message: Message):
    # ПРОВЕРКА ПРАВ
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет прав администратора.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("⚠️ Использование: `/add_group ИмяГруппы`", parse_mode="Markdown")
    
    group_name = args[1].strip()
    
    # Передаем title=group_name вместо name=group_name
    success, result = await api_client.create_group(title=group_name)
    if success:
        await message.answer(f"✅ Группа **{group_name}** успешно создана!", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Ошибка создания группы: {result}")


# Вспомогательная функция для генерации карточки группы и пагинации
async def get_group_page(page_index: int):
    groups = await api_client.get_groups()
    
    if not groups:
        return "Список групп пуст.", None

    page_index = max(0, min(page_index, len(groups) - 1))
    group = groups[page_index]
    total = len(groups)

    # Используем .get() для безопасности, если бэкенд вернет title или name
    group_title = group.get("title") or group.get("name") or "Без названия"

    text = (
        f"📂 **Управление группами** ({page_index + 1}/{total})\n\n"
        f"🆔 **ID:** `{group['id']}`\n"
        f"🏷 **Название:** `{group_title}`"
    )

    buttons = []
    nav_row = []

    if page_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"adm_grp_page_{page_index - 1}"))
    if page_index < total - 1:
        nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"adm_grp_page_{page_index + 1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(
            text=f"🗑 Удалить {group_title}", 
            callback_data=f"adm_grp_del_{group['id']}_{page_index}"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return text, keyboard

# 2. ПРОСМОТР И УДАЛЕНИЕ (Команда /del_group)
@router.message(Command("del_group"))
async def cmd_del_group(message: Message):
    # ПРОВЕРКА ПРАВ
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет прав администратора.")

    
    text, keyboard = await get_group_page(0)
    if not keyboard:
        return await message.answer(text)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# 3. НАВИГАЦИЯ ПО СТРАНИЦАМ ГРУПП (Callback)
@router.callback_query(F.data.startswith("adm_grp_page_"))
async def process_group_page(callback: CallbackQuery):
    # ПРОВЕРКА ПРАВ
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Доступ запрещен", show_alert=True)

    
    page_index = int(callback.data.split("_")[3])
    text, keyboard = await get_group_page(page_index)
    
    if keyboard:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# 4. ПОДТВЕРЖДЕНИЕ И УДАЛЕНИЕ ГРУППЫ (Callback)
@router.callback_query(F.data.startswith("adm_grp_del_"))
async def process_group_delete(callback: CallbackQuery):
    # ПРОВЕРКА ПРАВ
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Доступ запрещен", show_alert=True)

    
    parts = callback.data.split("_")
    group_id = int(parts[3])
    page_index = int(parts[4])

    success = await api_client.delete_group(group_id)
    
    if not success:
        return await callback.answer("❌ Ошибка при удалении группы из API.", show_alert=True)

    await callback.answer("🗑 Группа удалена")
    
    # Показываем ту же страницу (или предыдущую, если это была последняя группа)
    text, keyboard = await get_group_page(page_index)
    if keyboard:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback.message.edit_text("✅ Все группы удалены.", reply_markup=None)