from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class CardModel(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    column: Mapped[str] = mapped_column(String, nullable=False)
