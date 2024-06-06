from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from models.tournament import Tournament, TournamentResult
from models.error import DatabaseError, DATABASE_ERROR_MESSAGE
import os

_uri = os.getenv("MONGO_URI")
TOURNAMENT_DB = "TournamentDB"
TOURNAMENT_COLLECTION = "tournament"
KEY_FIELD = "key"

def get_db():
    client = MongoClient(_uri, server_api=ServerApi('1'))
    db = client[TOURNAMENT_DB]
    return db

def insert_tnr_info(tnr: Tournament):
    try:
        db = get_db()
        tournament_collection = db[TOURNAMENT_COLLECTION]
        id = tournament_collection.insert_one(tnr.to_dict()).inserted_id
        return id
    except:
        raise DatabaseError(DATABASE_ERROR_MESSAGE)

def add_round_to_tnr(tournament_key: str, value: TournamentResult):
    try:
        db = get_db()
        tournament_collection = db[TOURNAMENT_COLLECTION]
        filter = {KEY_FIELD: tournament_key}
        data = {"results": {"round": value.round, "rows": value.rows}}
        update_operation = {"$push": data}
        res = tournament_collection.update_one(filter, update_operation)
    except:
        raise DatabaseError(DATABASE_ERROR_MESSAGE)

def update_tnr_info(tournament_key: str, tnr: Tournament):
    try:
        db = get_db()
        tournament_collection = db[TOURNAMENT_COLLECTION]
        filter = {KEY_FIELD: tournament_key}
        update_data = tnr.get_update_data_dict()
        update_operation = {"$set": update_data}
        res = tournament_collection.update_one(filter, update_operation)
    except:
        raise DatabaseError(DATABASE_ERROR_MESSAGE)

def find_db_have_tournament(tournament_key: str):
    try:
        db = get_db()
        tournament_collection = db[TOURNAMENT_COLLECTION]
        res = tournament_collection.find_one({KEY_FIELD: tournament_key})
        return res
    except:
        raise DatabaseError(DATABASE_ERROR_MESSAGE)

def find_db_have_tournament_with_round(tournament_key: str, round: int):
    try:
        db = get_db()
        tournament_collection = db[TOURNAMENT_COLLECTION]
        res = tournament_collection.find_one({
            "key": tournament_key,
            "results": { "$elemMatch": {"round": round} }
        })
        return res
    except:
        raise DatabaseError(DATABASE_ERROR_MESSAGE)
