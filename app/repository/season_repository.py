from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.season_models import Season
from app.schemas.season_schemas import SeasonCreate

def create_season(db: Session, season_data: SeasonCreate) -> Season:
    season_data_dict = season_data.model_dump()
    stmt = insert(Season).values(**season_data_dict)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=['season']
    )
    db.execute(stmt)
    
    return db.query(Season).filter_by(season=season_data.season).first()
    