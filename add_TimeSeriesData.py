import pandas as pd
import numpy as np
import json
import requests
from selenium import webdriver
from bs4 import BeautifulSoup


with open('auth.json', 'r') as f:
    auth = json.load(f)

url = "https://s20.si0.kabu.co.jp/members/"
driver = webdriver.Chrome(
    executable_path=r'C:\Users\KOJ\PycharmProjects\untitled\GitMaster\auto_Investment\chromedriver')
driver.get(url)
driver.find_element_by_name('SsLogonUser').send_keys(auth['id'])
driver.find_element_by_name('SsLogonPassword').send_keys(auth['loginPw'])
driver.find_element_by_id('image1').click()

s = requests.Session()
print(type(s))
for cookie in driver.get_cookies():
    s.cookies.set(cookie['name'], cookie['value'])

ETF_Link = pd.read_csv('ETF_link.csv', encoding='utf-8')
ETF_Link = ETF_Link.values

for i in ETF_Link:
    etfNum = i[0].split('.')[-2].split('=')[-1]
    timeSeriesLink = "https://s20.si0.kabu.co.jp/ap/PC/InvInfo/Market/StockDetail/Default?Symbol=" + etfNum + \
                     "&Exchange=TSE&Category=PRICE_HISTORY"
    result = s.get(timeSeriesLink).text
    soup = BeautifulSoup(result, "html.parser")
    table = soup.find_all("table", class_="tb3")
    df = pd.read_html(str(table), header=0)[0]
    df = df.drop("前日比", axis=1)
    df = df.rename(columns={'基準日': 'Date', '始値': 'Open', '高値': 'High', '安値': 'Low', '終値': 'Close', '出来高': 'Volume'})


    def fix_date(row):
        return row.split('(')[0]


    df['Date'] = df['Date'].apply(fix_date)
    df = df.replace('--', np.nan)
    df = df.dropna(axis=0)

    result = pd.DataFrame(df)
    load = pd.read_csv(etfNum + '.csv', encoding='utf-8')
    result = pd.concat([result[:1], load[0:]])
    result = result.drop_duplicates()
    result.to_csv(etfNum + '.csv', index=False, encoding='utf-8')
    break

driver.close()