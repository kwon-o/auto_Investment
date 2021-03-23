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


class autoInvestment:
    def __init__(self):
        with open('auth.json', 'r') as f:
            self.auth = json.load(f)

        headers = {'content-type': 'application/json'}
        json_data = json.dumps({'APIPassword': self.auth['APIPassword'], }).encode('utf8')
        url = 'http://localhost:18080/kabusapi/token'

        response = requests.post(url, data=json_data, headers=headers)

        self.token = json.loads(response.text)['Token']

        self.bought_list = []
        self.target_buy_count = 4
        self.buy_percent = 0.24
        self.total_cash = 0
        self.buy_amount = 0

    # def aaa(self):
    #     url = 'http://localhost:18080/kabusapi/positions'
    #     params = {'product': 0}  # product - 0:すべて、1:現物、2:信用、3:先物、4:OP
    #     # params['symbol'] = '9433'  # symbol='xxxx'
    #     req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET')
    #     req.add_header('Content-Type', 'application/json')
    #     req.add_header('X-API-KEY', self.token)
    #
    #     try:
    #         with urllib.request.urlopen(req) as res:
    #             print(res.status, res.reason)
    #             for header in res.getheaders():
    #                 print(header)
    #             print()
    #             content = json.loads(res.read())
    #             pprint.pprint(content)
    #     except urllib.error.HTTPError as e:
    #         print(e)
    #         content = json.loads(e.read())
    #         pprint.pprint(content)
    #     except Exception as e:
    #         print(e)

    def get_stock_balance(self, code):
        if code == 'ALL':
            self.dbgout('Cash balance : ' + str(self.get_current_cash()))

            url = 'http://localhost:18080/kabusapi/positions'
            params = {'product': 1}  # product - 0:すべて、1:現物、2:信用、3:先物、4:OP
            req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-API-KEY', self.token)

            with urllib.request.urlopen(req) as res:
                content = json.loads(res.read())
            if len(content) == 0:
                return 'None Stock', 0
            allStocks = []
            cnt = 0
            for i in content:
                stock_code = i['Symbol']
                stock_name = i['SymbolName']
                stock_qty = i['LeavesQty']
                print(stock_code, stock_name, stock_qty)
                cnt += 1
                if code == 'ALL':
                    self.dbgout(str(cnt) + '. ' + stock_code + '( ' + stock_name + ' )' + ' : ' + str(stock_qty))
                    allStocks.append({'code': stock_code, 'name': stock_name, 'qty': stock_qty})
                if stock_code == code:
                    return stock_code, stock_qty
            if code == 'ALL':
                return allStocks
        elif code is not 'ALL':
            url = 'http://localhost:18080/kabusapi/positions'
            params = {'product': 1, 'symbol': code}
            req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-API-KEY', self.token)

            with urllib.request.urlopen(req) as res:
                content = json.loads(res.read())
                print(content)
            if len(content) == 0:
                url = 'http://localhost:18080/kabusapi/symbol/' + str(code) + '@1'
                req = urllib.request.Request(url, method='GET')
                req.add_header('Content-Type', 'application/json')
                req.add_header('X-API-KEY', self.token)

                with urllib.request.urlopen(req) as res:
                    content = json.loads(res.read())
                stock_code = content['SymbolName']
                return stock_code, 0
            else:
                stock_code = content[0]['SymbolName']
                stock_qty = content[0]['LeavesQty']
                return stock_code, stock_qty

    @staticmethod
    def get_current_cash():
        with open('auth.json', 'r') as f:
            auth = json.load(f)

        loginURL = "https://s20.si0.kabu.co.jp/members/"
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(executable_path='chromedriver', options=options)
        driver.get(loginURL)
        driver.find_element_by_name('SsLogonUser').send_keys(auth['id'])
        driver.find_element_by_name('SsLogonPassword').send_keys(auth['loginPw'])
        driver.find_element_by_id('image1').click()

        s = requests.Session()
        for cookie in driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'])

        cashCheckURL = "https://s20.si0.kabu.co.jp/ap/PC/Assets/Kanougaku/Stock"
        result = s.get(cashCheckURL).text
        soup = BeautifulSoup(result, "html.parser")
        table = soup.find_all("table", class_="table1")
        df = pd.read_html(str(table))[0]

        driver.close()

        return df[1][1]

    def dbgout(self, message):
        print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
        # toSlackMsg = {"text": datetime.datetime.now().strftime('[%m/%d %H:%M:%S]') + message}
        # slack_webhook_url = self.auth["slackUrl"]
        # headers = {
        #     "Content-type": "application/json",
        #     "Authorization": "Bearer " + self.auth["slackToken"]}
        # requests.post(slack_webhook_url, headers=headers, data=json.dumps(toSlackMsg))


if __name__ == '__main__':
    symbol_list = ['1308', '1615', '1670', '1398', '2511', '2520', '1488', '1568', '1595', '2513']
    auto = autoInvestment()
    print(auto.get_stock_balance('1670'))
    # print(auto.get_stock_balance('1305'))
