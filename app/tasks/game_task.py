import logging
import time
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from app.services.api_client import ApiClient
from app.services.ingestion import game_ingest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_daily_game_task(db: Session, api_client: ApiClient, game_date: str):
    date_str = game_date.strftime("%Y-%m-%d")
    start_time = time.time()
    
    summary = {
        "task": "daily_game_ingestion",
        "game_date": date_str,
        "status": "failure",
        "processed_games": 0,
        "processed_teams_stats": 0,
        "errors": [],
        "duration_seconds": 0
    }
    
    try:
        ingest = game_ingest.ingest_games_for_date(db, api_client, date_str)
        
        summary["status"] = ingest.get("status", "failure")
        summary["processed_games"] = ingest.get("processed_games", 0)
        summary["processed_teams_stats"] = ingest.get("processed_teams_stats", 0)
        summary["errors"] = ingest.get("errors", [])
    except Exception as e:
        error_msg = "Erro durante a ingestão diária do jogo: {}".format(str(e))
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    logger.info(f"Task terminada: {summary}")
    return summary

def run_historical_game_task(db: Session, api_client: ApiClient, season: int):
    start_time = time.time()
    
    summary = {
        "task": "historical_game_ingestion",
        "season": season,
        "status": "failure",
        "errors": [],
        "duration_seconds": 0
    }
    
    try:
        ingest = game_ingest.ingest_games_for_season(db, api_client, season)
        
        summary["status"] = "success"
    except Exception as e:
        error_msg = "Erro durante a ingestão histórica do jogo: {}".format(str(e))
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    logger.info(f"Task terminada: {summary}")
    return summary