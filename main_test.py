import requests
import time
import json
import pprint
import urllib.request
import datetime
import pandas as pd
import sys
import mysql.connector as mydb
from selenium import webdriver
from bs4 import BeautifulSoup


class autoInvestment:
    def __init__(self):
        with open('auth.json', 'r') as f:
            self.auth = json.load(f)

        headers = {'content-type': 'application/json'}
        json_data = json.dumps({'APIPassword': self.auth['APIPassword'], }).encode('utf8')
        url = 'http://localhost:18080/kabusapi/token'

        response = requests.post(url, data=json_data, headers=headers)

        self.token = json.loads(response.text)['Token']

        # sys.stdout = open('log/' + self.t_now.strftime('%Y%m%d') + '.log', 'w')

    # def __del__(self):

        # sys.stdout.close()

    def main(self, stock_list):
        self.buy_etf()

    def buy_etf(self):
        url = 'http://localhost:18080/kabusapi/symbol/1305@1'
        req = urllib.request.Request(url, method='GET')
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-API-KEY', self.token)

        try:
            with urllib.request.urlopen(req) as res:
                print(res.status, res.reason)
                for header in res.getheaders():
                    print(header)
                print()
                content = json.loads(res.read())
                pprint.pprint(content)
                print(content['TradingUnit'])
        except urllib.error.HTTPError as e:
            print(e)
            content = json.loads(e.read())
            pprint.pprint(content)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    symbol_list = ['1308', '1615', '1670', '1398', '2511', '2520', '1488', '1568', '1595', '2513']
    auto = autoInvestment()
    auto.main(symbol_list)