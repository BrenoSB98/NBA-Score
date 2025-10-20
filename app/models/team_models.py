from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
import decimal

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .game_models import Game, TeamStatistics
    from .standing_models import Standing
    from .player_models import PlayerStatistics
    from .season_models import Season

class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    nickname: Mapped[str | None] = mapped_column(String(255))
    code: Mapped[str | None] = mapped_column(String(10), index=True)
    city: Mapped[str | None] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(Text)
    is_nba_franchise: Mapped[bool | None]
    is_all_star: Mapped[bool | None]

    home_games: Mapped[List["Game"]] = relationship(foreign_keys="[Game.home_team_id]", back_populates="home_team")
    visitor_games: Mapped[List["Game"]] = relationship(foreign_keys="[Game.visitor_team_id]", back_populates="visitor_team")
    standings: Mapped[List["Standing"]] = relationship(back_populates="team")
    game_statistics: Mapped[List["TeamStatistics"]] = relationship(back_populates="team")
    season_statistics: Mapped[List["TeamSeasonStatistics"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    player_statistics: Mapped[List["PlayerStatistics"]] = relationship(back_populates="team")
    league_affiliations: Mapped[List["TeamLeague"]] = relationship(back_populates="team", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Equipe(id={self.id}, nome='{self.name}')>"

class TeamLeague(Base, TimestampMixin):
    __tablename__ = "team_league"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.source_id"), index=True)
    league_name: Mapped[str] = mapped_column(String(100), index=True)
    conference: Mapped[str | None] = mapped_column(String(100))
    division: Mapped[str | None] = mapped_column(String(100))

    team: Mapped["Team"] = relationship(back_populates="league_affiliations")

    __table_args__ = (UniqueConstraint("team_id", "league_name", name="_team_league_uc"),)

    def __repr__(self) -> str:
        return f"<Liga(team_id={self.team_id}, Liga='{self.league_name}')>"

class TeamSeasonStatistics(Base, TimestampMixin):
    __tablename__ = "team_season_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.source_id"), index=True)
    season: Mapped[int] = mapped_column(ForeignKey("seasons.season"), index=True)

    games: Mapped[int | None]
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
    plus_minus: Mapped[int | None]

    team: Mapped["Team"] = relationship(back_populates="season_statistics")
    season_info: Mapped["Season"] = relationship(back_populates="team_season_statistics")

    __table_args__ = (UniqueConstraint("team_id", "season", name="_team_season_uc"),)

    def __repr__(self) -> str:
        return f"<Estatísticas da Equipe na Temporada(season={self.season}, team_id={self.team_id})>"
