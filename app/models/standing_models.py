from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, IngestionControlMixin

class Standing(Base, TimestampMixin, IngestionControlMixin):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True)
    
    league_id = Column(Integer, ForeignKey("leagues.source_id"), nullable=False)
    season = Column(Integer, ForeignKey("seasons.season"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.source_id"), nullable=False)
    
    conference_name = Column(String(100))
    conference_rank = Column(Integer)
    division_name = Column(String(100))
    division_rank = Column(Integer)
    win = Column(Integer)
    loss = Column(Integer)
    games_behind = Column(String(10))
    streak = Column(Integer)
    win_streak = Column(Boolean)

    league = relationship("League", back_populates="standings")
    season_info = relationship("Season", back_populates="standings")
    team = relationship("Team", back_populates="standings")

    __table_args__ = (UniqueConstraint('league_id', 'season', 'team_id', name='_league_season_team_uc'),)

    def __repr__(self):
        return f"<Standing(season={self.season}, team_id={self.team_id}, rank={self.conference_rank})>"
