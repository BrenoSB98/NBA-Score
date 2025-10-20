from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .game_models import Game
    from .standing_models import Standing

class League(Base, TimestampMixin):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True, comment="ID interno sequencial do banco")
    source_id: Mapped[int] = mapped_column(unique=True, index=True, comment="ID da liga na API, se disponível")
    
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    type: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(Text)

    games: Mapped[List["Game"]] = relationship(back_populates="league")
    standings: Mapped[List["Standing"]] = relationship(back_populates="league")

    def __repr__(self) -> str:
        return f"<League(id={self.id}, name='{self.name}')>"
    