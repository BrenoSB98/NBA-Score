from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
import decimal

class PlayerLeagueBase(BaseModel):
    league_name: str
    jersey: Optional[int] = None
    is_active: Optional[bool] = None
    position: Optional[str] = None

class PlayerLeagueCreate(PlayerLeagueBase):
    player_id: int

class PlayerLeague(PlayerLeagueBase):
    id: int
    player_id: int

    class Config:
        from_attributes = True

class PlayerBase(BaseModel):
    source_id: int
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    birth_country: Optional[str] = None
    nba_start_year: Optional[int] = None
    pro_years: Optional[int] = None
    height_meters: Optional[decimal.Decimal] = None
    weight_kilograms: Optional[decimal.Decimal] = None
    college: Optional[str] = None
    affiliation: Optional[str] = None

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlayerStatisticsBase(BaseModel):
    player_id: int
    team_id: int
    game_id: int
    points: Optional[int] = None
    position: Optional[str] = None
    min_played: Optional[str] = None
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

class PlayerStatisticsCreate(PlayerStatisticsBase):
    pass

class PlayerStatistics(PlayerStatisticsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
