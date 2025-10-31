from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class LeagueBase(BaseModel):
    source_id: int
    name: str = Field(..., example="standard")
    type: Optional[str] = Field(None, example="standard")
    logo_url: Optional[HttpUrl] = None

class LeagueCreate(LeagueBase):
    pass

class League(LeagueBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }