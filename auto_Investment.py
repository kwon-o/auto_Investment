import requests
import json
import pprint
import urllib.request
import datetime
import pandas as pd


def get_token():
    with open('auth.json', 'r') as f:
        auth = json.load(f)

    headers = {'content-type': 'application/json'}
    json_data = json.dumps(
        {'APIPassword': auth['APIPassword'], }
    ).encode('utf8')
    url = 'http://localhost:18080/kabusapi/token'

    response = requests.post(url, data=json_data, headers=headers)

    return json.loads(response.text)['Token']


def get_current_price(code):
    url = 'http://localhost:18080/kabusapi/board/' + str(code) + '@1'
    req = urllib.request.Request(url, method='GET')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-KEY', get_token())

    with urllib.request.urlopen(req) as res:
        content = json.loads(res.read())
    print(content)
    return content['CurrentPrice'], content['AskPrice'], content['BidPrice']


def get_stock_balance():  # 미완성
    url = 'http://localhost:18080/kabusapi/positions'
    params = {'product': 0}
    req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-KEY', get_token())

    with urllib.request.urlopen(req) as res:
        print(res.status, res.reason)
        for header in res.getheaders():
            print(header)

        content = json.loads(res.read())
    pprint.pprint(content)


def get_ohlc(code, qty):
    df = pd.read_csv(str(code) + '.csv', encoding='utf-8')
    df.set_index('Date', inplace=True)
    df.drop('Volume', axis=1, inplace=True)
    return df[:qty]


def get_target_price(code):
    try:
        time_now = datetime.datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(code, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            lastday = ohlc.iloc[0]
            today_open = lastday[3]
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * 0.5
        return target_price
    except Exception as ex:
        dbgout("'get_target_price() -> exception! " + str(ex) + "'")
        return None


def get_movingaverage(code, window):
    try:
        time_now = datetime.datetime.now()
        str_today = time_now.strftime('%Y/%m/%d')
        ohlc = get_ohlc(code, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['Close'].sort_index()
        ma = closes.rolling(window=window).mean()
        return ma.loc[lastday]
    except Exception as ex:
        dbgout("'get_movingaverage() -> exception! " + str(ex) + "'")
        return None

def buy_etf(code):
    try:
        global bought_List
        if code in bought_List:
            print('code:', code, 'in',bought_List)
            return False

        time_now = datetime.datetime.now()
        current_price, ask_price, bid_price = get_current_price(code)
        target_price = get_target_price(code)
        ma5_price = get_movingaverage(code, 5)
        ma10_price = get_movingaverage(code, 10)

        buy_qty = 0
        if ask_price > 0:
            buy_qty = buy_amount # 추가해야됨
        stock_name, stock_qty = get_stock_balance(code)  # 추가해야됨. 종목명과 보유 수량 조회

        if current_price >= target_price and current_price >= ma5_price and current_price >= ma10_price and ma5_price > ma10_price :
            etc = 0  # 임시변수 나중에 수정하기

    except Exception as ex:
        dbgout("'get_buy_etf(" + str(code) + ") -> exception! " + str(ex) + "'")


def dbgout(message):
    print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message)


if __name__ == '__main__':
    bought_List = []
    buy_amount = 0