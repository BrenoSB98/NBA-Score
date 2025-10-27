import logging
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user_models import User
from app.services.api_client import ApiClient
from app.tasks import game_task, league_task, player_task, team_task, season_task, standings_task

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

def get_api_client() -> ApiClient:
    return ApiClient()

@router.post("/run/initial-load", status_code=status.HTTP_202_ACCEPTED, summary="Carrega dos dados estáticos iniciais")
async def run_initial_load(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    api_client: ApiClient = Depends(get_api_client),
):  
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    
    logger.info(f"Disparou a carga inicial.")
    def log_task_start():
        try:
            season_task.run_season_task(db, api_client)
            league_task.run_league_task(db, api_client)
            team_task.run_team_task(db, api_client)
        except Exception as e:
            logger.warning(f"Erro ao executar a tarefa: {e}")
        finally:
            db.close()
    background_tasks.add_task(log_task_start)
    return {"message": "Carga inicial disparada com sucesso."}

@router.post("/run/players/{season_year}", status_code=status.HTTP_202_ACCEPTED, summary="Carrega os dados dos jogadores para uma temporada específica")
async def run_player_load(
    season_year: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    api_client: ApiClient = Depends(get_api_client),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    
    logger.info(f"Disparou a carga de jogadores para a temporada {season_year}.")
    def log_task_start():
        try:
            player_task.run_player_task(db, api_client, season_year)
        except Exception as e:
            logger.warning(f"Erro ao executar a tarefa: {e}")
        finally:
            db.close()
    background_tasks.add_task(log_task_start)
    return {"message": f"Carga de jogadores para a temporada {season_year} disparada com sucesso."}

@router.post("/run/historicial-datas/{season}", status_code=status.HTTP_202_ACCEPTED, summary="Carrega os dados históricos para uma temporada específica")
async def run_historical_data_load(
    season: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    api_client: ApiClient = Depends(get_api_client),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    
    logger.info(f"Disparou a carga de dados históricos para a temporada {season}.")
    def log_task_start():
        try:
            team_task.run_team_season_task(db, api_client, season)
            player_task.run_players_task(db, api_client, season)
            player_task.run_players_stats_task(db, api_client, season)
            game_task.run_historical_game_task(db, api_client, season)
            standings_task.run_standings_task(db, api_client, season)
        except Exception as e:
            logger.warning(f"Erro ao executar a tarefa: {e}")
        finally:
            db.close()
    background_tasks.add_task(log_task_start)
    return {"message": f"Carga de dados históricos para a temporada {season} disparada com sucesso."}

@router.post("/run/daily-incremental", status_code=status.HTTP_202_ACCEPTED, summary="Carrega os dados incrementais diários")
async def run_daily_incremental_load(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    api_client: ApiClient = Depends(get_api_client),
    game_date: Optional[str] = None,
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    
    if game_date:
        try:
            today = date.fromisoformat(game_date)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data inválido. Use YYYY-MM-DD.")
    else:
        today = date.today() - timedelta(days=1)
        game_date = today.strftime("%Y-MM-DD")
        
    logger.info(f"Disparou a carga incremental diária para a data {today}.")
    def log_task_start():
        try:
            current_season = today.year if today.month >= 10 else today.year - 1
            game_task.run_daily_game_task(db, api_client, today)
            standings_task.run_standings_task(db, api_client, current_season)
        except Exception as e:
            logger.warning(f"Erro ao executar a tarefa: {e}")
        finally:
            db.close()
    background_tasks.add_task(log_task_start)
    return {"message": f"Carga incremental diária para a data {today} disparada com sucesso."}