from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
import decimal
from datetime import date

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .game_models import Game
    from .team_models import Team

class Player(Base, TimestampMixin):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    source_id: Mapped[int] = mapped_column(unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255), index=True)
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_country: Mapped[str | None] = mapped_column(String(255))
    nba_start_year: Mapped[int | None]
    pro_years: Mapped[int | None]
    height_meters: Mapped[decimal.Decimal | None] = mapped_column(Numeric(4, 2))
    weight_kilograms: Mapped[decimal.Decimal | None] = mapped_column(Numeric(5, 2))
    college: Mapped[str | None] = mapped_column(String(255))
    affiliation: Mapped[str | None] = mapped_column(String(255))

    game_statistics: Mapped[List["PlayerStatistics"]] = relationship(back_populates="player", cascade="all, delete-orphan")
    league_affiliations: Mapped[List["PlayerLeague"]] = relationship(back_populates="player", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Jogador(id={self.id}, nome='{self.first_name} {self.last_name}')>"

class PlayerLeague(Base, TimestampMixin):
    __tablename__ = "player_league"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.source_id"), index=True)
    league_name: Mapped[str] = mapped_column(String(100), index=True)
    jersey: Mapped[int | None]
    is_active: Mapped[bool | None]
    position: Mapped[str | None] = mapped_column(String(50))

    player: Mapped["Player"] = relationship(back_populates="league_affiliations")

    __table_args__ = (UniqueConstraint("player_id", "league_name", name="_player_league_uc"),)

    def __repr__(self) -> str:
        return f"<Liga do Jogador(id={self.player_id}, Liga='{self.league_name}')>"

class PlayerStatistics(Base, TimestampMixin):
    __tablename__ = "player_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    player_id: Mapped[int] = mapped_column(ForeignKey("players.source_id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.source_id"), index=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.source_id"), index=True)
    
    points: Mapped[int | None]
    position: Mapped[str | None] = mapped_column(String(50))
    min_played: Mapped[str | None] = mapped_column(String(10))
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
    comment: Mapped[str | None] = mapped_column(Text)

    player: Mapped["Player"] = relationship(back_populates="game_statistics")
    team: Mapped["Team"] = relationship(back_populates="player_statistics")
    game: Mapped["Game"] = relationship(back_populates="player_statistics")

    __table_args__ = (UniqueConstraint("player_id", "game_id", name="_player_game_uc"),)

    def __repr__(self) -> str:
        return f"<Estatistícas do Jogador(game_id={self.game_id}, player_id={self.player_id})>"