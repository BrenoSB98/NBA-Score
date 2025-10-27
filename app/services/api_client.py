import requests
import logging
import time
from typing import Dict, Any, Optional

from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
class ApiClient:
    
    def __init__(self):
        self.base_url = f"https://{settings.nba_api_host}"
        self.api_key = settings.nba_api_key
        if not self.api_key:
            raise ValueError("A chave da API (NBA_API_KEY) não foi configurada no .env")
        
        self.headers = {
            "x-rapidapi-host": settings.nba_api_host,
            "x-rapidapi-key": self.api_key
        }

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, retries: int = 3):
        url = f"{self.base_url}/{endpoint}"
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if data and "response" in data:
                    return data["response"]
                else:
                    logger.warning(f"Resposta da API para {url} com params {params} não continha a chave 'response'.")
                    return None          
            except requests.exceptions.RequestException as e:
                logger.error(f"Tentativa {attempt + 1} falhou para {url}: {e}")
                attempt += 1
                time.sleep(10)
        
        logger.error(f"Todas as {retries} tentativas falharam para o endpoint {endpoint}.")
        return None

    def get_seasons(self):
        return self.get("seasons")

    def get_leagues(self):
        return self.get("leagues")

    def get_teams(self):
        return self.get("teams")

    def get_team_statistics(self, team_id: int, season: int):
        params = {"id": team_id, "season": season}
        return self.get("teams/statistics", params=params)

    def get_players(self, team_id: int, season: int):
        params = {"team": team_id, "season": season}
        return self.get("players", params=params)

    def get_player_statistics(self, player_id: int, season: int):
        params = {"id": player_id, "season": season}
        return self.get("players/statistics", params=params)

    def get_games(self, date: str):
        params = {"date": date}
        return self.get("games", params=params)

    def get_game_statistics(self, game_id: int):
        params = {"id": game_id}
        return self.get("games/statistics", params=params)

    def get_standings(self, league_source_id: int, season: int):
        params = {"league": league_source_id, "season": season}
        return self.get("standings", params=params)
