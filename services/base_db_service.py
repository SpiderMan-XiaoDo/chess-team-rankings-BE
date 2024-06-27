from models.tournament import Tournament, TournamentResult

class BaseDBService:
    def insert_tnr_info(self, tnr: Tournament):
        pass

    def add_round_to_tnr(self, tournament_key: str, value: TournamentResult):
        pass

    def update_tnr_info(self, tournament_key: str, tnr: Tournament):
        pass

    def get_tnr(self, tournament_key: str, round: int = None):
        pass