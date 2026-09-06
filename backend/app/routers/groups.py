from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.deps import verify_api_key

from app.core.database import get_db
from app.models.models import Group
from app.schemas.schemas import GroupCreate, GroupResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("", response_model=list[GroupResponse])
async def get_all_groups(db: AsyncSession = Depends(get_db)):
    """Получить список всех групп/подгрупп для выбора на сайте."""
    stmt = select(Group).order_by(Group.title)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_by_id(group_id: int, db: AsyncSession = Depends(get_db)):
    """Получить информацию о конкретной группе."""
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )
    return group


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def create_group(group_in: GroupCreate, db: AsyncSession = Depends(get_db)):
    """Создать новую группу (вызывается ботом или администратором)."""
    # Проверяем на уникальность названия
    stmt = select(Group).where(Group.title == group_in.title)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Группа с таким названием уже существует"
        )

    new_group = Group(title = group_in.title)
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def delete_group(
    group_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Удалить группу полностью вместе с её расписанием."""
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Группа не найдена"
        )

    await db.delete(group)
    await db.commit()
    return None