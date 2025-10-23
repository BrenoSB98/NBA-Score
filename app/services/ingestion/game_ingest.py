import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta

from app.services.api_client import ApiClient
from app.models.game_models import Game,TeamStatistics
from app.models.team_models import Team
from app.repository.ingestion_repository import upsert_bulk
from app.schemas.game_schemas import GameCreate, TeamStatisticsCreate
from app.utils.hashing import generate_payload_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_games_by_date(api_client: ApiClient, date: str) -> Optional[List[Dict[str, Any]]]:
    logger.info(f"Buscando jogos para a data: {date}")
    
    try:
        games_data = api_client.get_games(date=date)
        if games_data:
            logger.info(f"Número de jogos encontrados para {date}: {len(games_data)}")
            return games_data
        logger.warning(f"Nenhum jogo encontrado para a data: {date}")
        return None
    except Exception as e:
        error_msg = f"Erro ao buscar jogos para a data {date}: {e}"
        logger.error(error_msg)
        return None

def transform_game_data(game_line: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transform_game = []    
    for game in game_line:
        date_info = game.get("date", {})
        status_info = game.get("status", {})
        arena_info = game.get("arena", {})
        teams_info = game.get("teams", {})
        scores_info = game.get("scores", {})
        
        home_team_info = teams_info.get("home", {})
        visitor_team_info = teams_info.get("visitors", {})
        home_score_info = scores_info.get("home", {})
        visitor_score_info = scores_info.get("visitors", {})
        
        game_datetime = None
        if date_info.get("start"):
            try:
                game_datetime = datetime.fromisoformat(date_info["date"].replace("Z", "+00:00"))
            except ValueError:
                logger.warning(f"Formato de data inválido para o jogo ID {game.get('id')}: {date_info['date']}")
        
        league_id = None
        league_data = game.get("league")
        if isinstance(league_data, dict):
            league_id = league_data.get("id")
        elif isinstance(league_data, str):
             pass
         
        payload_game = {
            "source_id": game.get("id"),
            "league_id": league_id,
            "season": game.get("season"),
            "game_date": game_datetime,
            "status": status_info.get("long"),
            "home_team_id": home_team_info.get("id"),
            "visitor_team_id": visitor_team_info.get("id"),
            "home_score": home_score_info.get("points"),
            "visitor_score": visitor_score_info.get("points"),
            "arena_name": arena_info.get("name"),
            "arena_city": arena_info.get("city"),
            "payload_hash": generate_payload_hash(game)
        }
        if payload_game["home_team_id"] and payload_game["visitor_team_id"]:
            game_schema = GameCreate(**payload_game)
            transform_game.append(game_schema.model.dump())
        else:
            logger.warning(f"Dados incompletos para o jogo ID {game.get('id')}, pulando.")
    return transform_game

def fetch_game_statistics(api_client: ApiClient, game_id: int) -> Optional[List[Dict[str, Any]]]:
    logger.info(f"Buscando estatísticas do jogo ID: {game_id}")
    
    try:
        stats_data = api_client.get_game_statistics(game_id=game_id)
        if stats_data:
            logger.info(f"Número de registros de estatísticas encontrados para o jogo ID {game_id}: {len(stats_data)}")
            return stats_data
        logger.warning(f"Nenhum dado de estatísticas encontrado para o jogo ID: {game_id}")
        return None
    except Exception as e:
        error_msg = f"Erro ao buscar estatísticas para o jogo ID {game_id}: {e}"
        logger.error(error_msg)
        return None
    
def transform_team_statistics_data(stats_line: List[Dict[str, Any]], game_source_id: int) -> List[Dict[str, Any]]:
    transform_stats = []    
    for stats in stats_line:
        team_info = stats.get("team", {})
        team_id = team_info.get("id")
        
        if not team_id:
            logger.warning(f"ID do time ausente nas estatísticas do jogo ID {game_source_id}, pulando.")
            continue
        stats_list = stats.get("statistics", [])
        if not stats_list:
            logger.warning(f"Lista de estatísticas vazia para o time ID {team_id} no jogo ID {game_source_id}, pulando.")
            continue
        payload_stats = {
                "team_id": team_id,
                "game_id": game_source_id,
                "points": stats.get("points"),
                "fgm": stats.get("fgm"),
                "fga": stats.get("fga"),
                "fgp": stats.get("fgp"),
                "ftm": stats.get("ftm"),
                "fta": stats.get("fta"),
                "ftp": stats.get("ftp"),
                "tpm": stats.get("tpm"),
                "tpa": stats.get("tpa"),
                "tpp": stats.get("tpp"),
                "off_reb": stats.get("offReb"),
                "def_reb": stats.get("defReb"),
                "tot_reb": stats.get("totReb"),
                "assists": stats.get("assists"),
                "p_fouls": stats.get("pFouls"),
                "steals": stats.get("steals"),
                "turnovers": stats.get("turnovers"),
                "blocks": stats.get("blocks"),
                "plus_minus": stats.get("plusMinus"),
                "fast_break_points": stats.get("fastBreakPoints"),
                "points_in_paint": stats.get("pointsInPaint"),
                "biggest_lead": stats.get("biggestLead"),
                "second_chance_points": stats.get("secondChancePoints"),
                "points_off_turnovers": stats.get("pointsOffTurnovers"),
                "longest_run": stats.get("longestRun"),
                "payload_hash": generate_payload_hash(stats)
            }
        try:
            stats_schema = TeamStatisticsCreate(**payload_stats)
            transform_stats.append(stats_schema.model.dump())
        except Exception as e:
            logger.warning(f"Erro ao criar schema para as estatísticas do time ID {team_id} no jogo ID {game_source_id}: {e}")  
            logger.debug(f"Dados de estatísticas problemáticos: {payload_stats}")
    return transform_stats

def ingest_games_for_date(db: Session, api_client: ApiClient, date: str) -> Dict[str, Any]:
    summary = {"source": "games_and_stats", "date": date, "status": "failure","processed": 0, "processed_stats": 0, "errors": []}
    
    list_games = []
    try:
        games_data = fetch_games_by_date(api_client, date)
        if not games_data:
            summary["status"] = "sucess"
            logger.info(f"Nenhum jogo para ingerir na data {date}.")
            return summary
        
        transformed_games = transform_game_data(games_data)
        if not transformed_games:
            summary["status"] = "sucess"
            logger.info(f"Nenhum jogo válido para ingerir na data {date}.")
            return summary
        
        logger.info(f"Iniciando a ingestão de {len(transformed_games)} jogos para a data {date}.")        
        upsert_bulk(db=db, model=Game, payloads=transformed_games, unique_key="source_id")
        summary["processed"] = len(list_games)
        logger.info(f"Número de jogos ingeridos para a data {date}: {summary['processed']}")
        
        all_stats = []
        for game in transformed_games:
            game_id = game["source_id"]
            
            if game.get("status") in ["Finished", "Completed", "FT"]:
                stats_data = fetch_game_statistics(api_client, game_id)
                if stats_data:
                    transformed_stats = transform_team_statistics_data(stats_data, game_id)
                    all_stats.extend(transformed_stats)
                else:
                    logger.debug(f"O jogo ID {game_id} não possui estatísticas para ingestão.")
        if all_stats:
            logger.info(f"Iniciando a ingestão de {len(all_stats)} registros de estatísticas de times para a data {date}.")
            upsert_bulk(db=db, model=TeamStatistics, payloads=all_stats, unique_key="id")
            summary["processed_stats"] = len(all_stats)
            logger.info(f"Número de registros de estatísticas ingeridos para a data {date}: {summary['processed_stats']}")
        
        summary["status"] = "sucess"
        db.commit()
    except Exception as e:
        db.rollback()
        error_msg = f"Erro durante a ingestão de jogos e estatísticas para a data {date}: {e}"
        logger.exception(error_msg)
        summary["errors"].append(error_msg)
    finally:
        logger.info(f"Finalizando a ingestão para a data {date} com status: {summary['status']}")
        db.close()
    return summary

def ingest_games_for_season(db: Session, api_client: ApiClient, season: int, start_month: int=10, end_month: int=6):
    logger.info(f"Iniciando a ingestão de jogos para a temporada {season} do mês {start_month} ao mês {end_month}.")
    try:
        start_date = datetime(season, start_month, 1)
        end_date = datetime(season + 1, end_month, 30)
    except ValueError as e:
        logger.error(f"Erro ao criar datas para a temporada {season}: {e}")
        return
    current_date = start_date
    games_processed = 0
    stats_processed = 0
    erros = 0
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        summary = ingest_games_for_date(db, api_client, date_str)
        games_processed += summary.get("processed", 0)
        stats_processed += summary.get("processed_stats", 0)
        
        if summary.get("status") == "failure":
            erros += 1
        current_date += timedelta(days=1)
        time.sleep(5)    
                