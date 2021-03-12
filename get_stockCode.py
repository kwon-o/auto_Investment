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
    url = 'http://localhost:18081/kabusapi/token'

    response = requests.post(url, data=json_data, headers=headers)

    return json.loads(response.text)['Token']

def get_current_price(code):
    url = 'http://localhost:18081/kabusapi/board/' + str(code) + '@1'
    req = urllib.request.Request(url, method='GET')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-KEY', get_token())

    with urllib.request.urlopen(req) as res:
        content = json.loads(res.read())
    print(content)
    return content['CurrentPrice'], content['AskPrice'], content['BidPrice']

code = "1305"
url = 'http://localhost:18081/kabusapi/positions'
params = {'product': 1}  # product - 0:すべて、1:現物、2:信用、3:先物、4:OP
req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET')
req.add_header('Content-Type', 'application/json')
req.add_header('X-API-KEY', get_token())

with urllib.request.urlopen(req) as res:
    content = json.loads(res.read())

stocks = []
if len(content) > 0:
    for i in range(content):
        stock_code = content['Symbol']
        stock_name = content['SymbolName']
        stock_qty = content['LeavesQty']
        print()(str(i) + ' ' + stock_code + '( ' + stock_name + ' )' + ' : ' + str(stock_qty))
        stocks.append({'code': stock_qty, 'name': stock_name, 'qty': stock_qty})

else:
    url = 'http://localhost:18081/kabusapi/symbol/' + str(code) + '@1'
    req = urllib.request.Request(url, method='GET')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-KEY', get_token())

    with urllib.request.urlopen(req) as res:
        content = json.loads(res.read())
    stock_code = content['']


print(stocks)