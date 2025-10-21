import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.api_client import ApiClient
from app.repository.ingestion_repository import upsert_bulk
from app.models.season_models import Season
from app.schemas.season_schemas import SeasonCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_seasons(api_client: ApiClient) -> Optional[List[int]]:
    """Fetch seasons data from the external API."""
    logger.info("Buscando temporadas na API externa...")
    
    try:
        seasons_data = api_client.get_seasons()
        if seasons_data is None:
            logger.warning("Nenhuma temporada encontrada na API.")
            return None
        return seasons_data
    except Exception as e:
        logger.error(f"Erro ao buscar temporadas: {e}")
        return None

def transform_season_data(seasons_data: List[int]) -> List[Dict[str, Any]]:
    """Transform raw season data into SeasonCreate schema."""
    logger.info(f"Transformando {len(seasons_data)} registros de temporadas.")
    transformed_seasons = []
    
    for year in seasons_data:
        season_schemas = SeasonCreate(season=year)
        transformed_seasons.append(season_schemas.model_dump())
    return transformed_seasons

def upsert_seasons(db: Session, seasons: List[Dict[str, Any]]) -> None:
    """Upsert season data into the database."""
    if not seasons:
        logger.info("Nenhum dado de temporada para inserir/atualizar.")
        return
    logger.info(f"Inserindo/atualizando {len(seasons)} registros de temporadas no banco de dados.")
    upsert_bulk(
        db_session=db, 
        model=Season, 
        payloads=seasons, 
        unique_key='season'
    )
    
def ingest_seasons(db: Session, api_client: ApiClient) -> Dict[str, Any]:
    """Main function to ingest seasons from API to database."""
    summary = {"source": "seasons", "status": "failure", "processed": 0, "errors": []}
    
    try:
        seasons_data = fetch_seasons(api_client)
        
        if seasons_data:
            transformed_seasons = transform_season_data(seasons_data)
            upsert_seasons(db, transformed_seasons)
            summary["status"] = "success"
            summary["processed"] = len(transformed_seasons)
    except Exception as e:
        error_msg = f"Erro durante a ingestão de temporadas: {e}"
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    logger.info(f"Resumo da ingestão de temporadas: {summary}")
    return summary