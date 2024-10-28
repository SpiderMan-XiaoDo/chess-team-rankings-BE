"""API Utilities function"""
import requests
from bs4 import BeautifulSoup
from models.error import DatabaseError, CHESSRESULTS_CONNECT_ERROR_MSG
from .. import VS, EV, VSG

def getvs(api_url, method = 'GET'):
    """Get view state, event validation, view state generator"""
    try:
        s = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0'}

        if method == 'GET':
            response = s.get(api_url, headers=headers)
        else:
            response = s.post(api_url, headers=headers)
        soup = BeautifulSoup(response.content, 'lxml')
        viewstate = soup.find(id=VS).get('value')
        eventvalidation = soup.find(id=EV).get('value')
        viewstategenerator = soup.find(id=VSG).get('value')
        return viewstate, eventvalidation, viewstategenerator
    except Exception as exc:
        raise DatabaseError(CHESSRESULTS_CONNECT_ERROR_MSG) from exc
