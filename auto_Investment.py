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


def get_info():
    url = 'http://localhost:18080/kabusapi/board/1570@1'
    req = urllib.request.Request(url, method='GET')
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


get_info()


