import pandas as pd
import mysql.connector as mydb
import json
import calendar
from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup


class DBUpdater:
    def __init__(self):
        with open('auth.json', 'r') as f:
            _auth = json.load(f)
        self.conn = mydb.connect(
            host="localhost",
            port="3306",
            user="root",
            password=_auth["DBPassword"],
            db="investar",
            charset="utf8"
        )
        self.cursor = self.conn.cursor()
        self.conn.commit()
        self.codes = dict()

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

            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
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
        self.update_daily_price()


if __name__ == '__main__':
    dbu = DBUpdater()
    dbu.execute_daily()
