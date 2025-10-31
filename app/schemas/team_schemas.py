from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional
import decimal

class TeamLeagueBase(BaseModel):
    league_name: str
    conference: Optional[str] = None
    division: Optional[str] = None

class TeamLeagueCreate(TeamLeagueBase):
    team_id: int

class TeamLeague(TeamLeagueBase):
    id: int
    team_id: int
    
    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    source_id: int
    name: str = Field(..., example="Los Angeles Lakers")
    nickname: Optional[str] = Field(None, example="Lakers")
    code: Optional[str] = Field(None, example="LAL")
    city: Optional[str] = Field(None, example="Los Angeles")
    logo_url: Optional[HttpUrl] = None
    is_nba_franchise: Optional[bool] = None
    is_all_star: Optional[bool] = None

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamSeasonStatisticsBase(BaseModel):
    team_id: int
    season: int
    games_played: Optional[int] = None
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
    plus_minus: Optional[int] = None

class TeamSeasonStatisticsCreate(TeamSeasonStatisticsBase):
    pass

class TeamSeasonStatistics(TeamSeasonStatisticsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }