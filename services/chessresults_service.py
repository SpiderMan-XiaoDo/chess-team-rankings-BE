from typing import Tuple
from utils.tournament import format_chess_results_homepage_link
from api_urls.utils import getvs
from api_urls import BASE_API_URL
from models.tournament import TnrHomepageInput, Tournament, TournamentResult, TnrSearchOutput
from models.error import DatabaseError, TournamentNotHaveInfoError, CHESSRESULTS_CONNECT_ERROR_MSG, NOT_FOUND_CHESSRESULTS_XLSX_FILE_MESSAGE
from utils import find_object_with_key_value
from utils.xlsx import get_excel_rows
from utils.tournament import get_tnr_key, get_tnr_name, get_tnr_group, get_tnr_round, get_tnr_current_max_round, get_chess_result_link_from_key_and_round, format_chess_results_excel_link
from services.db_service import insert_tnr_info, update_tnr_info, add_round_to_tnr, find_db_have_tournament
import requests
import io
from functools import lru_cache

def get_tnr_homepage_response(api_url) -> str:
    try:
        homepage_url = format_chess_results_homepage_link(api_url)
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
    
def get_chess_results_tournament_info(api_url) -> Tournament:
    try:
        key = get_tnr_key(api_url)
        tnr_html_content = get_tnr_homepage_response(api_url)
        tnr_name = get_tnr_name(tnr_html_content)
        group_name = get_tnr_group(tnr_html_content)
        max_round = get_tnr_round(tnr_html_content)
        current_max_round = get_tnr_current_max_round(tnr_html_content)
        if (max_round != None and current_max_round != None):
            is_final = int(max_round) == int(current_max_round)
        else:
            is_final = False
        tnr = Tournament(key, tnr_name, group_name, is_final, current_max_round, max_round, None)
        return tnr
    except:
        raise TournamentNotHaveInfoError()
    
def get_rank_from_chessreults_when_db_not_exists(api_url, excel_url, round) -> Tuple[list, str]:
    try:
        tnr_info = get_chess_results_tournament_info(api_url)
        excel_url = excel_url[:-1] + f'{round}'
        rows = get_chess_results_excel_rows(excel_url)
        round_res = TournamentResult(round, rows)
        tnr_info.results = [round_res]
        insert_tnr_info(tnr_info)
        group_name = tnr_info.group_name
        return rows, group_name
    except:
        raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG)
    
def get_rank_from_chessresult_when_db_exists(tnr_info: Tournament, excel_url, round) -> list:
    try:
        excel_url = excel_url[:-1] + f'{round}'
        rows = get_chess_results_excel_rows(excel_url)
        round_res = round_res = TournamentResult(round, rows)
        update_data = Tournament(tnr_info.key, tnr_info.tnr_name, tnr_info.group_name, tnr_info.is_final, tnr_info.current_max_round, tnr_info.max_round)
        update_tnr_info(tnr_info.key, update_data)
        add_round_to_tnr(tournament_key=tnr_info.key, value=round_res)
        return rows
    except:
        raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG)
    
@lru_cache(maxsize=1024)
def get_tnr_result_from_key_and_round(key: str, round: int):
    try:
        db_tnr = find_db_have_tournament(tournament_key=key)
        api_url = get_chess_result_link_from_key_and_round(key, round)
        excel_url, _, _ = format_chess_results_excel_link(api_url)
        if (db_tnr):
            round_res = find_object_with_key_value(db_tnr['results'], "round", round)
            if (round_res != None):
                # Case1: Get from DB
                rows = round_res['rows']
            else:
                # Case2: Get from chessresults when DB exist tournament
                tnr_info = get_chess_results_tournament_info(api_url)
                rows = get_rank_from_chessresult_when_db_exists(tnr_info, excel_url, round)
            group_name = db_tnr['groupName']
        else:
            # Case3: Get from chessresults when DB not exist tournament
            rows, group_name = get_rank_from_chessreults_when_db_not_exists(api_url=api_url, excel_url=excel_url, round=round)
        tnr = {
            "url": api_url,
            "groupName": group_name,
            "round": round,
            "rows": rows
        }
        return tnr
    except Exception as e:
        raise "Error"
    
def get_tnr_result(api_url):
    try:
        excel_url, have_round, round = format_chess_results_excel_link(api_url)
        key = get_tnr_key(api_url)
        db_tnr = find_db_have_tournament(tournament_key=key)
        if (have_round == False):
            if (db_tnr):
                if (db_tnr['isFinal'] == True):
                    round = db_tnr['maxRound']
                else:
                    tnr_info = get_chess_results_tournament_info(api_url)
                    round = tnr_info.current_max_round
            else:
                tnr_info = get_chess_results_tournament_info(api_url)
                round = tnr_info.current_max_round
        tnr = get_tnr_result_from_key_and_round(key, round)
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
        tnr_info = get_chess_results_tournament_info(api_url)
        insert_tnr_info(tnr_info)
        res = {
            "url": tnr['url'],
            "name": tnr_info.tnr_name
        }
    return res