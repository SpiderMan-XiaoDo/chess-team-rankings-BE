"""Mongo DB Service"""
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from models.tournament import Tournament, TournamentResult
from models.error import DatabaseError, DATABASE_ERROR_MESSAGE
from .base_db_service import BaseDBService

_uri = os.getenv("MONGO_URI")
TOURNAMENT_DB = "TournamentDB"
TOURNAMENT_COLLECTION = "tournament"
KEY_FIELD = "key"

class MongoDBService(BaseDBService):
    """Mongo DB Service"""
    def __init__(self):
        super(BaseDBService).__init__()

    def __get_db(self):
        client = MongoClient(_uri, server_api=ServerApi('1'))
        db = client[TOURNAMENT_DB]
        return db

    def insert_tnr_info(self, tnr: Tournament):
        try:
            db = self.__get_db()
            tournament_collection = db[TOURNAMENT_COLLECTION]
            tnr_id = tournament_collection.insert_one(tnr.to_dict()).inserted_id
            return tnr_id
        except Exception as exc:
            raise DatabaseError(DATABASE_ERROR_MESSAGE) from exc

    def add_round_to_tnr(self, tournament_key: str, value: TournamentResult):
        try:
            db = self.__get_db()
            tournament_collection = db[TOURNAMENT_COLLECTION]
            tnr_filter = {KEY_FIELD: tournament_key}
            data = {"results": {"round": value.round, "rows": value.rows}}
            update_operation = {"$push": data}
            tournament_collection.update_one(tnr_filter, update_operation)
        except Exception as exc:
            raise DatabaseError(DATABASE_ERROR_MESSAGE) from exc

    def update_tnr_info(self, tournament_key: str, tnr: Tournament):
        try:
            db = self.__get_db()
            tournament_collection = db[TOURNAMENT_COLLECTION]
            tnr_filter = {KEY_FIELD: tournament_key}
            update_data = tnr.get_update_data_dict()
            update_operation = {"$set": update_data}
            tournament_collection.update_one(tnr_filter, update_operation)
        except Exception as exc:
            raise DatabaseError(DATABASE_ERROR_MESSAGE) from exc

    def get_tnr(self, tournament_key: str, rd: int = None) -> Tournament:
        try:
            db = self.__get_db()
            tournament_collection = db[TOURNAMENT_COLLECTION]
            if rd is None:
                res = tournament_collection.find_one({KEY_FIELD: tournament_key})
            else:
                res = tournament_collection.find_one({
                    "key": tournament_key,
                    "results": { "$elemMatch": {"round": rd} }
                })
            tnr = Tournament.from_dict(res)
            return tnr
        except Exception as exc:
            raise DatabaseError(DATABASE_ERROR_MESSAGE) from exc
