"""API Server"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request
from flask_cors import CORS
from flask_caching import Cache
import requests

from models.tournament import TnrSearchInput
from models.error import TournamentNotHaveInfoError
from utils import make_cache_key
from utils.tournament import get_tnr
from services import ChessresultsService
from api_urls import SEARCH_URL
from api_urls.utils import getvs

app = Flask(__name__)
cors = CORS(app)

app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

cache = Cache(app)

@app.route('/search', methods=['POST'])
@cache.cached(timeout=60, key_prefix='search', make_cache_key=make_cache_key)
def search():
    """Search tournament"""
    data = request.json
    name = data['name']
    time_type = data['timeType']

    api_url = SEARCH_URL
    vs, ev, vsg = getvs(api_url)

    tnr_search_input = TnrSearchInput(vs, vsg, ev, name, time_type)
    data = tnr_search_input.to_dict()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*"
    }
    response = requests.post(api_url, data=data, headers=headers, timeout=30)
    if response.status_code == 200:
        chessresultsservice = ChessresultsService()
        html_content = response.text
        tnr_res = get_tnr(html_content)
        res = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for tnr in tnr_res:
                futures.append(executor.submit(chessresultsservice.search_tnr, tnr=tnr))
            for future in as_completed(futures):
                res.append(future.result())
        return {
            'data': res
        }, 200
    return {
        'data': [],
        'message': "Lỗi không xác định!"
    }, 500
@app.route('/getRank', methods=['POST'])
# @cache.cached(timeout=600, key_prefix='getRank', make_cache_key=make_cache_key)
def get_rank():
    """Get tournament rank"""
    data = request.json
    key = data['key']
    if 'round' in data:
        rd = str (data['round'])
    else:
        rd = None
    if key is None:
        return {
            "message": "Lỗi thiếu tham số"
        }, 500
    try:
        chessresultsservice = ChessresultsService()
        tnr = chessresultsservice.get_tnr_result(key, rd)
        return {
            "data": tnr
        }
    except Exception as e:
        print(e)
        return {"message": e}, 500

@app.route('/getRanks', methods=['POST'])
def get_ranks():
    """Get tournament rank (multiple)"""
    data = request.json
    data_list = data['datas']
    if data_list is None:
        return {
            "message": "Lỗi thiếu tham số!"
        }, 500
    res = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for data in data_list:
            chessresultsservice = ChessresultsService()
            key = data['key']
            if 'round' in data:
                rd = str (data['round'])
            else:
                rd = None
            try:
                futures.append(executor.submit(chessresultsservice.get_tnr_result, key=key, rd=rd))
            except TournamentNotHaveInfoError as error:
                continue
            except Exception as error:
                return {
                    "message": error
                }, 500
        for future in as_completed(futures):
            tnr = future.result()
            res.append(tnr)
    return {
        "data": res
    }, 200

@app.route('/', methods=['GET'])
def index():
    """Init"""
    # print(_uri)
    return "Hello"

if __name__ == '__main__':
    app.run(debug=True)
