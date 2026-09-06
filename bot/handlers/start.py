from html import escape
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from api_client import api_client
from config import settings
from keyboards.group_pagination import get_groups_keyboard
from keyboards.callbacks import GroupPagination
from keyboards.admin_approve import get_admin_approve_keyboard
from keyboards.main_menu import get_starosta_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    full_name = escape(message.from_user.full_name or message.from_user.username or "Пользователь")

    # 1. Запрашиваем профиль из API
    user = await api_client.get_user(telegram_id)
    
    if user:
        if user['is_approved']:
            group_title = "Не назначена"
            
            # 2. Если у пользователя есть group_id, находим название группы
            user_group_id = user.get('group_id')
            if user_group_id:
                groups = await api_client.get_groups()
                # Ищем группу с совпадающим ID
                target_group = next((g for g in groups if g['id'] == user_group_id), None)
                if target_group:
                    group_title = target_group['title']
            
            # 3. Экранируем название группы для безопасности HTML
            group_title = escape(group_title)

            await message.answer(
                f"👋 Здравствуйте, староста <b>{full_name}</b>!\n\n"
                f"Используйте меню ниже для управления расписанием группы <b>{group_title}</b>.",
                parse_mode="HTML",
                reply_markup=get_starosta_main_menu()
            )
            return
        else:
            await message.answer("⏳ Ваша заявка на рассмотрении у администратора.")
            return

    # 2. Если пользователя нет, предлагаем выбрать группу (пагинация с page=1)
    groups = await api_client.get_groups()
    if not groups:
        await message.answer("⚠️ В базе данных пока нет созданных групп.")
        return

    await message.answer(
    "👋 Здравствуйте!\n\n"
    "Этот бот предназначен для старост, чтобы они могли удобно вести расписание.\n"
    "Для начала работы выберите вашу группу из списка ниже, чтобы подать заявку администратору:",
        reply_markup=get_groups_keyboard(groups, page=1),
        parse_mode="Markdown"
    )

# --- Обработка пагинации (Нажатие Вперед/Назад) ---
@router.callback_query(GroupPagination.filter(F.action.in_({"prev", "next"})))
async def process_pagination(callback: CallbackQuery, callback_data: GroupPagination):
    groups = await api_client.get_groups()
    
    # Обновляем сообщение новой клавиатурой
    await callback.message.edit_reply_markup(
        reply_markup=get_groups_keyboard(groups, page=callback_data.page)
    )
    await callback.answer()

# --- Обработка выбора группы старостой ---
@router.callback_query(GroupPagination.filter(F.action == "select"))
async def process_group_select(callback: CallbackQuery, callback_data: GroupPagination, bot: Bot):
    telegram_id = callback.from_user.id
    full_name = callback.from_user.full_name or callback.from_user.username
    group_id = callback_data.group_id
    
    # 1. Получаем название группы
    groups = await api_client.get_groups()
    group_title = next((g['title'] for g in groups if g['id'] == group_id), "???")

    # 2. Регистрируем пользователя в API (с is_approved=False)
    success = await api_client.register_user(telegram_id, full_name, group_id)
    
    if not success:
        await callback.message.answer("❌ Ошибка при подаче заявки. Попробуйте позже.")
        await callback.answer()
        return

    # 3. Уведомляем старосту
    await callback.message.edit_text(
        f"✅ Заявка отправлена!\n\n"
        f"Вы выбрали группу: **{group_title}**.\n\n"
        "Ожидайте одобрения администратором. Бот уведомит вас о результате.",
        parse_mode="Markdown"
    )
    await callback.answer()

    # 4. ОТПРАВЛЯЕМ ЗАЯВКУ АДМИНУ
    admin_text = (
        "🔔 **Новая заявка старосты!**\n\n"
        f"👤 Староста: **{full_name}**\n"
        f"🆔 Telegram ID: `{telegram_id}`\n"
        f"👥 Группа: **{group_title}**"
    )
    
    await bot.send_message(
        chat_id=settings.ADMIN_ID,
        text=admin_text,
        reply_markup=get_admin_approve_keyboard(telegram_id, group_id),
        parse_mode="Markdown"
    )