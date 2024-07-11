from models.tournament import Tournament, TournamentResult
from models.error import DatabaseError, DATABASE_ERROR_MESSAGE
from .base_db_service import BaseDBService
import os
import json

KEY_FIELD = "key"
JSON_DIR_PATH = "db_json"

class JSONFileDBService(BaseDBService):
    def __init__(self) -> None:
        super().__init__()
        os.makedirs(JSON_DIR_PATH, exist_ok=True)

    def __read_json_file_tnr_content(self, key):
        try:
            with open(os.path.join(JSON_DIR_PATH, f'{key}.json'), 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            return json_data
        except:
            raise DatabaseError(DATABASE_ERROR_MESSAGE)

    def __write_json_file_tnr_content(self, key, json_data):
        print(json_data)
        try:
            with open(os.path.join(JSON_DIR_PATH, f'{key}.json'), 'w', encoding='utf-8') as file:
                json.dump(json_data, file, ensure_ascii=False)
        except:
            raise DatabaseError(DATABASE_ERROR_MESSAGE)

    def insert_tnr_info(self, tnr: Tournament):
        try:
            json_data = tnr.to_dict()
            self.__write_json_file_tnr_content(tnr.key, json_data)
        except:
            raise DatabaseError(DATABASE_ERROR_MESSAGE)

    def add_round_to_tnr(self, tournament_key: str, value: TournamentResult):
        try:
            json_data = self.__read_json_file_tnr_content(tournament_key)
            new_round = {
                "round": value.round,
                "rows": value.rows
            }
            if 'results' in json_data:
                json_data['results'].append(new_round)
            else:
                json_data |= {'results': [new_round]}
            self.__write_json_file_tnr_content(tournament_key, json_data)
        except:
            raise DatabaseError(DATABASE_ERROR_MESSAGE)

    def update_tnr_info(self, tournament_key: str, tnr: Tournament):
        try:
            json_data = self.__read_json_file_tnr_content(tournament_key)
            update_data = tnr.get_update_data_dict()
            json_data |= update_data
            self.__write_json_file_tnr_content(tournament_key, json_data)
        except:
            raise DatabaseError(DATABASE_ERROR_MESSAGE)

    def get_tnr(self, tournament_key: str, round: int = None) -> Tournament:
        try:
            if os.path.exists(os.path.join(JSON_DIR_PATH, f'{tournament_key}.json')):
                json_data = self.__read_json_file_tnr_content(tournament_key)
                if (round is None):
                    tnr = Tournament.from_dict(json_data)
                else:
                    if 'results' not in json_data:
                        return None
                    result = any(d.get('round') == round for d in json_data['results'])
                    if (result):
                        tnr = Tournament.from_dict(json_data)
                return tnr
            else: 
                return None
        except:
            raise DatabaseError(DATABASE_ERROR_MESSAGE)
