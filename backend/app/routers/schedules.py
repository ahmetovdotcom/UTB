import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.deps import verify_api_key
from app.core.database import get_db
from app.models.models import Group, Schedule, User
from app.schemas.schemas import (
    LessonResponse, 
    IOSShortcutResponse, 
    ScheduleBulkCreate
)
from app.utils.time_parser import sort_schedules_by_time
from app.services.wallpaper import generate_schedule_wallpaper

router = APIRouter(prefix="/schedules", tags=["Schedules"])

# Папка кэша для сгенерированных PNG
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "wallpaper_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

DAYS_MAP = {
    1: "Понедельник", 2: "Вторник", 3: "Среда", 
    4: "Четверг", 5: "Пятница", 6: "Суббота", 7: "Воскресенье"
}

def invalidate_wallpaper_cache(group_id: int, day_of_week: int):
    """Вспомогательная функция для сброса файла кэша при обновлении расписания."""
    cache_path = os.path.join(CACHE_DIR, f"{group_id}_{day_of_week}.png")
    if os.path.exists(cache_path):
        os.remove(cache_path)

@router.get("/{group_id}", response_model=list[LessonResponse])
async def get_schedule(
    group_id: int,
    day: int = Query(..., ge=1, le=7, description="1 (Пн) .. 7 (Вс)"),
    db: AsyncSession = Depends(get_db)
):
    """Получить массив пар группы на конкретный день в хронологическом порядке."""
    stmt = (
        select(Schedule)
        .where(Schedule.group_id == group_id, Schedule.day_of_week == day)
    )
    result = await db.execute(stmt)
    lessons = result.scalars().all()
    
    # Красивая сортировка в одну строчку через вынесенный сервис
    return sort_schedules_by_time(lessons)


@router.get("/{group_id}/wallpaper.png")
async def get_schedule_wallpaper(
    group_id: int,
    day: int = Query(..., ge=1, le=7, description="День недели (1..7)"),
    db: AsyncSession = Depends(get_db)
):
    """Возвращает PNG-изображение расписания для обоев iOS (с дисковым кэшем)."""
    cache_file_path = os.path.join(CACHE_DIR, f"{group_id}_{day}.png")

    # 1. Если файл кэша уже существует — сразу отдаем его с диска (за доли миллисекунды)
    if os.path.exists(cache_file_path):
        return FileResponse(cache_file_path, media_type="image/png")

    # 2. Если кэша нет — берем данные из БД
    day_name = DAYS_MAP.get(day)
    if not day_name:
        raise HTTPException(status_code=400, detail="Некорректный день недели")

    stmt = select(Schedule).where(
        Schedule.group_id == group_id, 
        Schedule.day_of_week == day
    )
    result = await db.execute(stmt)
    lessons = sort_schedules_by_time(result.scalars().all())

    # 3. Генерируем изображение в памяти
    png_bytes = generate_schedule_wallpaper(day_name, lessons)

    # 4. Сохраняем на диск для следующих 999 студентов этой группы
    with open(cache_file_path, "wb") as f:
        f.write(png_bytes)

    return Response(content=png_bytes, media_type="image/png")


@router.put("/{group_id}/day/{day_of_week}", response_model=list[LessonResponse], dependencies=[Depends(verify_api_key)])
async def update_day_schedule(
    group_id: int,
    day_of_week: int,
    payload: ScheduleBulkCreate,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, payload.telegram_id)
    if not user or not user.is_approved or user.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для изменения расписания этой группы"
        )

    delete_stmt = (
        delete(Schedule)
        .where(Schedule.group_id == group_id, Schedule.day_of_week == day_of_week)
    )
    await db.execute(delete_stmt)

    new_lessons = [
        Schedule(
            group_id=group_id,
            day_of_week=day_of_week,
            time=lesson.time,
            subject=lesson.subject,
            room=lesson.room
        )
        for lesson in payload.lessons
    ]
    
    db.add_all(new_lessons)
    await db.commit()
    
    # СБРАСЫВАЕМ КЭШ ОБОЕВ, чтобы генерация пересобрала новую картинку
    invalidate_wallpaper_cache(group_id, day_of_week)
    
    stmt = (
        select(Schedule)
        .where(Schedule.group_id == group_id, Schedule.day_of_week == day_of_week)
        .order_by(Schedule.time)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.delete("/{group_id}/day/{day_of_week}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def clear_day_schedule(
    group_id: int,
    day_of_week: int,
    telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, telegram_id)
    if not user or not user.is_approved or user.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для изменения расписания этой группы"
        )

    stmt = (
        delete(Schedule)
        .where(Schedule.group_id == group_id, Schedule.day_of_week == day_of_week)
    )
    await db.execute(stmt)
    await db.commit()

    # СБРАСЫВАЕМ КЭШ ОБОЕВ
    invalidate_wallpaper_cache(group_id, day_of_week)

    return None