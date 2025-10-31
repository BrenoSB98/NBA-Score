from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StandingBase(BaseModel):
    league_id: int
    season: int
    team_id: int
    conference_name: Optional[str] = None
    conference_rank: Optional[int] = None
    division_name: Optional[str] = None
    division_rank: Optional[int] = None
    win: Optional[int] = None
    loss: Optional[int] = None
    games_behind: Optional[str] = None
    streak: Optional[int] = None
    win_streak: Optional[bool] = None

class StandingCreate(StandingBase):
    pass

class Standing(StandingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }