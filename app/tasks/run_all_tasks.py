import logging
import time
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal, check_db_connection
from app.services.api_client import ApiClient
from app.tasks import (season_task, team_task, league_task, player_task, game_task, standings_task)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _get_dependencies():
    db = SessionLocal()
    cliente = ApiClient()
    return db, cliente

def _close_dependencies(db: Session):
    if db:
        db.close()
        logger.info("Sessão do banco fechada.")

def run_initial_tasks(season_to_load_players: int = datetime.now().year):
    start_time = time.time()
    db, cliente = _get_dependencies()
    overall_status = "sucess"
    summaries = []
    
    try:
        if not check_db_connection():
            raise Exception("Não foi possível conectar ao banco de dados.")
        
        summaries.append(season_task.run_season_task(db, cliente))
        summaries.append(league_task.run_league_task(db, cliente))
        summaries.append(team_task.run_team_task(db, cliente))
        summaries.append(player_task.run_player_task(db, cliente, season_to_load_players))
        
        for summary in summaries:
            if summary.get("status") == "failure":
                overall_status = "partial_failed"
                logger.error(f"Erro na tarefa: {summary.get('task')}, Detalhes: {summary.get('details')}")
    except Exception as e:
        overall_status = "failed"
        logger.error(f"Erro ao executar tarefas históricas: {e}")
    finally:
        _close_dependencies(db)
    
    end_time = time.time()
    duration = round(end_time - start_time,2)
    logger.info(f"Tarefas históricas concluídas com status: {overall_status} em {duration:.2f} segundos.")

def run_daily_incremental_tasks(date_to_load: date = date.today() - timedelta(days=1)):
    date_str = date_to_load.strftime("%Y-%m-%d")
    
    logger.info(f"Iniciando tarefas incrementais diárias para a data: {date_str}")
    start_time = time.time()
    db, cliente = _get_dependencies()
    overall_status = "sucess"
    summaries = []
    
    season_active = date_to_load.year if date_to_load.month >= 10 else date_to_load.year - 1
    league_id = 12
    try:
        if not check_db_connection():
            raise Exception("Não foi possível conectar ao banco de dados.")
        
        summaries.append(game_task.run_daily_game_task(db, cliente, date_to_load))
        summaries.append(standings_task.run_standings_task(db, cliente, league_id, season_active))
        
        for summary in summaries:
            if summary.get("status") == "failure":
                overall_status = "partial_failed"
                logger.error(f"Erro na tarefa: {summary.get('task')}, Detalhes: {summary.get('details')}")
    except Exception as e:
        overall_status = "failed"
        logger.error(f"Erro ao executar tarefas incrementais diárias: {e}")
    finally:
        _close_dependencies(db)
    
    end_time = time.time()
    duration = round(end_time - start_time,2)
    logger.info(f"Tarefas incrementais diárias concluídas com status: {overall_status} em {duration:.2f} segundos.")

def run_historical_tasks(season: int):
    logger.info("Iniciando todas as tarefas (históricas e incrementais diárias).")
    start_time = time.time()
    db, client = _get_dependencies()
    overall_status = "sucess"
    summaries = []
    
    try:
        if not check_db_connection():
            raise Exception("Não foi possível conectar ao banco de dados.")
        
        summaries.append(team_task.run_team_season_task(db, client, season=season))
        summaries.append(player_task.run_players_task(db, client, season=season))
        summaries.append(player_task.run_players_stats_task(db, client, season=season))
        summaries.append(game_task.run_historical_game_task(db, client, season))
                
        for summary in summaries:
            if summary.get("status") == "failure":
                overall_status = "partial_failed"
                logger.error(f"Erro na tarefa: {summary.get('task')}, Detalhes: {summary.get('details')}")
    except Exception as e:
        overall_status = "failed"
        logger.error(f"Erro ao executar todas as tarefas: {e}")
    finally:
        _close_dependencies(db)
    
    end_time = time.time()
    duration = round(end_time - start_time,2)
    logger.info(f"Todas as tarefas concluídas com status: {overall_status} em {duration:.2f} segundos.")

if __name__ == "__main__":
    run_initial_tasks(season_to_load_players=2022)
    #run_daily_incremental_tasks()
    #run_historical_tasks(season=2022)
    pass