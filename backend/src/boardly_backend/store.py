import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import CardModel

COLUMNS = [
    {"id": "new", "title": "New"},
    {"id": "todo", "title": "To Do"},
    {"id": "in_progress", "title": "In Progress"},
    {"id": "done", "title": "Done"},
]


def _to_dict(card: CardModel) -> dict:
    return {
        "id": card.id,
        "title": card.title,
        "description": card.description,
        "column": card.column,
    }


class CardStore:
    """Same interface the in-memory mock had, now backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_cards(self) -> list[dict]:
        cards = self.session.scalars(select(CardModel)).all()
        return [_to_dict(c) for c in cards]

    def create(self, *, title: str, description: str, column: str) -> dict:
        card = CardModel(
            id=str(uuid.uuid4()), title=title, description=description, column=column
        )
        self.session.add(card)
        self.session.commit()
        self.session.refresh(card)
        return _to_dict(card)

    def get(self, card_id: str) -> dict | None:
        card = self.session.get(CardModel, card_id)
        return _to_dict(card) if card else None

    def update(self, card_id: str, **fields) -> dict | None:
        card = self.session.get(CardModel, card_id)
        if card is None:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(card, key, value)
        self.session.commit()
        self.session.refresh(card)
        return _to_dict(card)

    def delete(self, card_id: str) -> bool:
        card = self.session.get(CardModel, card_id)
        if card is None:
            return False
        self.session.delete(card)
        self.session.commit()
        return True
