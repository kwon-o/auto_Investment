import pandas as pd
import mysql.connector as mydb
import numpy as np
import json
import requests
import sys
from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup


class DBUpdater:
    def __init__(self):
        with open('auth.json', 'r') as f:
            self.auth = json.load(f)
        self.conn = mydb.connect(
            host="localhost",
            port="3306",
            user="root",
            password=self.auth["DBPassword"],
            db="investar",
            charset="utf8"
        )
        self.codes = dict()
        self.session = requests.Session()
        self.update_flg = 0


    @staticmethod
    def read_stock_code():
        return pd.read_csv('stock_code.csv', encoding='shift_jis')

    def update_comp_info(self):
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)
        for idx in range(len(df)):
            self.codes[df['code'].values[idx]] = df['company'].values[idx]

        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info"
            curs.execute(sql)
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')

            if None == rs[0] or rs[0].strftime('%Y-%m-%d') < today:
                stockCode = self.read_stock_code()
                for idx in range(len(stockCode)):
                    code = stockCode.code.values[idx]
                    company = stockCode.company.values[idx]
                    sql = f"REPLACE INTO company_info " \
                          f"(code, company, last_update) VALUES ('{code}', '{company}','{today}') "
                    curs.execute(sql)
                    self.codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] {idx:04d} REPLACE INTO company_info VALUES ({code}, {company}, {today})")
                self.conn.commit()
                print('')
                self.update_flg = 1

    @staticmethod
    def read_Time_Series_Data(code):
        try:
            driver = webdriver.Chrome(executable_path='chromedriver.exe')
            driver.get("https://kabuoji3.com/stock/" + str(code) + "/")
            source = driver.page_source
            soup = BeautifulSoup(source, 'html.parser')
            table = soup.find_all("table", class_='stock_table stock_data_table')
            df = pd.read_html(str(table), header=0)

            if len(df) == 2:
                df = pd.concat([df[0], df[1]])
            else:
                df = df[0]
            df = df.drop("終値調整", axis=1)
            df = df.rename(
                columns={'日付': 'date', '始値': 'open', '高値': 'high', '安値': 'low', '終値': 'close', '出来高': 'volume'})
            driver.close()
            return df
        except ImportError:
            return None

    def get_session(self):
        url = "https://s20.si0.kabu.co.jp/members/"
        driver = webdriver.Chrome(
            executable_path=r'C:\Users\KOJ\PycharmProjects\untitled\GitMaster\auto_Investment\chromedriver')
        driver.get(url)
        driver.find_element_by_name('SsLogonUser').send_keys(self.auth['id'])
        driver.find_element_by_name('SsLogonPassword').send_keys(self.auth['loginPw'])
        driver.find_element_by_id('image1').click()
        for cookie in driver.get_cookies():
            self.session.cookies.set(cookie['name'], cookie['value'])
        return self.session

    def add_Time_Series_data(self):
        self.get_session()
        for code in self.codes:
            timeSeriesLink = "https://s20.si0.kabu.co.jp/ap/PC/InvInfo/Market/StockDetail/Default?Symbol=" \
                             + code + "&Exchange=TSE&Category=PRICE_HISTORY"
            result = self.session.get(timeSeriesLink).text
            soup = BeautifulSoup(result, "html.parser")
            table = soup.find_all("table", class_="tb3")
            try:
                df = pd.read_html(str(table), header=0)[0]
            except ValueError:
                continue
            df = df.drop("前日比", axis=1)
            df = df.rename(columns={'基準日': 'date', '始値': 'open', '高値': 'high', '安値': 'low',
                                    '終値': 'close', '出来高': 'volume'})

            def fix_date(row):
                return row.split('(')[0]

            df['date'] = df['date'].apply(fix_date)
            df.replace('/', '-')
            df = df.replace('--', np.nan)
            df = df.dropna(axis=0)
            df = pd.DataFrame(df)

            self.replace_into_db(df, code)
            print('Code ' + code + ': Time series data replace was successful!')

    def replace_into_db(self, df, code):
        with self.conn.cursor() as curs:
            for r in df.itertuples():
                sql = f"REPLACE INTO daily_price VALUES ('{code}', '{r.date}',{r.open},{r.high}," \
                      f"{r.low},{r.close},{r.volume})"
                curs.execute(sql)
            self.conn.commit()

    def update_daily_price(self):
        for code in self.codes:
            df = self.read_Time_Series_Data(code)
            if df is None:
                continue
            self.replace_into_db(df, code)

    def execute_daily(self):
        self.update_comp_info()
        # self.update_daily_price() # Run only the first time
        # if self.update_flg == 1:
        self.add_Time_Series_data()
        toSlackMsg = {"text": datetime.now().strftime('[%m/%d %H:%M:%S]') + 'Database Update successful!'}
        slack_webhook_url = self.auth["slackUrl"]
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer " + self.auth["slackToken"]}
        requests.post(slack_webhook_url, headers=headers, data=json.dumps(toSlackMsg))


if __name__ == '__main__':
    weekday = datetime.today().weekday()
    dbu = DBUpdater()
    if weekday in [0, 1, 2, 3, 4]:
        dbu.execute_daily()
    else:
        sys.exit(0)
