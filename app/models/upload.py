from sqlalchemy import UUID, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey

from app.models.base import BaseSQLModel


# Таблица загрузок файлов пользователей
class Upload(BaseSQLModel):
    __tablename__ = "upload"
    name: Mapped[str] = mapped_column(String(length=250), nullable=False)
    unique_name: Mapped[str] = mapped_column(
        String(length=50), unique=True, nullable=False
    )
    file_type: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="uploads")
