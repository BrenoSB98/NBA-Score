import logging
import time
from sqlalchemy.orm import Session

from app.services.api_client import ApiClient
from app.services.ingestion import player_ingest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_players_task(db: Session, client: ApiClient, season: int):
    start_time = time.time()
    
    summary = {
        "task": "players_ingestion",
        "season": season,
        "status": "failure",
        "processed_players": 0,
        "errors": [],
        "duration_seconds": 0
    }

    try:
        ingestion_summary = player_ingest.ingest_players(db=db, client=client, season=season)
        
        summary["status"] = ingestion_summary.get("status", "failure")
        summary["processed_players"] = ingestion_summary.get("processed_players", 0)
        summary["errors"] = ingestion_summary.get("errors", [])

    except Exception as e:
        error_message = f"Erro inesperado ao executar a tarefa de jogadores para a temporada {season}: {e}"
        logger.exception(error_message)
        summary["errors"].append(error_message)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    
    logger.info(f"Tarefa de ingestão de jogadores ({season}) finalizada. Resumo: {summary}")
    return summary

def run_players_stats_task(db: Session, client: ApiClient, season: int):
    start_time = time.time()
    
    summary = {
        "task": "players_stats_ingestion",
        "season": season,
        "status": "failure",
        "processed_players": 0,
        "total_stats_lines": 0,
        "errors": [],
        "duration_seconds": 0
    }

    try:
        ingestion_summary = player_ingest.ingest_player_stats(db=db, client=client, season=season)
        
        summary["status"] = ingestion_summary.get("status", "failure")
        summary["processed_players"] = ingestion_summary.get("processed_players", 0)
        summary["total_stats_lines"] = ingestion_summary.get("total_stats_lines", 0)
        summary["errors"] = ingestion_summary.get("errors", [])

    except Exception as e:
        error_message = f"Erro inesperado ao executar a tarefa de estatísticas de jogadores para a temporada {season}: {e}"
        logger.exception(error_message)
        summary["errors"].append(error_message)
    
    end_time = time.time()
    summary["duration_seconds"] = round(end_time - start_time, 2)
    
    logger.info(f"Tarefa de ingestão de estatísticas de jogadores ({season}) finalizada. Resumo: {summary}")
    return summary