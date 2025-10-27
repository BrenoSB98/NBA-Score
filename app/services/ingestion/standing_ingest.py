import logging
import time
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session

from app.services.api_client import ApiClient
from app.models.standing_models import Standing
from app.repository.ingestion_repository import upsert_bulk
from app.schemas.standing_schemas import StandingCreate
from app.utils.hashing import generate_payload_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_standings(api_client: ApiClient, league_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
    logger.info(f"Buscando standings para a liga {league_id} na temporada {season}")
    try:
        standings_data = api_client.get_standings(league_id=league_id, season=season)
        if standings_data:
            logger.info(f"Encontrados {len(standings_data)} registros de standings para a liga {league_id} na temporada {season}")
            return standings_data
        logger.warning(f"Nenhum dado de standings encontrado para a liga {league_id} na temporada {season}")
        return None
    except Exception as e:
        error_msg = f"Erro ao buscar standings para a liga {league_id} na temporada {season}: {e}"
        logger.error(error_msg)
        return None

def transfrom_standings_data(standings_data: List[Dict[str, Any]], league_id: int, season: int) -> List[StandingCreate]:
    transformed_data = []
    for record in standings_data:
        team_info = record.get("team", {})
        conference_info = record.get("conference", {})
        division_info = record.get("division", {})
        win_info = record.get("win", {})
        loss_info = record.get("loss", {})
        
        payload_standardized = {
            "league_id": league_id,
            "season": season,
            "team_id": team_info.get("id"),
            "conference_name": conference_info.get("name"),
            "conference_rank": conference_info.get("rank"),
            "division_name": division_info.get("name"),
            "division_rank": division_info.get("rank"),
            "win": win_info.get("total"),
            "loss": loss_info.get("total"),
            "games_behind": record.get("gamesBehind"),
            "streak": record.get("streak"),
            "win_streak": record.get("winStreak"),
            "payload_hash": generate_payload_hash(record)
        }
        
        if payload_standardized["team_id"]:
            try:
                standing_create = StandingCreate(**payload_standardized)
                transformed_data.append(standing_create)
            except Exception as e:
                logger.error(f"Erro ao transformar o registro de standing: {e}. Registro: {record}")
                logger.debug(f"Payload padronizado com erro: {payload_standardized}")
        else:
            logger.warning(f"Registro de standing ignorado devido à ausência de team_id: {record}")
    return transformed_data

def upsert_standings(db: Session, standings: List[Dict[str, Any]]) -> None:
    if not standings:
        logger.info("Nenhum standing para inserir ou atualizar.")
        return
    
    try:
        upsert_bulk(db_session=db, model=Standing, payloads=standings, unique_key="id")
        logger.info(f"Upsert concluído para {len(standings)} registros de standings.")
    except Exception as e:
        logger.error(f"Erro ao realizar upsert dos standings: {e}")

def ingest_standings(db: Session, api_client: ApiClient, league_id: int, season: int) -> Dict[str, Any]:
    summary = {"source": "standings", "league_id": league_id, "season": season, "status": "failure", "processed": 0, "errors": []}
    try:
        standings_data = fetch_standings(api_client, league_id, season)
        if standings_data is None:
            summary["errors"].append(f"Nenhum dado de standings encontrado para a liga {league_id} na temporada {season}.")
            return summary
        transformed_standings = transfrom_standings_data(standings_data, league_id, season)
        if not transformed_standings:
            summary["errors"].append(f"Nenhum registro válido de standings após transformação para a liga {league_id} na temporada {season}.")
            return summary
        upsert_standings(db, [standing.dict() for standing in transformed_standings])
        db.commit()
        
        summary["status"] = "success"
        summary["processed"] = len(transformed_standings)
        logger.info(f"Ingestão concluída com sucesso para a liga {league_id} na temporada {season}. Registros processados: {summary['processed']}")
        return summary
    except Exception as e:
        db.rollback()
        error_msg = f"Erro inesperado durante a ingestão dos standings: {e}"
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    logger.info(f"Ingestão finalizada com status: {summary['status']}")
    return summary