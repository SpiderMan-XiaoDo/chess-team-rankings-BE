from flask import Flask, request
from flask_cors import CORS
import requests

from flask_caching import Cache
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.tournament import TnrSearchInput
from utils import make_cache_key
from utils.tournament import get_tnr
from models.error import TournamentNotHaveInfoError
from services import Chessresults_Service
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
    response = requests.post(api_url, data=data, headers=headers)
    if response.status_code == 200:
        chessresults_service = Chessresults_Service()
        html_content = response.text
        tnr_res = get_tnr(html_content)
        res = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for tnr in tnr_res:
                futures.append(executor.submit(chessresults_service.insert_search_tnr_result, tnr=tnr))
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
def getRank():
    data = request.json
    key = data['key']
    if ('round' in data):
        round = str (data['round'])
    else:
        round = None
    if key is None:
        return {
            "message": "Lỗi thiếu tham số"
        }, 500
    try:
        chessresults_service = Chessresults_Service()
        tnr = chessresults_service.get_tnr_result(key, round)
        return {
            "data": tnr
        }
    except Exception as e:
        print(e)
        return {"message": e}, 500

@app.route('/getRanks', methods=['POST'])
def get_ranks():
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
            chessresults_service = Chessresults_Service()
            key = data['key']
            if ('round' in data):
                round = str (data['round'])
            else:
                round = None
            try:
                futures.append(executor.submit(chessresults_service.get_tnr_result, key=key, round=round))
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
    # print(_uri)
    return "Hello"

if __name__ == '__main__':
    app.run(debug=True)

