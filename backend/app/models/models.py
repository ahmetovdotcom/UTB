from typing import Optional, List
from sqlalchemy import BigInteger, SmallInteger, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.database import Base





class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # связи
    users: Mapped[List["User"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="group", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )

    # связи
    group: Mapped[Optional["Group"]] = relationship(back_populates="users")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    time: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(150), nullable=False)
    room: Mapped[str] = mapped_column(String(50), nullable=False)


    # relactionships
    group: Mapped["Group"] = relationship(back_populates="schedules")