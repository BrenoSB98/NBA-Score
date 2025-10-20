from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .game_models import Game
    from .standing_models import Standing
    from .team_models import TeamSeasonStatistics
    from .player_models import PlayerSeasonStatistics

class Season(Base, TimestampMixin):
    __tablename__ = "seasons"

    season: Mapped[int] = mapped_column(primary_key=True, comment="Ano de início da temporada, usado como ID")        
    games: Mapped[List["Game"]] = relationship(back_populates="season_info")
    standings: Mapped[List["Standing"]] = relationship(back_populates="season_info")
    team_season_statistics: Mapped[List["TeamSeasonStatistics"]] = relationship(back_populates="season_info")
    player_season_statistics: Mapped[List["PlayerSeasonStatistics"]] = relationship(back_populates="season_info")

    def __repr__(self) -> str:
        return f"<Temporada(season={self.season})>"
