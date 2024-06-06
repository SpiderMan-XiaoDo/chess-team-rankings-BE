from typing import List, TypedDict
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
    def __init__(self, key: str, tnr_name: str, group_name: str, is_final: bool, current_max_round: int, max_round: int, results: List[TournamentResult] = None):
        self.key = key
        self.tnr_name = tnr_name
        self.group_name = group_name
        self.is_final = is_final
        self.current_max_round = current_max_round
        self.results = results
        self.max_round = max_round

    def to_dict(self):
        if (self.results == None):
            results = []
        else:
            results = [obj.to_dict() for obj in self.results]
        return {
            "key": self.key,
            "tnrName": self.tnr_name,
            "groupName": self.group_name,
            "isFinal": self.is_final,
            "currentMaxRound": self.current_max_round,
            "maxRound": self.max_round,
            "results": results
        }
    
    def get_update_data_dict(self):
        update_data = {
            "isFinal": self.is_final,
            "currentMaxRound": self.current_max_round,
            "maxRound": self.max_round,
        }
        return update_data
    
class TnrSearchOutput(TypedDict):
    name: str
    url: str

class TnrSearchInput():
    def __init__(self, vs, vsg, ev, name, time_type):
        self.vs = vs
        self.vsg = vsg
        self.ev = ev
        self.name = name
        self.time_type = time_type
    def to_dict(self):
        data = {
            "__VIEWSTATE": self.vs,
            "__VIEWSTATEGENERATOR": self.vsg,
            "__EVENTVALIDATION": self.ev,
            "ctl00$P1$txt_bez": self.name,
            "ctl00$P1$combo_anzahl_zeilen": 0,
            "ctl00$P1$txt_leiter": "",
            "ctl00$P1$cb_suchen": "Search",
            "ctl00$P1$combo_art": 5,
            "ctl00$P1$combo_sort": 1,
            "ctl00$P1$combo_land": "-",
            "ctl00$P1$combo_bedenkzeit": self.time_type,
            "ctl00$P1$txt_tnr": "",
            "ctl00$P1$txt_veranstalter": "",
            "ctl00$P1$txt_Hauptschiedsrichter": "",
            "ctl00$P1$txt_Schiedsrichter": "",
            "ctl00$P1$txt_ort": "",
            "ctl00$P1$txt_von_tag": "",
            "ctl00$P1$txt_bis_tag": "",
            "ctl00$P1$txt_eventid": ""
        }
        return data
    
class TnrHomepageInput():
    def __init__(self, vs, vsg, ev):
        self.vs = vs
        self.vsg = vsg
        self.ev = ev

    def to_dict(self):
        data = {
            "__VIEWSTATE": self.vs,
            "__VIEWSTATEGENERATOR": self.vsg,
            "__EVENTVALIDATION": self.ev,
            "cb_alleDetails": "Show tournament details"
        }
        return data
    
    def get_headers(self):
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*"
        }