from typing import List
import json

class TournamentResult: 
    def __init__(self, round: int, rows: List):
        self.round = round
        self.rows = rows
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
    
    def to_dict(self):
        return {
            "round": self.round,
            "rows": self.rows
        }

class Tournament:
    def __init__(self, key: str, group_name: str, is_final: bool, current_max_round: int, max_round: int, results: List[TournamentResult] = None):
        self.key = key
        self.group_name = group_name
        self.is_final = is_final
        self.current_max_round = current_max_round
        self.results = results
        self.max_round = max_round
