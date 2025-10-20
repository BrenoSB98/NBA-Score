from pydantic import BaseModel, Field

class SeasonSchema(BaseModel):
    season: int = Field(..., example=2022, description="Ano da temporada (ex: 2022 para a temporada 2022-2023)")

    class Config:
        orm_mode = True

class SeasonCreateSchema(SeasonSchema):
    pass

class Season(SeasonSchema):
    class Config:
        from_attributes = True