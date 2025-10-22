import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.api_client import ApiClient
from app.models.player_models import Player, PlayerLeague
from app.models.team_models import Team
from app.models.game_models import Game
from app.repository.ingestion_repository import upsert_bulk
from app.schemas.player_schemas import PlayerCreate, PlayerLeagueCreate
from app.schemas.game_schemas import PlayerStatisticsCreate
from app.utils.hashing import generate_payload_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_players_per_team(api_client: ApiClient, team_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
    logger.info(f"Buscando jogadores para o time {team_id} na temporada {season}.")
    
    try:
        player_data = api_client.get_players(team_id=team_id, season=season)
        if player_data:
            logger.info(f"Encontrados {len(player_data)} jogadores para o time {team_id} na temporada {season}.")
            return player_data
        logger.warning(f"Nenhum jogador encontrado para o time {team_id} na temporada {season}.")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar jogadores para o time {team_id} na temporada {season}: {e}")
        return None

def transform_player_data(players_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    player_to_upsert = []
    player_league_to_upsert = []
        
    for raw_player in players_data:
        birth_date = raw_player.get("birth", {})
        #if birth_date:
        #    birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        nba_info = raw_player.get("nba", {})
        height_info = nba_info.get("height", {})
        weight_info = nba_info.get("weight", {})
        
        payload_player = {
            "source_id": raw_player["id"],
            "first_name": raw_player["firstname"],
            "last_name": raw_player["lastname"],
            "birth_date": raw_player.get("date"),
            "birth_country": birth_date.get("country"),
            "nba_start_year": nba_info.get("start"),
            "pro_years": nba_info.get("pro"),
            "height_feet": height_info.get("meters"),
            "weight_kg": weight_info.get("kilograms"),
            "college": raw_player.get("college"),
            "affiliation": raw_player.get("affiliation"),
            "payload_hash": generate_payload_hash(raw_player)
        }
        player_data = PlayerCreate(**payload_player)
        player_to_upsert.append(player_data.model_dump())
        
        for league, details in raw_player.get("leagues", {}).items():
            if not details:
                continue
            
            payload_league = {
                "player_id": raw_player["id"],
                "league_name": league,
                "jersey": details.get("jersey"),
                "is_active": details.get("active"),
                "position": details.get("position"),
                "payload_hash": generate_payload_hash(details),
            }
            player_league_data = PlayerLeagueCreate(**payload_league)
            player_league_to_upsert.append(player_league_data.model_dump())
    return player_to_upsert, player_league_to_upsert

def ingest_players(db: Session, api_client: ApiClient, season: int) -> Dict[str, Any]:    
    summary = {"source": "players", "season": season, "status": "failure", "processed": 0, "errors": []}
    players_to_upsert = []
    league_to_upsert = []
    
    try:
        teams_in_db = db.query(Team).filter(Team.is_nba_franchise == True).all()
        if not teams_in_db:
            logger.warning("Nenhum time da NBA encontrado no banco de dados para ingestão de jogadores.")
            summary["errors"].append("Nenhum time da NBA encontrado no banco de dados.")
            return summary
        
        logger.info(f"Iniciando ingestão de jogadores para {len(teams_in_db)} times na temporada {season}.")
        for team in teams_in_db:
            players_data = fetch_players_per_team(api_client, team.source_id, season)
            if players_data:
                transformed_players, transformed_league = transform_player_data(players_data)
                players_to_upsert.extend(transformed_players)
                league_to_upsert.extend(transformed_league)

        if players_to_upsert:
            logger.info(f"Inserindo/atualizando {len(players_to_upsert)} registros de jogadores...")
            upsert_bulk(db=db, model=Player, payloads=players_to_upsert, unique_key="source_id")
            
        
        if league_to_upsert:
            logger.info(f"Inserindo/atualizando {len(league_to_upsert)} afiliações de jogadores...")
            upsert_bulk(db=db, model=PlayerLeague, payloads=league_to_upsert, unique_key="id")
        
        summary["status"] = "success"
        summary["processed"] = len(players_to_upsert)
        logger.info(f"Ingestão de jogadores concluída com sucesso para a temporada {season}.")
    
    except Exception as e:
        error_msg = f"Erro durante a ingestão de jogadores para a temporada {season}: {e}"
        logger.error(error_msg)
        summary["errors"].append(error_msg)
    
    logger.info(f"Resumo da ingestão de jogadores: {summary}")
    return summary
