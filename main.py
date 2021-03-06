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

        self.bought_list = []
        self.target_buy_count = 3
        self.buy_percent = 0.33
        self.total_cash = int(self.get_current_cash())
        self.buy_amount = self.total_cash * self.buy_percent
        self.t_now = datetime.datetime.now()
        sys.stdout = open('log/' + self.t_now.strftime('%Y%m%d') + '.log', 'w')

    def __del__(self):
        sys.stdout.close()

    def main(self, stock_list):
        try:
            print('total cash : ', self.total_cash)
            print('buy percent : ', self.buy_percent)
            print('buy_amount : ', self.buy_amount)
            print('start time : ', datetime.datetime.now().strftime('%m/%d %H:%M:%S'))

            while True:

                t_start = self.t_now.replace(hour=9, minute=5, second=0, microsecond=0)
                t_sell = self.t_now.replace(hour=14, minute=45, second=0, microsecond=0)
                t_exit = self.t_now.replace(hour=14, minute=58, second=0, microsecond=0)

                today = datetime.datetime.today().weekday()
                if today == 5 or today == 6:
                    print('Today is', 'Saturday.' if today == 5 else 'Sunday.')
                    sys.exit(0)

                if t_start < self.t_now < t_sell:
                    for sym in stock_list:
                        if len(self.bought_list) < self.target_buy_count:
                            self.buy_etf(sym)
                            time.sleep(1)
                    if self.t_now.minute == 30 and 0 <= self.t_now.second <= 5:
                        self.get_stock_balance('ALL')
                        time.sleep(5)
                if t_sell < self.t_now < t_exit:
                    if self.sell_all():
                        self.dbgout('sell_all() returned True -> self-destructed!')
                        sys.exit(0)
                if t_exit < self.t_now:
                    self.dbgout('self-destructed!')
                    sys.exit(0)

                time.sleep(3)

        except Exception as ex:
            self.dbgout('main -> excption! ' + str(ex) + '')

    def get_current_price(self, code):
        url = 'http://localhost:18080/kabusapi/board/' + str(code) + '@1'
        req = urllib.request.Request(url, method='GET')
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-API-KEY', self.token)

        with urllib.request.urlopen(req) as res:
            content = json.loads(res.read())
        print(content)
        return content['CurrentPrice'], content['AskPrice'], content['BidPrice']

    def get_ohlc(self, code, qty):
        conn = mydb.connect(
            host="localhost",
            port="3306",
            user="root",
            password=self.auth["DBPassword"],
            db="investar",
            charset="utf8"
        )
        conn.cursor()
        sql = f"SELECT * FROM daily_price WHERE code={code}"
        df = pd.read_sql(sql, conn, index_col='date')
        df = df.sort_index(ascending=False)
        df = df.drop('code', axis=1)
        df = df.drop('volume', axis=1)
        return df.iloc[:qty]

    def get_target_price(self, code):
        try:
            time_now = datetime.datetime.now()
            str_today = time_now.strftime('%Y%m%d')
            ohlc = self.get_ohlc(code, 10)
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
            self.dbgout("'get_target_price() -> exception! " + str(ex) + "'")
            return None

    def get_movingaverage(self, code, window):
        try:
            time_now = datetime.datetime.now()
            str_today = time_now.strftime('%Y/%m/%d')
            ohlc = self.get_ohlc(code, 20)
            if str_today == str(ohlc.iloc[0].name):
                lastday = ohlc.iloc[1].name
            else:
                lastday = ohlc.iloc[0].name
            closes = ohlc['close'].sort_index()
            ma = closes.rolling(window=window).mean()
            return ma.loc[lastday]
        except Exception as ex:
            self.dbgout("'get_movingaverage() -> exception! " + str(ex) + "'")
            return None

    def get_stock_balance(self, code):
        url = 'http://localhost:18080/kabusapi/positions'
        params = {'product': 1}  # product - 0:すべて、1:現物、2:信用、3:先物、4:OP
        req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET')
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-API-KEY', self.token)

        with urllib.request.urlopen(req) as res:
            content = json.loads(res.read())

        if len(content) > 0 or code == 'ALL':
            if len(content) == 0:
                return 'None Stock', 0
            allStocks = []
            for i in range(content):
                stock_code = content['Symbol']
                stock_name = content['SymbolName']
                stock_qty = content['LeavesQty']
                if code == 'ALL':
                    self.dbgout(str(i) + ' ' + stock_code + '( ' + stock_name + ' )' + ' : ' + str(stock_qty))
                    allStocks.append({'code': stock_code, 'name': stock_name, 'qty': stock_qty})
                if stock_code == code:
                    return stock_code, stock_qty
            if code == 'ALL':
                return allStocks
        elif code is not 'ALL':
            try:
                url = 'http://localhost:18080/kabusapi/symbol/' + str(code) + '@1'
                req = urllib.request.Request(url, method='GET')
                req.add_header('Content-Type', 'application/json')
                req.add_header('X-API-KEY', self.token)

                with urllib.request.urlopen(req) as res:
                    content = json.loads(res.read())
                stock_code = content['SymbolName']
                return stock_code, 0
            except urllib.error.HTTPError as e:
                print(e)
                content = json.loads(e.read())
                pprint.pprint(content)
            except Exception as e:
                print(e)

    def buy_etf(self, code):
        try:
            if code in self.bought_list:
                print('code:', code, 'in', self.bought_list)
                return False

            current_price, ask_price, bid_price = self.get_current_price(code)
            target_price = self.get_target_price(code)
            ma5_price = self.get_movingaverage(code, 5)
            ma10_price = self.get_movingaverage(code, 10)

            url = 'http://localhost:18080/kabusapi/symbol/' + code + '@1'
            req = urllib.request.Request(url, method='GET')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-API-KEY', self.token)
            with urllib.request.urlopen(req) as res:
                content = json.loads(res.read())
            TradingUnit = int(content['TradingUnit'])

            buy_qty = 0
            if ask_price > 0:
                buy_qty = self.buy_amount // ask_price
                buy_qty = (buy_qty // TradingUnit) * TradingUnit
            stock_name, stock_qty = self.get_stock_balance(code)

            if current_price >= target_price and current_price >= ma5_price and current_price >= ma10_price:
                if ma5_price > ma10_price:
                    print(stock_name + '(' + str(code) + ') ' + str(buy_qty) + 'EA : ' + str(current_price) +
                          ' meets the buy condition!')
                    obj = {'Password': self.auth['APIPassword'],
                           'Symbol': code,
                           'Exchange': 1,
                           'SecurityType': 1,
                           'FrontOrderType': 20,
                           'Side': '2',
                           'CashMargin': 1,
                           'DelivType': 2,
                           'FundType': '02',
                           'AccountType': 2,
                           'Qty': int(buy_qty),
                           'Price': target_price,
                           'ExpireDay': 0}
                    json_data = json.dumps(obj).encode('utf-8')

                    url = 'http://localhost:18080/kabusapi/sendorder'
                    req = urllib.request.Request(url, json_data, method='POST')
                    req.add_header('Content-Type', 'application/json')
                    req.add_header('X-API-KEY', self.token)

                    with urllib.request.urlopen(req) as res:
                        content = json.loads(res.read())

                    time.sleep(2)
                    stock_name, bought_qty = self.get_stock_balance(code)
                    if bought_qty > 0:
                        self.bought_list.append(code)
                        self.dbgout("'buy_etf(" + str(stock_name) + ' : ' + str(code) + ') -> ' + str(bought_qty) +
                                    "EA bought !' " + content['OrderId'])

        except urllib.error.HTTPError as e:
            print(e)
            content = json.loads(e.read())
            pprint.pprint(content)

        except Exception as ex:
            self.dbgout("'buy_etf(" + str(code) + ") -> exception! " + str(ex) + "'")

    def sell_all(self):
        try:
            while True:
                sellStocks = self.get_stock_balance('ALL')
                total_qty = 0
                for s in sellStocks:
                    total_qty += s['qty']
                if total_qty == 0:
                    return True

                for s in sellStocks:
                    if s['qty'] != 0:
                        obj = {'Password': self.auth['APIPassword'],
                               'Symbol': s['code'],
                               'Exchange': 1,
                               'SecurityType': 1,
                               'FrontOrderType': 17,
                               'Side': '1',
                               'CashMargin': 1,
                               'DelivType': 0,
                               'FundType': '  ',
                               'AccountType': 2,
                               'Qty': s['qty'],
                               'Price': 0,
                               'ExpireDay': 0}
                        json_data = json.dumps(obj).encode('utf-8')

                        url = 'http://localhost:18080/kabusapi/sendorder'
                        req = urllib.request.Request(url, json_data, method='POST')
                        req.add_header('Content-Type', 'application/json')
                        req.add_header('X-API-KEY', self.token)

                        with urllib.request.urlopen(req) as res:
                            content = json.loads(res.read())

                        print('sell', s['code'], s['name'], s['qty'], '->', content['OrderId'])

        except Exception as ex:
            self.dbgout("sell_all() -> exception! " + str(ex))

    @staticmethod
    def get_current_cash():
        with open('auth.json', 'r') as f:
            auth = json.load(f)

        loginURL = "https://s20.si0.kabu.co.jp/members/"
        driver = webdriver.Chrome(
            executable_path=r'C:\Users\KOJ\PycharmProjects\untitled\GitMaster\auto_Investment\chromedriver')
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
        toSlackMsg = {"text": self.t_now.strftime('[%m/%d %H:%M:%S]') + message}
        slack_webhook_url = self.auth["slackUrl"]
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer " + self.auth["slackToken"]}
        requests.post(slack_webhook_url, headers=headers, data=json.dumps(toSlackMsg))


if __name__ == '__main__':
    symbol_list = ['1308', '1615', '1670', '1398', '2511', '2520', '1488', '1568', '1595', '2513']
    auto = autoInvestment()
    auto.main(symbol_list)
