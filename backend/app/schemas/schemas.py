from typing import Optional
from pydantic import BaseModel, ConfigDict

# --- GROUPS --- 

class GroupBase(BaseModel):
    title: str

class GroupCreate(GroupBase):
    pass

class GroupResponse(GroupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# --- USERS ---
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    group_id: Optional[int] = None


class UserCreate(UserBase):
    """Схема для регистрации / подачи заявки старостой из бота."""
    pass


class UserApprove(BaseModel):
    """Схема для подтверждения прав старосты администратором."""
    is_approved: bool
    group_id: Optional[int] = None


class UserResponse(UserBase):
    """Схема ответа с данными пользователя."""
    is_approved: bool

    model_config = ConfigDict(from_attributes=True)



# --- LESSONS / SHEDULES --- 

class LessonBase(BaseModel):
    time: str
    subject: str
    room: str

class LessonCreate(LessonBase):
    pass
    #day_of_week: int

class LessonResponse(LessonBase):
    id: int
    day_of_week: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleBulkCreate(BaseModel):
    """Схема массового создания/обновления расписания от бота."""
    telegram_id: int
    lessons: list[LessonCreate]



# --- SPECIAL RESPONSE FOR iOS SHORTCUTS ---
class IOSShortcutResponse(BaseModel):
    group_title: str
    day_name: str
    formatted_text: str  # Текст с emoji, готовый для отображения на экране блокировки
    lessons: list[LessonResponse]
