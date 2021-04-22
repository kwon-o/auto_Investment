import requests
import time
import json
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
        self.s = self.get_session()

        self.target_buy_count = 3
        self.buy_percent = 0.33
        self.total_cash = 0
        self.buy_amount = 0
        self.k = 0.3

        self.symbol_list = ['1305', '1308', '1615', '2511', '2520', '1568', '2513', '1311',
                            '2510', '1343', '1547', '1540', '1593']
        self.bought_list = []

        sys.stdout = open('log/' + datetime.datetime.now().strftime('%Y%m%d') + '.log', 'w')

    def __del__(self):
        sys.stdout.close()

    def get_session(self):
        loginURL = "https://s20.si0.kabu.co.jp/members/"
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(executable_path='chromedriver', options=options)
        driver.get(loginURL)
        driver.find_element_by_name('SsLogonUser').send_keys(self.auth['id'])
        driver.find_element_by_name('SsLogonPassword').send_keys(self.auth['loginPw'])
        driver.find_element_by_id('image1').click()
        s = requests.Session()
        for cookie in driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'])
        driver.close()
        return s

    def main(self):
        try:
            self.get_stock_balance('ALL')
            self.total_cash = int(self.get_current_cash())
            self.buy_amount = self.total_cash * self.buy_percent
            print('total cash : ', self.total_cash)
            print('buy percent : ', self.buy_percent)
            print('buy_amount : ', self.buy_amount)
            print('start time : ', datetime.datetime.now().strftime('%m/%d %H:%M:%S'))
            self.dbgout('Program Start!')

            while True:
                t_now = datetime.datetime.now()
                t_start = t_now.replace(hour=9, minute=3, second=0, microsecond=0)
                t_breakS = t_now.replace(hour=11, minute=30, second=0, microsecond=0)
                t_breakE = t_now.replace(hour=12, minute=30, second=0, microsecond=0)
                t_sell = t_now.replace(hour=14, minute=50, second=0, microsecond=0)
                t_exit = t_now.replace(hour=15, minute=00, second=0, microsecond=0)

                if t_start < t_now < t_breakS:
                    if t_now.minute == 30 and 0 <= t_now.second <= 20:
                        self.get_stock_balance('ALL')
                    for sym in self.symbol_list:
                        if len(self.bought_list) < self.target_buy_count:
                            self.buy_etf(sym)
                            time.sleep(1)
                    continue
                if t_breakE < t_now < t_sell:
                    if t_now.minute == 30 and 0 <= t_now.second <= 20:
                        self.get_stock_balance('ALL')
                    for sym in self.symbol_list:
                        if len(self.bought_list) < self.target_buy_count:
                            self.buy_etf(sym)
                            time.sleep(1)
                    continue
                if t_sell < t_now < t_exit:
                    if self.sell_all():
                        self.dbgout('sell_all() returned True -> self-destructed!')
                        sys.exit(0)
                if t_exit < t_now:
                    self.dbgout('self-destructed!')
                    sys.exit(0)

                print('Waiting to run...')
                time.sleep(30)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('main -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' + str(ex) + ')')

    def get_current_price(self, code):
        try:
            url = 'http://localhost:18080/kabusapi/board/' + str(code) + '@1'
            req = urllib.request.Request(url, method='GET')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-API-KEY', self.token)

            with urllib.request.urlopen(req) as res:
                content = json.loads(res.read())
            if content['CurrentPrice'] is None:
                content['CurrentPrice'] = 1
                content['AskPrice'] = 1
                content['BidPrice'] = 1
                content['OpeningPrice'] = 1
            return content['CurrentPrice'], content['AskPrice'], content['BidPrice'], content['OpeningPrice']
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('get_current_price(' + code + ') -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' +
                        str(ex) + ')')

    def get_ohlc(self, code, qty):
        try:
            selecter = DBSelecter.MarketDB()
            df = selecter.get_daily_price(code)
            return df.iloc[:qty]
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('get_ohlc(' + code + ') -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' + str(ex) + ')')

    def get_target_price(self, code):
        try:
            current_price, ask_price, bid_price, open_price = self.get_current_price(code)
            ohlc = self.get_ohlc(code, 3)
            lastday = ohlc.iloc[0]
            lastday_high = lastday[2]
            lastday_low = lastday[3]
            target_price = (open_price + (lastday_high - lastday_low) * self.k) - 1
            return int(target_price)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('get_target_price(' + code + ') -> excption!! (line : ' + str(exc_tb.tb_lineno) +
                        ', ' + str(ex) + ')')
            return 999999

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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('get_movingaverage() -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' + str(ex) + ')')
            return None

    def get_stock_balance(self, code):
        try:
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
                    return [{'code': '----', 'name': 'None Stock', 'qty': 0}]
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
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('get_stock_balance(' + code + ') -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' +
                        str(ex) + ')')

    def buy_etf(self, code):
        try:
            if code in self.bought_list:
                print('code:', code, 'in', self.bought_list)
                return False
            current_price, ask_price, bid_price, open_price = self.get_current_price(code)
            target_price = self.get_target_price(code)
            ma5_price = self.get_movingaverage(code, 5)
            ma10_price = self.get_movingaverage(code, 10)

            url = 'http://localhost:18080/kabusapi/symbol/' + str(code) + '@1'
            req = urllib.request.Request(url, method='GET')
            req.add_header('Content-Type', 'application/json')
            req.add_header('X-API-KEY', self.token)
            with urllib.request.urlopen(req) as res:
                content = json.loads(res.read())
            TradingUnit = int(content['TradingUnit'])
            UpperLimit = content['UpperLimit']
            LowerLimit = content['LowerLimit']
            buy_qty = 0
            if ask_price > 0 and ask_price != 1:
                buy_qty = self.buy_amount // ask_price
                buy_qty = (buy_qty // TradingUnit) * TradingUnit
            stock_name, stock_qty = self.get_stock_balance(code)

            if current_price >= target_price and current_price >= ma5_price and current_price >= ma10_price and \
                    buy_qty != 0:
                self.dbgout(stock_name + '(' + str(code) + ') ' + str(buy_qty) + 'EA : ' + str(target_price) +
                            ' meets the buy condition!')
                self.dbgout('UpperLimit : ' + str(UpperLimit) + ', LowerLimit : ' + str(LowerLimit))
                obj = {'Password': self.auth['APIPassword'],
                       'Symbol': code,
                       'Exchange': 1,
                       'SecurityType': 1,
                       'FrontOrderType': 27,
                       'Side': '2',
                       'CashMargin': 1,
                       'DelivType': 2,
                       'AccountType': 2,
                       'Qty': int(buy_qty),
                       'Price': target_price,
                       'ExpireDay': 0,
                       'ClosePositionOrder': 0,
                       'FundType': '02'}
                json_data = json.dumps(obj).encode('utf-8')

                url = 'http://localhost:18080/kabusapi/sendorder'
                req = urllib.request.Request(url, json_data, method='POST')
                req.add_header('Content-Type', 'application/json')
                req.add_header('X-API-KEY', self.token)

                with urllib.request.urlopen(req) as res:
                    content = json.loads(res.read())
                if content['Result'] == 0:
                    self.dbgout("buy_etf(" + str(stock_name) + ' : ' + str(code) + ') -> ' + str(buy_qty) +
                                "EA * " + str(target_price) + "Yen Order complete !' " + content['OrderId'])
                time.sleep(1)
                stock_name, bought_qty = self.get_stock_balance(code)
                if bought_qty > 0:
                    self.bought_list.append(code)
                    self.dbgout("buy_etf(" + str(stock_name) + ' : ' + str(code) + ') -> ' + str(bought_qty) +
                                "EA Bought !' " + content['OrderId'])
                time.sleep(1)
        except urllib.error.HTTPError as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            content = json.loads(e.read())
            self.dbgout('buy_etf(' + code + ') -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' + content + ')')
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('buy_etf(' + code + ') -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' + str(ex) + ')')

    def sell_all(self):
        try:
            while True:
                sellStocks = self.get_stock_balance('ALL')
                total_qty = 0
                print(sellStocks)
                for s in sellStocks:
                    print(s)
                    total_qty += int(s['qty'])
                if total_qty == 0:
                    print('0')
                    return True

                for s in sellStocks:
                    if s['qty'] != 0:
                        obj = {'Password': self.auth['APIPassword'],
                               'Symbol': s['code'],
                               'Exchange': 1,
                               'SecurityType': 1,
                               'FrontOrderType': 16,
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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('sell_all() -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' + str(ex) + ')')

    def get_current_cash(self):
        try:
            cashCheckURL = "https://s20.si0.kabu.co.jp/ap/PC/Assets/Kanougaku/Stock"
            result = self.s.get(cashCheckURL).text
            soup = BeautifulSoup(result, "html.parser")
            table = soup.find_all("table", class_="table1")
            df = pd.read_html(str(table))[0]
            return df[1][0]
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.dbgout('get_current_cash() -> excption!! (line : ' + str(exc_tb.tb_lineno) + ', ' + str(ex) + ')')

    def dbgout(self, message):
        print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
        toSlackMsg = {"text": datetime.datetime.now().strftime('[%m/%d %H:%M:%S]') + message}
        slack_webhook_url = self.auth["slackUrl"]
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer " + self.auth["slackToken"]}
        requests.post(slack_webhook_url, headers=headers, data=json.dumps(toSlackMsg))


if __name__ == '__main__':
    weekday = datetime.datetime.today().weekday()
    auto = autoInvestment()
    if weekday in [0, 1, 2, 3, 4]:
        auto.main()
    else:
        sys.exit(0)
