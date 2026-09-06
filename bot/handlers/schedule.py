from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from api_client import api_client

router = Router()

DAYS = {
    1: "Понедельник", 2: "Вторник", 3: "Среда",
    4: "Четверг", 5: "Пятница", 6: "Суббота", 7: "Воскресенье"
}


class ScheduleStates(StatesGroup):
    waiting_for_day = State()
    waiting_for_text = State()


def get_days_keyboard():
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"set_day_{num}")]
        for num, name in DAYS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "📝 Изменить расписание")
async def start_update_schedule(message: Message, state: FSMContext):
    # Проверяем, авторизован ли староста
    user = await api_client.get_user(message.from_user.id)
    if not user or not user.get("is_approved"):
        await message.answer("❌ У вас нет прав для изменения расписания или ваша заявка еще не одобрена.")
        return

    await state.update_data(group_id=user["group_id"])
    await message.answer("Выберите день недели для редактирования:", reply_markup=get_days_keyboard())
    await state.set_state(ScheduleStates.waiting_for_day)


@router.callback_query(ScheduleStates.waiting_for_day, F.data.startswith("set_day_"))
async def process_day_selection(callback: CallbackQuery, state: FSMContext):
    day_num = int(callback.data.split("_")[-1])
    await state.update_data(selected_day=day_num)
    
    await callback.message.edit_text(
        f"Выбран день: **{DAYS[day_num]}**\n\n"
        "Пришлите расписание списком в формате:\n"
        "`Время; Название предмета; Кабинет`\n\n"
        "Пример:\n"
        "`08:30-09:50; Высшая математика; 402`\n"
        "`10:00-11:20; Базы данных; 310`",
        parse_mode="Markdown"
    )
    await state.set_state(ScheduleStates.waiting_for_text)


@router.message(ScheduleStates.waiting_for_text)
async def process_schedule_text(message: Message, state: FSMContext):
    raw_text = message.text.strip()
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    
    parsed_lessons = []
    
    # Парсинг строки
    for line in lines:
        parts = [p.strip() for p in line.split(";")]
        if len(parts) != 3:
            await message.answer(
                f"⚠️ **Ошибка в строке:** `{line}`\n\n"
                "Формат должен быть строго: `Время; Предмет; Кабинет`",
                parse_mode="Markdown"
            )
            return
        
        parsed_lessons.append({
            "time": parts[0],
            "subject": parts[1],
            "room": parts[2]
        })

    data = await state.get_data()
    group_id = data["group_id"]
    day_num = data["selected_day"]

    # Отправка в FastAPI
    success = await api_client.update_schedule(
        group_id=group_id,
        day_of_week=day_num,
        telegram_id=message.from_user.id,
        lessons=parsed_lessons
    )

    if success:
        await message.answer(f"✅ Расписание на **{DAYS[day_num]}** успешно обновлено!", parse_mode="Markdown")
        await state.clear()
    else:
        await message.answer("❌ Ошибка при сохранении данных на сервере. Проверьте права доступа.")