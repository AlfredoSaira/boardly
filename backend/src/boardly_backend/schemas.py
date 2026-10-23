from typing import Literal

from pydantic import BaseModel, Field

Column = Literal["new", "todo", "in_progress", "done"]


class Card(BaseModel):
    id: str
    title: str
    description: str = ""
    column: Column


class CardCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    column: Column = "new"


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None


class CardMove(BaseModel):
    column: Column


class ColumnInfo(BaseModel):
    id: Column
    title: str


class Board(BaseModel):
    columns: list[ColumnInfo]
    cards: list[Card]
