import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session

from app.services.api_client import APIClient
from app.repository.ingestion_repository import upsert_bulk
from app.models.league_models import League
from app.schemas.league_schemas import LeagueCreate
from app.utils.hashing import generate_payload_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_league_data(api_client: APIClient, league_id: int) -> Optional[Dict[str, Any]]:
    logger.info(f"Buscando dados da liga com ID: {league_id}")
    try:
        league_data = api_client.get_league(league_id)
        if league_data:
            logger.info(f"Dados da liga obtidos com sucesso para ID: {league_id}")
            return league_data
        logger.warning(f"Nenhum dado encontrado para a liga com ID: {league_id}")
    except Exception as e:
        logger.error(f"Erro ao buscar dados da liga com ID {league_id}: {e}")
        return None

def transform_leagues_data(league_data: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    logger.info(f"Transformando dados da liga com ID: {league_data.get('id')}")
    transform_data = []

    for item in league_data:
        payload = {}
        if isinstance(item, str):
            payload = {
                "source_id": abs(hash(item)) % (10**8),
                "name": item,
                "type": None,
                "logo_url": None,
            }
        elif isinstance(item, dict) and "id" in item and "name" in item:
            payload = {
                "source_id": item["id"],
                "name": item["name"],
                "type": item.get("type"),
                "logo_url": item.get("logo"),
            }
        else:
            logger.warning(f"Formato de dado inesperado: {item}")
            continue
        
        payload_hash = generate_payload_hash(payload)
        league_schema = LeagueCreate(**payload, payload_hash=payload_hash)
        transform_data.append(league_schema.model_dump())
        
    logger.info(f"Transformação concluída para {len(transform_data)} ligas")
    return transform_data

def upsert_leagues(db_session: Session, leagues_data: List[Dict[str, Any]]) -> None:
    if not leagues_data:
        logger.info("Nenhum dado de liga para inserir no banco.")
        return
    try:
        logger.info(f"Iniciando upsert para {len(leagues_data)} ligas")
        upsert_bulk(db=db_session, model=League, payloads=leagues_data, unique_key="source_id")
        logger.info("Upsert concluído com sucesso")
    except Exception as e:
        logger.error(f"Erro durante o upsert das ligas: {e}")

def ingest_leagues(api_client: APIClient, db_session: Session) -> Dict[str, Any]:
    summary = {"source": "leagues", "status": "failure", "processed": 0, "errors": []}
    
    try:
        league_data = fetch_league_data(api_client)
        if league_data:
            logger.info("Iniciando o processo de ingestão de ligas")
            transform_leagues = transform_leagues_data(league_data)
            
            upsert_leagues(db_session, transform_leagues)
            summary["status"] = "success"
            summary["processed"] = len(transform_leagues)
    
    except Exception as e:
        error_msg = f"Erro durante a ingestão de ligas: {e}"
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    logger.info(f"Resumo da ingestão: {summary}")
    return summary
