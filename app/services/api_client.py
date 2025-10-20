import requests
import logging
import time
from typing import List, Dict, Any, Optional

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, retries: int = 3) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}"
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                # Verifica se a resposta foi bem-sucedida (código 2xx)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Tentativa {attempt + 1} falhou para {url}: {e}")
                attempt += 1
                time.sleep(10) # Espera 10 segundo antes de tentar novamente
        
        logger.error(f"Todas as {retries} tentativas falharam para o endpoint {endpoint}.")
        return None

    def get_seasons(self) -> Optional[List[int]]:
        data = self.get("seasons")
        return data.get("response") if data else None

    def get_leagues(self) -> Optional[List[Dict[str, Any]]]:
        data = self.get("leagues")
        return data.get("response") if data else None

    def get_teams(self) -> Optional[List[Dict[str, Any]]]:
        data = self.get("teams")
        return data.get("response") if data else None

    def get_team_statistics(self, team_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
        params = {"id": team_id, "season": season}
        data = self.get("teams/statistics", params=params)
        return data.get("response") if data else None

    def get_players(self, team_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
        params = {"team": team_id, "season": season}
        data = self.get("players", params=params)
        return data.get("response") if data else None

    def get_player_statistics(self, player_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
        params = {"id": player_id, "season": season}
        data = self.get("players/statistics", params=params)
        return data.get("response") if data else None

    def get_games(self, date: str) -> Optional[List[Dict[str, Any]]]:
        params = {"date": date}
        data = self.get("games", params=params)
        return data.get("response") if data else None

    def get_game_statistics(self, game_id: int) -> Optional[List[Dict[str, Any]]]:
        params = {"id": game_id}
        data = self.get("games/statistics", params=params)
        return data.get("response") if data else None

    def get_standings(self, league_source_id: int, season: int) -> Optional[List[Dict[str, Any]]]:
        params = {"league": league_source_id, "season": season}
        data = self.get("standings", params=params)
        return data.get("response") if data else None
