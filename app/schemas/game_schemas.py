from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import decimal

class GameBase(BaseModel):
    source_id: int
    league_id: int
    season: int
    game_date: Optional[datetime] = None
    status: Optional[str] = None
    home_team_id: int
    visitor_team_id: int
    home_score: Optional[int] = None
    visitor_score: Optional[int] = None
    arena_name: Optional[str] = None
    arena_city: Optional[str] = None

class GameCreate(GameBase):
    pass

class Game(GameBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamStatisticsBase(BaseModel):
    team_id: int
    game_id: int
    points: Optional[int] = None
    fast_break_points: Optional[int] = None,
    points_in_paint: Optional[int] = None,
    biggest_lead: Optional[int] = None,
    second_chance_points: Optional[int] = None,
    points_off_turnovers: Optional[int] = None,
    longest_run: Optional[int] = None,
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fgp: Optional[decimal.Decimal] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    ftp: Optional[decimal.Decimal] = None
    tpm: Optional[int] = None
    tpa: Optional[int] = None
    tpp: Optional[decimal.Decimal] = None
    off_reb: Optional[int] = None
    def_reb: Optional[int] = None
    tot_reb: Optional[int] = None
    assists: Optional[int] = None
    p_fouls: Optional[int] = None
    steals: Optional[int] = None
    turnovers: Optional[int] = None
    blocks: Optional[int] = None
    plus_minus: Optional[str] = None

class TeamStatisticsCreate(TeamStatisticsBase):
    pass

class TeamStatistics(TeamStatisticsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TeamGameLogBase(BaseModel):
    team_id: int
    game_id: int
    is_home: bool
    points: Optional[int] = None
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fgp: Optional[decimal.Decimal] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    ftp: Optional[decimal.Decimal] = None
    tpm: Optional[int] = None
    tpa: Optional[int] = None
    tpp: Optional[decimal.Decimal] = None
    off_reb: Optional[int] = None
    def_reb: Optional[int] = None
    tot_reb: Optional[int] = None
    assists: Optional[int] = None
    p_fouls: Optional[int] = None
    steals: Optional[int] = None
    turnovers: Optional[int] = None
    blocks: Optional[int] = None
    plus_minus: Optional[str] = None

class TeamGameLogCreate(TeamGameLogBase):
    pass

class TeamGameLog(TeamGameLogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True