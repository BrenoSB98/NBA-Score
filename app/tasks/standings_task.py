import logging
import time
from sqlalchemy.orm import Session

from app.services.api_client import ApiClient
from app.services.ingestion import standing_ingest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_standings_task(db: Session, api_client: ApiClient, league_id: int, season: int):
    start_time = time.time()
    
    summary = {
        "task": "standings_ingestion",
        "league_id": league_id,
        "season": season,
        "status": "failure",
        "processed_standings": 0,
        "errors": [],
        "duration_seconds": 0
    }
    
    try:
        ingest = standing_ingest.ingest_standings(db, api_client, league_id, season)
        
        summary["status"] = ingest.get("status", "failure")
        summary["processed_standings"] = ingest.get("processed_standings", 0)
        summary["errors"] = ingest.get("errors", [])
    except Exception as e:
        error_msg = "Erro durante a ingestão da classificação: {}".format(str(e))
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    
    logger.info(f"Task terminada: {summary}")
    return summary