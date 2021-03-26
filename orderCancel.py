import requests
import time
import json
import pprint
import urllib.request
import datetime
import pandas as pd
import sys
from selenium import webdriver
from bs4 import BeautifulSoup
import DBSelecter

with open('auth.json', 'r') as f:
    auth = json.load(f)

headers = {'content-type': 'application/json'}
json_data = json.dumps({'APIPassword': auth['APIPassword'], }).encode('utf8')
url = 'http://localhost:18080/kabusapi/token'

response = requests.post(url, data=json_data, headers=headers)
token = json.loads(response.text)['Token']


obj = {'OrderID': '20210326A01N30613921', 'Password': auth['APIPassword']}
json_data = json.dumps(obj).encode('utf8')

url = 'http://localhost:18080/kabusapi/cancelorder'
req = urllib.request.Request(url, json_data, method='PUT')
req.add_header('Content-Type', 'application/json')
req.add_header('X-API-KEY', token)

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
