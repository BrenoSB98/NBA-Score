import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.services.api_client import APIClient
from app.models.team_models import Team, TeamLeague, TeamSeasonStatistics
from app.repository.ingestion_repository import upsert_bulk
from app.schemas.team_schemas import TeamCreate, TeamLeagueCreate, TeamSeasonStatisticsCreate
from app.utils.hashing import generate_payload_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_teams_data(api_client: APIClient) -> Optional[List[Dict[str, Any]]]:
    logger.info("Buscando times na API externa...")
    try:
        teams_data = api_client.get_teams()
        if teams_data:
            logger.info(f"Encontrados {len(teams_data)} times na API.")
            return teams_data
        logger.warning("Nenhum time encontrado na API.")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar times na API: {e}")
        return None

def transform_team_data(team_data: Dict[str, Any]) -> Tuple[TeamCreate, List[TeamLeagueCreate], List[TeamSeasonStatisticsCreate]]:
    logger.info(f"Transformando dados do time: {team_data.get('name')}")
    teams_to_upsert = []
    teams_leagues_to_upsert = []
    
    for team in team_data:
        if not team.get("nbaFranchise"):
            continue
        
        payload_team = {
            "source_id": team["id"],
            "name": team["name"],
            "nickname": team.get("nickname"),
            "code": team.get("code"),
            "city": team.get("city"),
            "logo_url": team.get("logo"),
            "is_nba_franchise": team.get("nbaFranchise"),
            "is_all_star": team.get("allStar"),
            "payload_hash": generate_payload_hash(team)
        }
        team_schema = TeamCreate(**payload_team)
        teams_to_upsert.append(team_schema)
        
        for league, details in team.get("leagues", {}).items():
            payload_league = {
                "team_id": team["id"],
                "league_name": league,
                "conference": details.get("conference"),
                "division": details.get("division"),
                "payload_hash": generate_payload_hash(details)
            }
            league_schema = TeamLeagueCreate(**payload_league)
            teams_leagues_to_upsert.append(league_schema)
    return teams_to_upsert, teams_leagues_to_upsert

def upsert_teams_and_leagues(db: Session, teams_data: List[TeamCreate], leagues_data: List[TeamLeagueCreate]) -> None:
    logger.info("Iniciando upsert de times e ligas no banco de dados...")
    try:
        if teams_data:
            logger.info(f"Upsert de {len(teams_data)} times...")
            upsert_bulk(db=db, model=Team, payloads=teams_data, unique_key="source_id")
            logger.info(f"Upsert concluído para {len(teams_data)} times.")
        
        if leagues_data:
            logger.info(f"Upsert de {len(leagues_data)} ligas de times...")
            upsert_bulk(db=db, model=TeamLeague, payloads=leagues_data, unique_key="id")
            logger.info(f"Upsert concluído para {len(leagues_data)} ligas de times.")
    except Exception as e:
        logger.error(f"Erro ao realizar upsert de times e ligas: {e}")

def ingest_teams(db: Session, api_client: APIClient) -> Dict[str, Any]:
    summary = {"source": "teams", "status": "failure", "processed": 0, "errors": []}
    
    try:
        teams_data = fetch_teams_data(api_client)
        if teams_data:
            teams_to_upsert, leagues_to_upsert = transform_team_data(teams_data)
            upsert_teams_and_leagues(db, teams_to_upsert, leagues_to_upsert)
            summary["status"] = "success"
            summary["processed"] = len(teams_to_upsert)
    except Exception as e:
        error_msg = f"Erro geral na ingestão de times: {e}"
        logger.error(error_msg)
        summary["errors"].append(error_msg)
        
    logger.info(f"Resumo da ingestão de times: {summary}")
    return summary

def fetch_team_season_stats(api_client: APIClient, team_id: int, season: int) -> Optional[Dict[str, Any]]:
    logger.info(f"Buscando estatísticas da temporada {season} para o time ID {team_id}...")
    try:
        stats_data = api_client.get_team_statistics(team_id=team_id, season=season)
        if stats_data and len(stats_data) > 0:
            logger.info(f"Estatísticas encontradas para o time ID {team_id} na temporada {season}.")
            return stats_data[0]
        logger.warning(f"Nenhuma estatística encontrada para o time ID {team_id} na temporada {season}.")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas para o time ID {team_id} na temporada {season}: {e}")
        return None

def transform_team_season_stats(team_id: int, season: int, stats_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Transformando estatísticas da temporada para o time ID {team_id}...")
    payload_stats = {
        "team_id": team_id,
        "season": season,
        "games_played": stats_data.get("games"),
        "points": stats_data.get("points"),
        "fgm": stats_data.get("fgm"),
        "fga": stats_data.get("fga"),
        "fgp": stats_data.get("fgp"),
        "ftm": stats_data.get("ftm"),
        "fta": stats_data.get("fta"),
        "ftp": stats_data.get("ftp"),
        "tpm": stats_data.get("tpm"),
        "tpa": stats_data.get("tpa"),
        "tpp": stats_data.get("tpp"),
        "off_reb": stats_data.get("offReb"),
        "def_reb": stats_data.get("defReb"),
        "tot_reb": stats_data.get("totReb"),
        "assists": stats_data.get("assists"),
        "p_fouls": stats_data.get("pFouls"),
        "steals": stats_data.get("steals"),
        "turnovers": stats_data.get("turnovers"),
        "blocks": stats_data.get("blocks"),
        "plus_minus": stats_data.get("plusMinus"),
        "payload_hash": generate_payload_hash(stats_data)
    }
    stats_schema = TeamSeasonStatisticsCreate(**payload_stats)
    return stats_schema.model_dump()

def ingest_team_season_statistics(db: Session, api_client: APIClient, season: int) -> Dict[str, Any]:
    summary = {"source": "teams_season_stats", "season": season, "status": "failure", "processed": 0, "errors": []}
    stats_to_upsert = []
    
    try:
        teams_in_db = db.query(Team).filter(Team.is_nba_franchise == True).all()
        if not teams_in_db:
            summary["errors"].append("Nenhum time NBA encontrado no banco de dados para ingestão de estatísticas.")
            return summary
        logger.info(f"Encontrados {len(teams_in_db)} times NBA no banco de dados para ingestão de estatísticas.")
        
        for team in teams_in_db:
            stats_data = fetch_team_season_stats(api_client, team.source_id, season)
            if stats_data:
                stats_schema = transform_team_season_stats(team.source_id, season, stats_data)
                stats_to_upsert.append(stats_schema)
        if stats_to_upsert:
            logger.info(f"Iniciando upsert de {len(stats_to_upsert)} estatísticas de temporada de times no banco de dados...")
            upsert_bulk(db=db, model=TeamSeasonStatistics, payloads=stats_to_upsert, unique_key=["team_id", "season"])
            logger.info(f"Upsert concluído para {len(stats_to_upsert)} estatísticas de temporada de times.")
            summary["status"] = "success"
            summary["processed"] = len(stats_to_upsert)
    except Exception as e:
        error_msg = f"Erro geral na ingestão de estatísticas de temporada de times: {e}"
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    logger.info(f"Resumo da ingestão de estatísticas de temporada de times: {summary}")
    return summary
