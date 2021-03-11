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

url = 'http://localhost:18081/kabusapi/positions'
params = { 'product': 0 }   # product - 0:すべて、1:現物、2:信用、3:先物、4:OP
#params['symbol'] = '9433'  # symbol='xxxx'
req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET')
req.add_header('Content-Type', 'application/json')
req.add_header('X-API-KEY', get_token())

try:
    with urllib.request.urlopen(req) as res:
        print(res.status, res.reason)
        for header in res.getheaders():
            print(header)
        print()
        content = json.loads(res.read())
        pprint.pprint(content)
except urllib.error.HTTPError as e:
    print(e)
    content = json.loads(e.read())
    pprint.pprint(content)
except Exception as e:
    print(e)