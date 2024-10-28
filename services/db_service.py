"""DB Service"""
from models.tournament import Tournament, TournamentResult
from models.db import DBServiceType
from .mongo_db_service import MongoDBService
from .json_file_db_service import JSONFileDBService
from .base_db_service import BaseDBService

class DBService(BaseDBService):
    """DB Service"""
    def __init__(self, db_type: DBServiceType = DBServiceType.JSON_FILE):
        if db_type == DBServiceType.JSON_FILE:
            self.db_service = JSONFileDBService()
        else:
            self.db_service = MongoDBService()

    def insert_tnr_info(self, tnr: Tournament):
        try:
            return self.db_service.insert_tnr_info(tnr)
        except Exception as e:
            raise e

    def add_round_to_tnr(self, tournament_key: str, value: TournamentResult):
        try:
            return self.db_service.add_round_to_tnr(tournament_key, value)
        except Exception as e:
            raise e

    def update_tnr_info(self, tournament_key: str, tnr: Tournament):
        try:
            return self.db_service.update_tnr_info(tournament_key, tnr)
        except Exception as e:
            raise e

    def get_tnr(self, tournament_key: str, rd: int = None) -> Tournament:
        try:
            return self.db_service.get_tnr(tournament_key, rd)
        except Exception as e:
            raise e
