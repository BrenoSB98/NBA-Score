import logging
import time
from sqlalchemy.orm import Session

from app.services.api_client import ApiClient
from app.services.ingestion import teams_ingest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_team_task(db: Session, api_client: ApiClient):
    start_time = time.time()
    
    summary = {
        "task": "teams_ingestion",
        "status": "failure",
        "processed_teams": 0,
        "errors": [],
        "duration_seconds": 0
    }
    
    try:
        ingest = teams_ingest.ingest_teams(db, api_client)
        
        summary["status"] = ingest.get("status", "failure")
        summary["processed_teams"] = ingest.get("processed_teams", 0)
        summary["errors"] = ingest.get("errors", [])
    except Exception as e:
        error_msg = "Erro durante a ingestão da equipe: {}".format(str(e))
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    logger.info(f"Task terminada: {summary}")
    return summary

def run_team_season_task(db: Session, api_client: ApiClient, season: int):
    start_time = time.time()
    
    summary = {
        "task": "teams_season_stats_ingestion",
        "season": season,
        "status": "failure",
        "processed_records": 0,
        "errors": [],
        "duration_seconds": 0
    }
    
    try:
        ingest = teams_ingest.ingest_team_season_statistics(db, api_client, season)
        
        summary["status"] = ingest.get("status", "failure")
        summary["processed_records"] = ingest.get("processed_records", 0)
        summary["errors"] = ingest.get("errors", [])
    except Exception as e:
        error_msg = "Erro durante a ingestão da temporada da equipe: {}".format(str(e))
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    logger.info(f"Task terminada: {summary}")
    return summary