import pandas as pd
import mysql.connector as mydb
import numpy as np
import json
import requests
import sys
from datetime import datetime


class MarketDB:
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
        self.get_comp_info()

    def get_comp_info(self):
        sql = "SELECT * FROM company_info"
        comp = pd.read_sql(sql, self.conn)
        for idx in range(len(comp)):
            self.codes[comp['code'].values[idx]] = comp['company'].values[idx]

    def get_daily_price(self, code):
        codes_keys = list(self.codes.keys())
        codes_values = list(self.codes.values())
        if str(code) in codes_keys:
            pass
        else:
            print("ValueError: Code({}) doesn't exist.".format(code))

        sql = f"SELECT * FROM daily_price WHERE code={code} ORDER BY date desc"
        df = pd.read_sql(sql, self.conn)
        df.index = df['date']
        return df


# if __name__ == '__main__':
#     mk = MarketDB()
#     print(mk.get_daily_price(1305))
