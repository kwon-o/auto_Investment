import requests
import json
import pprint
import urllib.request


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

    return content['CurrentPrice'], content['AskPrice'], content['BidPrice']


print(get_current_price('1305'))