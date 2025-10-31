from pydantic import BaseModel, Field

class SeasonBase(BaseModel):
    season: int = Field(..., example=2022, description="Ano da temporada (ex: 2022 para a temporada 2022-2023)")

    model_config = {
        "from_attributes": True
    }

class SeasonCreate(SeasonBase):
    pass

class Season(SeasonBase):
    model_config = {
        "from_attributes": True
    }