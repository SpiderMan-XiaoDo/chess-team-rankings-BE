"""DB Service Interface"""
from models.tournament import Tournament, TournamentResult

class BaseDBService:
    """Base DB Service"""
    def insert_tnr_info(self, tnr: Tournament):
        """Insert tournament"""

    def add_round_to_tnr(self, tournament_key: str, value: TournamentResult):
        """Insert round to tournament"""

    def update_tnr_info(self, tournament_key: str, tnr: Tournament):
        """Update tournament info"""

    def get_tnr(self, tournament_key: str, rd: int = None):
        """Get tournament"""
