import mysql.connector as mydb
import json
import pandas as pd
import logging


logger = logging.getLogger('LOGGER_NAME')
with open(r'C:\Users\KOJ\PycharmProjects\untitled\GitMaster\auto_Investment\auth.json', 'r') as f:
    auth = json.load(f)
conn = mydb.connect(
    host="localhost",
    port="3306",
    user="root",
    password=auth["DBPassword"],
    db="investar",
    charset="utf8"
)
conn.cursor()
sql = f"SELECT * FROM daily_price WHERE code=1305"
df = pd.read_sql(sql, conn, index_col='date')
df = df.sort_index(ascending=False)
df = df.drop('code', axis=1)
df = df.drop('volume', axis=1)

print(df.iloc[:5])