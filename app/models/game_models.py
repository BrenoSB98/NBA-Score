from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Dict, Any
from datetime import datetime
import decimal

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .league_models import League
    from .season_models import Season
    from .team_models import Team

class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    source_id: Mapped[int] = mapped_column(unique=True, index=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.source_id"), index=True)
    season: Mapped[int] = mapped_column(ForeignKey("seasons.season"), index=True)
    game_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str | None] = mapped_column(String(100))
    stage: Mapped[int | None]
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.source_id"), index=True)
    visitor_team_id: Mapped[int] = mapped_column(ForeignKey("teams.source_id"), index=True)
    home_score: Mapped[int | None]
    visitor_score: Mapped[int | None]
    home_linescore: Mapped[Dict[str, Any] | None] = mapped_column(JSON)
    visitor_linescore: Mapped[Dict[str, Any] | None] = mapped_column(JSON)
    arena_name: Mapped[str | None] = mapped_column(String(255))
    arena_city: Mapped[str | None] = mapped_column(String(255))
    arena_country: Mapped[str | None] = mapped_column(String(255))

    league: Mapped["League"] = relationship(back_populates="games")
    season_info: Mapped["Season"] = relationship(back_populates="games")
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id], back_populates="home_games")
    visitor_team: Mapped["Team"] = relationship(foreign_keys=[visitor_team_id], back_populates="visitor_games")
    team_statistics: Mapped[List["TeamStatistics"]] = relationship(back_populates="game")

    def __repr__(self) -> str:
        return f"<Game(id={self.id}, date='{self.game_date}')>"

class TeamStatistics(Base, TimestampMixin):
    __tablename__ = "team_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    game_id: Mapped[int] = mapped_column(ForeignKey("games.source_id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.source_id"), index=True)
    
    fast_break_points: Mapped[int | None]
    points_in_paint: Mapped[int | None]
    biggest_lead: Mapped[int | None]
    second_chance_points: Mapped[int | None]
    points_off_turnovers: Mapped[int | None]
    longest_run: Mapped[int | None]
    points: Mapped[int | None]
    fgm: Mapped[int | None]
    fga: Mapped[int | None]
    fgp: Mapped[decimal.Decimal | None] = mapped_column(Numeric(5, 2))
    ftm: Mapped[int | None]
    fta: Mapped[int | None]
    ftp: Mapped[decimal.Decimal | None] = mapped_column(Numeric(5, 2))
    tpm: Mapped[int | None]
    tpa: Mapped[int | None]
    tpp: Mapped[decimal.Decimal | None] = mapped_column(Numeric(5, 2))
    off_reb: Mapped[int | None]
    def_reb: Mapped[int | None]
    tot_reb: Mapped[int | None]
    assists: Mapped[int | None]
    p_fouls: Mapped[int | None]
    steals: Mapped[int | None]
    turnovers: Mapped[int | None]
    blocks: Mapped[int | None]
    plus_minus: Mapped[str | None] = mapped_column(String(10))
    min_played: Mapped[str | None] = mapped_column(String(10))

    game: Mapped["Game"] = relationship(back_populates="team_statistics")
    team: Mapped["Team"] = relationship(back_populates="game_statistics")

    __table_args__ = (UniqueConstraint('game_id', 'team_id', name='_game_team_uc'),)

    def __repr__(self) -> str:
        return f"<TeamStatistics(game_id={self.game_id}, team_id={self.team_id})>"
