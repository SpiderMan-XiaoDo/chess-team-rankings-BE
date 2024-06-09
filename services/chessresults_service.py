from typing import Tuple
from api_urls.utils import getvs
from api_urls import BASE_API_URL
from models.tournament import TnrHomepageInput, Tournament, TournamentResult, TnrSearchOutput
from models.error import DatabaseError, TournamentNotHaveInfoError, CHESSRESULTS_CONNECT_ERROR_MSG, DATABASE_ERROR_MESSAGE, NOT_FOUND_CHESSRESULTS_XLSX_FILE_MESSAGE
from utils.xlsx import get_excel_rows
from utils.tournament import get_tnr_key, get_chess_results_tournament_info_from_html, get_chess_result_link_from_key_and_round, get_chess_results_excel_link, get_chess_results_homepage_link
from services.db_service import insert_tnr_info, update_tnr_info, add_round_to_tnr, find_db_have_tournament
import requests
import io
from functools import lru_cache

def get_tnr_homepage_response(key: str) -> str:
    try:
        homepage_url = get_chess_results_homepage_link(key)
        vs, ev, vsg = getvs(homepage_url)
        tnr_homepage_input = TnrHomepageInput(vs, ev, vsg)
        data = tnr_homepage_input.to_dict()
        headers = tnr_homepage_input.get_headers()
        homepage_response = requests.post(homepage_url, data=data, headers=headers)
        if (homepage_response.status_code == 200):
            return homepage_response.text
        else:
            raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG)
    except Exception as e:
        raise e
    
def get_chess_results_excel_rows(excel_url) -> list:
    excel_response = requests.get(excel_url)            
    if excel_response.status_code == 200:
        file = io.BytesIO(excel_response.content)
        rows = get_excel_rows(file)
        return rows
    else:
        raise DatabaseError(NOT_FOUND_CHESSRESULTS_XLSX_FILE_MESSAGE)
    
def get_chess_results_tournament_info(key: str) -> Tournament:
    try:
        tnr_html_content = get_tnr_homepage_response(key)
        tnr = get_chess_results_tournament_info_from_html(tnr_html_content)
        return tnr
    except Exception as e:
        raise e
    
def get_rank_from_chessreults_when_db_not_exists(key: str, round) -> Tuple[list, str]:
    try:
        excel_url = get_chess_results_excel_link(key, round)
        rows = get_chess_results_excel_rows(excel_url)
        return rows
    except:
        raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG)
    
def get_rank_from_chessresult_when_db_exists(key: str, round) -> list:
    try:
        excel_url = get_chess_results_excel_link(key, round)
        rows = get_chess_results_excel_rows(excel_url)
        return rows
    except:
        raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG)
    
def insert_tnr_to_db(key: str, round, rows: list) -> Tournament:
    try:
        tnr_info = get_chess_results_tournament_info(key)
        round_res = TournamentResult(round, rows)
        tnr_info.results = [round_res]
        insert_tnr_info(tnr_info)
        return tnr_info
    except:
        raise DatabaseError(DATABASE_ERROR_MESSAGE)

def update_tnr_to_db(tnr_info: Tournament, round, rows) -> Tournament:
    round_res = round_res = TournamentResult(round, rows)
    update_data = Tournament(tnr_info.key, tnr_info.tnr_name, tnr_info.group_name, tnr_info.is_final, tnr_info.current_max_round, tnr_info.max_round)
    update_tnr_info(tnr_info.key, update_data)
    add_round_to_tnr(tournament_key=tnr_info.key, value=round_res)
    return rows

@lru_cache(maxsize=1024)
def get_tnr_result_from_key_and_round(key: str, round: int, db_tnr: Tournament = None):
    try:
        api_url = get_chess_result_link_from_key_and_round(key, round)
        excel_url = get_chess_results_excel_link(key, round)
        if (db_tnr != None):
            if (db_tnr.results != None):
                round_res = next((obj for obj in db_tnr.results if obj.round == round), None)
            else:
                round_res = None
            if (round_res != None):
                print('case 1')
                # Case1: Get from DB
                rows = round_res.rows
            else:
                print('case 2')
                # Case2: Get from chessresults when DB exist tournament
                tnr_info = get_chess_results_tournament_info(key)
                rows = get_rank_from_chessresult_when_db_exists(key=key, round=round)
                update_tnr_to_db(tnr_info=tnr_info, round=round, rows=rows)
            group_name = db_tnr.group_name
        else:
            print('case 3')
            # Case3: Get from chessresults when DB not exist tournament
            rows = get_rank_from_chessreults_when_db_not_exists(key=key, excel_url=excel_url, round=round)
            tnr_info = insert_tnr_to_db(key, round, rows)
            group_name = tnr_info.group_name
        tnr = {
            "url": api_url,
            "groupName": group_name,
            "round": round,
            "rows": rows
        }
        return tnr
    except Exception as e:
        raise e
    
def get_tnr_result(key: str, round: int = None):
    try:
        db_tnr = find_db_have_tournament(tournament_key=key)
        if (round == None):
            if (db_tnr != None):
                if (db_tnr['isFinal'] == True):
                    round = db_tnr['maxRound']
                else:
                    tnr_info = get_chess_results_tournament_info(key)
                    round = tnr_info.current_max_round
            else:
                tnr_info = get_chess_results_tournament_info(key)
                round = tnr_info.current_max_round
        db_tnr_temp = Tournament.from_dict(db_tnr)
        tnr = get_tnr_result_from_key_and_round(key=key, round=round, db_tnr=db_tnr_temp)
        return tnr
    except TournamentNotHaveInfoError as e:
        raise TournamentNotHaveInfoError("Error")
    except Exception as e:
        raise e
    
def insert_search_tnr_result(tnr: TnrSearchOutput):
    api_url = f"{BASE_API_URL}/{tnr['url']}"
    key = get_tnr_key(api_url)
    db_tnr = find_db_have_tournament(key)
    if (db_tnr):
        print('Case1')
        res = {
            "url": tnr['url'],
            "name": db_tnr['tnrName']
        }
    else:
        print('Case2')
        tnr_info = get_chess_results_tournament_info(key)
        insert_tnr_info(tnr_info)
        res = {
            "url": tnr['url'],
            "name": tnr_info.tnr_name
        }
    return res