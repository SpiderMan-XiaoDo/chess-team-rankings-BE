"""Chessresults Service"""
import io
from typing import Tuple
import requests
# from functools import lru_cache
# import time
from api_urls.utils import getvs
from api_urls import BASE_API_URL
from models.tournament import TnrHomepageInput, Tournament, TournamentResult, TnrSearchOutput
from models.error import (DatabaseError,
                            TournamentNotHaveInfoError,
                            CHESSRESULTS_CONNECT_ERROR_MSG,
                            NOT_FOUND_CHESSRESULTS_XLSX_FILE_MESSAGE)
from utils.xlsx import get_excel_rows
from utils.tournament import (get_tnr_key,
                                get_chess_results_tournament_info_from_html,
                                get_chess_result_link_from_key_and_round,
                                get_chess_results_excel_link,
                                get_chess_results_homepage_link)
from services import DBService
from config import DB_TYPE

class ChessresultsService:
    """Chessresults service"""
    def __init__(self) -> None:
        self.db_service = DBService(DB_TYPE)

    def __get_tnr_homepage_response(self, key: str) -> str:
        try:
            homepage_url = get_chess_results_homepage_link(key)
            vs, ev, vsg = getvs(homepage_url)
            tnr_homepage_input = TnrHomepageInput(vs, vsg, ev)
            data = tnr_homepage_input.to_dict()
            headers = tnr_homepage_input.get_headers()
            homepage_response = requests.post(homepage_url, data=data, headers=headers, timeout=20)
            if homepage_response.status_code == 200:
                return homepage_response.text
            raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG)
        except Exception as e:
            raise e

    def __get_chess_results_excel_rows(self, excel_url) -> list:
        excel_response = requests.get(excel_url, timeout=20)
        if excel_response.status_code == 200:
            file = io.BytesIO(excel_response.content)
            rows = get_excel_rows(file)
            return rows
        raise DatabaseError(NOT_FOUND_CHESSRESULTS_XLSX_FILE_MESSAGE)

    def __get_chess_results_tournament_info(self, key: str) -> Tournament:
        try:
            tnr_html_content = self.__get_tnr_homepage_response(key)
            tnr = get_chess_results_tournament_info_from_html(key, tnr_html_content)
            return tnr
        except Exception as e:
            raise e

    def __get_rank_from_chessresults(self, key: str, rd) -> Tuple[list, str]:
        try:
            excel_url = get_chess_results_excel_link(key, rd)
            rows = self.__get_chess_results_excel_rows(excel_url)
            return rows
        except Exception as exc:
            raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG) from exc

    def __insert_tnr_to_db(self, key: str, rd, rows: list) -> Tournament:
        try:
            tnr_info = self.__get_chess_results_tournament_info(key)
            round_res = TournamentResult(rd, rows)
            tnr_info.results = [round_res]
            self.db_service.insert_tnr_info(tnr_info)
            return tnr_info
        except Exception as exc:
            raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG) from exc

    def __update_tnr_to_db(self, tnr_info: Tournament, rd, rows) -> Tournament:
        round_res = round_res = TournamentResult(rd, rows)
        update_data = Tournament(tnr_info.key,
                                 tnr_info.url,
                                 tnr_info.tnr_name,
                                 tnr_info.group_name,
                                 tnr_info.is_final,
                                 tnr_info.current_max_round,
                                 tnr_info.max_round)
        self.db_service.update_tnr_info(tnr_info.key, update_data)
        self.db_service.add_round_to_tnr(tournament_key=tnr_info.key, value=round_res)
        return rows

    # @lru_cache(maxsize=1024)
    def __get_tnr_result_from_key_and_round(self, key: str, rd: int, db_tnr: Tournament = None):
        try:
            api_url = get_chess_result_link_from_key_and_round(key, rd)
            if db_tnr is not None:
                if db_tnr.results is not None:
                    round_res = next((obj for obj in db_tnr.results if obj.round == rd), None)
                else:
                    round_res = None
                if round_res is not None:
                    print('case 1')
                    # Case1: Get from DB
                    rows = round_res.rows
                else:
                    print('case 2')
                    # Case2: Get from chessresults when DB exist tournament
                    tnr_info = self.__get_chess_results_tournament_info(key)
                    rows = self.__get_rank_from_chessresults(key=key, rd=rd)
                    self.__update_tnr_to_db(tnr_info=tnr_info, rd=rd, rows=rows)
                group_name = db_tnr.group_name
                tnr_name = db_tnr.tnr_name
            else:
                print('case 3')
                # Case3: Get from chessresults when DB not exist tournament
                rows = self.__get_rank_from_chessresults(key=key, rd=rd)
                tnr_info = self.__insert_tnr_to_db(key, rd, rows)
                group_name = tnr_info.group_name
                tnr_name = tnr_info.tnr_name
            tnr = {
                "url": api_url,
                "groupName": group_name,
                "tnrName": tnr_name,
                "round": rd,
                "rows": rows
            }
            return tnr
        except Exception as e:
            raise e

    def get_tnr_result(self, key: str, rd: int = None):
        """Get tournament result"""
        try:
            db_tnr = self.db_service.get_tnr(tournament_key=key, rd=rd)
            if rd is None:
                if db_tnr is not None:
                    if db_tnr.is_final is True:
                        rd = db_tnr.max_round
                    else:
                        tnr_info = self.__get_chess_results_tournament_info(key)
                        rd = tnr_info.current_max_round
                else:
                    tnr_info = self.__get_chess_results_tournament_info(key)
                    rd = tnr_info.current_max_round
            tnr = self.__get_tnr_result_from_key_and_round(key=key, rd=rd, db_tnr=db_tnr)
            return tnr
        except TournamentNotHaveInfoError as e:
            raise TournamentNotHaveInfoError("Error") from e
        except Exception as e:
            raise e

    def search_tnr(self, tnr: TnrSearchOutput):
        """Search tournament"""
        try:
            api_url = f"{BASE_API_URL}/{tnr['url']}"
            key = get_tnr_key(api_url)
            db_tnr = self.db_service.get_tnr(key)
            if db_tnr:
                print('Case1')
                res: TnrSearchOutput = {
                    "url": db_tnr.url,
                    "name": db_tnr.tnr_name,
                    'groupName': db_tnr.group_name
                }
            else:
                print('Case2')
                tnr_info = self.__get_chess_results_tournament_info(key)
                self.db_service.insert_tnr_info(tnr_info)
                res: TnrSearchOutput = {
                    "url": tnr_info.url,
                    "name": tnr_info.tnr_name,
                    'groupName': tnr_info.group_name
                }
            return res
        except Exception as e:
            raise e
