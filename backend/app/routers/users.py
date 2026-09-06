from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.deps import verify_api_key
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserResponse, UserApprove

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Get all users"""
    stmt = select(User).order_by(User.username)
    restult = await db.execute(stmt)
    return restult.scalars().all()






@router.get("/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Проверить профиль и права старосты по Telegram ID."""
    user = await db.get(User, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация или подача заявки от старосты из Telegram-бота."""
    existing_user = await db.get(User, user_in.telegram_id)
    if existing_user:
        return existing_user

    new_user = User(
        telegram_id=user_in.telegram_id,
        username=user_in.username,
        group_id=user_in.group_id,
        is_approved=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.patch("/{telegram_id}/approve", response_model=UserResponse, dependencies=[Depends(verify_api_key)])
async def approve_user(
    telegram_id: int, 
    approve_data: UserApprove, 
    db: AsyncSession = Depends(get_db)
):
    """Подтвердить права старосты для управления расписанием."""
    user = await db.get(User, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Пользователь не найден"
        )
    
    user.is_approved = approve_data.is_approved
    if approve_data.group_id:
        user.group_id = approve_data.group_id

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{telegram_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
async def delete_user(
    telegram_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Удалить профиль старосты из системы."""
    user = await db.get(User, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Пользователь не найден"
        )

    await db.delete(user)
    await db.commit()
    return None