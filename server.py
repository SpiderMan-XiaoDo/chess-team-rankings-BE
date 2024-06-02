from flask import Flask, request
from flask_cors import CORS
import requests
from utils import *
from utils import get_tnr_current_max_round
import io
from bs4 import BeautifulSoup
from db_service import *
from flask_caching import Cache
import hashlib
from error import TournamentNotHaveInfoError

app = Flask(__name__)
cors = CORS(app)

app.config['CACHE_TYPE'] = 'SimpleCache' 
app.config['CACHE_DEFAULT_TIMEOUT'] = 300 

cache = Cache(app)

def make_cache_key(*args, **kwargs):
    """Tạo khóa cache dựa trên URL và nội dung của yêu cầu POST"""
    data = request.get_data()  # Lấy nội dung của yêu cầu POST
    return hashlib.md5(data).hexdigest()  # Tạo chuỗi hash duy nhất từ nội dung

def getvs(api_url, method = 'GET'):
    s = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}

    if (method == 'GET'):
        response = s.get(api_url, headers=headers)
    else:
        response = s.post(api_url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    viewstate = soup.find(id='__VIEWSTATE').get('value')
    eventvalidation = soup.find(id='__EVENTVALIDATION').get('value')
    viewstategenerator = soup.find(id='__VIEWSTATEGENERATOR').get('value')
    return viewstate, eventvalidation, viewstategenerator

def get_homepage_response(api_url):
    homepage_url = format_chess_results_homepage_link(api_url)
    vs, ev, vsg = getvs(homepage_url)
    data = {
        "__VIEWSTATE": vs,
        "__VIEWSTATEGENERATOR": vsg,
        "__EVENTVALIDATION": ev,
        "cb_alleDetails": "Show tournament details"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*"
    }
    homepage_response = requests.post(homepage_url, data=data, headers=headers)
    return homepage_response

def get_chess_results_excel_rows(excel_url):
    excel_response = requests.get(excel_url)            
    if excel_response.status_code == 200:
        file = io.BytesIO(excel_response.content)
        rows = get_excel_rows(file)
        return rows
    else:
        raise Exception("Không tìm thấy kết quả!")

def get_chess_results_tournament_info(api_url) -> Tournament:
    try:
        homepage_response = get_homepage_response(api_url)
        key = get_tnr_key(api_url)
        if homepage_response.status_code == 200:
            html_content = homepage_response.text
            group_name = get_tnr_group(html_content)
            max_round = get_tnr_round(html_content)
            current_max_round = get_tnr_current_max_round(html_content)
            is_final = int(max_round) == int(current_max_round)
            tnr = Tournament(key, group_name, is_final, current_max_round, max_round, None)
            return tnr
        else:
            raise Exception("Error")
    except:
        raise TournamentNotHaveInfoError()

def get_rank_from_chessreults_when_db_not_exists(api_url, excel_url):
    try:
        tnr_info = get_chess_results_tournament_info(api_url)
        round = tnr_info.current_max_round
        excel_url = excel_url[:-1] + f'{round}'
        rows = get_chess_results_excel_rows(excel_url)
        round_res = TournamentResult(round, rows)
        tnr_info.results = [round_res]
        insert_tnr_info(tnr_info)
        group_name = tnr_info.group_name
        return rows, group_name
    except:
        raise "Error"

def get_rank_from_chessreults_when_db_not_exists2(api_url, excel_url, round):
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
        raise "Error"
    
def get_rank_from_chessresult_when_db_exists(tnr_info: Tournament, excel_url, round):
    excel_url = excel_url[:-1] + f'{round}'
    rows = get_chess_results_excel_rows(excel_url)
    round_res = round_res = TournamentResult(round, rows)
    update_data = Tournament(tnr_info.key, tnr_info.group_name, tnr_info.is_final, tnr_info.current_max_round, tnr_info.max_round)
    update_tnr_info(tnr_info.key, update_data)
    add_round_to_tnr(tournament_key=tnr_info.key, value=round_res)
    return rows

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
            rows, group_name = get_rank_from_chessreults_when_db_not_exists2(api_url=api_url, excel_url=excel_url, round=round)
        tnr = {
            "url": api_url,
            "groupName": group_name,
            "round": round,
            "rows": rows
        }
        return tnr
    except TournamentNotHaveInfoError as e:
        raise TournamentNotHaveInfoError("Error")
    except Exception as e:
        raise e
    
@app.route('/search', methods=['POST'])
@cache.cached(timeout=60, key_prefix='search', make_cache_key=make_cache_key)
def search():
    data = request.json
    name = data['name']
    time_type = data['timeType']
    
    api_url = 'https://chess-results.com/TurnierSuche.aspx?lan=1'
    vs, ev, vsg = getvs(api_url)

    data = {
        "__VIEWSTATE": vs,
        "__VIEWSTATEGENERATOR": vsg,
        "__EVENTVALIDATION": ev,
        "ctl00$P1$txt_bez": name,
        "ctl00$P1$combo_anzahl_zeilen": 0,
        "ctl00$P1$txt_leiter": "",
        "ctl00$P1$cb_suchen": "Search",
        "ctl00$P1$combo_art": 5,
        "ctl00$P1$combo_sort": 1,
        "ctl00$P1$combo_land": "-",
        "ctl00$P1$combo_bedenkzeit": time_type,
        "ctl00$P1$txt_tnr": "",
        "ctl00$P1$txt_veranstalter": "",
        "ctl00$P1$txt_Hauptschiedsrichter": "",
        "ctl00$P1$txt_Schiedsrichter": "",
        "ctl00$P1$txt_ort": "",
        "ctl00$P1$txt_von_tag": "",
        "ctl00$P1$txt_bis_tag": "",
        "ctl00$P1$txt_eventid": ""
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*"
    }
    response = requests.post(api_url, data=data, headers=headers)
    if response.status_code == 200:
        html_content = response.text
        tnr_res = get_tnr(html_content)

        return {
            'data': tnr_res
        }, 200
    return {
        'data': [],
        'message': "Lỗi không xác định!"
    }, 500

@app.route('/getRank', methods=['POST'])
@cache.cached(timeout=600, key_prefix='getRank', make_cache_key=make_cache_key)
def getRank():
    data = request.json
    api_url = data['url']
    if api_url is None:
        return {
            "message": "Lỗi thiếu tham số"
        }, 500
    try:
        tnr = get_tnr_result(api_url)
        return {
            "data": tnr
        }
    except Exception as e:
        print(e)
        return {"message": e}, 500

@app.route('/getRanks', methods=['POST'])
@cache.cached(timeout=600, key_prefix='getRanks', make_cache_key=make_cache_key)
def get_ranks():
    data = request.json
    url_list = data['urls']
    if url_list is None:
        return {
            "message": "Lỗi thiếu tham số!"
        }, 500
    res = []
    for api_url in url_list:
        try:
            tnr = get_tnr_result(api_url)
            res.append(tnr)
        except TournamentNotHaveInfoError as error:
            continue
        except Exception as error:
            return {
                "message": error
            }, 500
    return {
        "data": res
    }, 200

@app.route('/', methods=['GET'])
def index():
    return "Hello"

if __name__ == '__main__':
    app.run(debug=True)

