import logging
import time
from sqlalchemy.orm import Session

from app.services.api_client import ApiClient
from app.services.ingestion import leagues_ingest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_league_task(db: Session, api_client: ApiClient):
    start_time = time.time()
    
    summary = {"task": "league_ingestion", 
               "status": "failure", 
               "inserted_records": 0, 
               "updated_records": 0,
               "processed_leagues": 0,
               "errors": [],
               "duration_seconds": 0
    }
    
    try:
        ingest = leagues_ingest.ingest_leagues(db, api_client)
        
        summary["status"] = ingest.get("status", "failure")
        summary["processed_leagues"] = ingest.get("processed_leagues", 0)
        summary["errors"] = ingest.get("errors", [])
    except Exception as e:
        error_msg = "Erro durante a ingestão da liga: {}".format(str(e))
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    logger.info(f"Task terminada: {summary}")
    return summary