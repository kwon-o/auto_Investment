import pandas as pd
import mysql.connector as mydb
import json
from datetime import datetime


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

    # def __del__(self):
    #     self.conn.close()

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

            if rs[0] == None or rs[0].strtime('%Y-%m-%d') < today:
                stockCode = self.read_stock_code()
                for idx in range(len(stockCode)):
                    code = stockCode.code.values[idx]
                    company = stockCode.company.values[idx]
                    sql = f"REPLACE INTO company_info (code, company, last_update) VALUES ('{code}', '{company}','{today}') "
                    curs.execute(sql)
                    self.codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] {idx:04d} REPLACE INTO company_info VALUES ({code}, {company}, {today})")
                self.conn.commit()
                print('')


    def read_Time_Series_Data(self, code, company):
        return None

    def select_comp_info(self):
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)
        for idx in range(len(df)):
            self.codes[df['code'].values[idx]] = df['company'].values[idx]
        print(self.codes)


if __name__ == '__main__':
    dbu = DBUpdater()
    dbu.select_comp_info()