from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from Tournament import Tournament, TournamentResult
import os

uri = os.getenv("MONGO_URI")

def get_db():
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["TournamentDB"]
    return db

def insert_tnr_info(tnr: Tournament):
    try:
        db = get_db()
        tournament_collection = db.tournament
        if (tnr.results == None):
            results = []
        else:
            results = [obj.to_dict() for obj in tnr.results]
        id = tournament_collection.insert_one({
            "key": tnr.key,
            "tnrName": tnr.tnr_name,
            "groupName": tnr.group_name,
            "isFinal": tnr.is_final,
            "currentMaxRound": tnr.current_max_round,
            "maxRound": tnr.max_round,
            "results": results
        }).inserted_id
        return id
    except:
        raise "Error"

def add_round_to_tnr(tournament_key: str, value: TournamentResult):
    try:
        db = get_db()
        tournament_collection = db.tournament
        filter = {"key": tournament_key}
        data = {"results": {"round": value.round, "rows": value.rows}}
        update_operation = {"$push": data}
        res = tournament_collection.update_one(filter, update_operation)
    except:
        raise "Error"

def update_tnr_info(tournament_key: str, tnr: Tournament):
    try:
        db = get_db()
        tournament_collection = db.tournament
        filter = {"key": tournament_key}
        update_data = {
            "isFinal": tnr.is_final,
            "currentMaxRound": tnr.current_max_round,
            "maxRound": tnr.max_round,
        }
        update_operation = {"$set": update_data}
        res = tournament_collection.update_one(filter, update_operation)
    except:
        raise "Error"

def find_db_have_tournament(tournament_key: str):
    try:
        db = get_db()
        tournament_collection = db.tournament
        res = tournament_collection.find_one({"key": tournament_key})
        return res
    except:
        raise "Error"

def find_db_have_tournament_with_round(tournament_key: str, round: int):
    try:
        db = get_db()
        tournament_collection = db.tournament
        res = tournament_collection.find_one({
            "key": tournament_key,
            "results": { "$elemMatch": {"round": round} }
        })
        return res
    except:
        raise "Error"
