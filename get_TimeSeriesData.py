import pandas as pd
import requests
import json
from selenium import webdriver
from bs4 import BeautifulSoup

ETF_link = []


def get_link(html):
    soup = BeautifulSoup(html, 'html.parser')
    hotKeys = soup.find("table", class_="table1")
    hotKeys = hotKeys.find_all("a")
    for i in hotKeys:
        if i['href'].split('/')[0] == "http:":
            ETF_link.append(i['href'])

with open('auth.json', 'r') as f:
    auth = json.load(f)

url = "https://s20.si0.kabu.co.jp/members/"
driver = webdriver.Chrome(executable_path='chromedriver')
driver.get(url)
driver.find_element_by_name('SsLogonUser').send_keys(auth['id'])
driver.find_element_by_name('SsLogonPassword').send_keys(auth['APIPassword'])
driver.find_element_by_id('image1').click()
driver.find_element_by_name('nav_g_02').click()
driver.find_element_by_link_text('フリーETF (手数料無料ETF)').click()
get_link(driver.page_source)
s = requests.Session()

for cookie in driver.get_cookie():
    s.cookies.set(cookie['name'], cookie['value'])
link_list = ["https://s20.si0.kabu.co.jp/ap/PC/Stocks/Stock/Search/ByKeyword?PageNo=2&Keyword=%e3%83%95%e3%83%aa%e3%83%bcETF&SortType.Value=0",
             "https://s20.si0.kabu.co.jp/ap/PC/Stocks/Stock/Search/ByKeyword?PageNo=3&Keyword=%e3%83%95%e3%83%aa%e3%83%bcETF&SortType.Value=0",
             "https://s20.si0.kabu.co.jp/ap/PC/Stocks/Stock/Search/ByKeyword?PageNo=4&Keyword=%e3%83%95%e3%83%aa%e3%83%bcETF&SortType.Value=0",
             "https://s20.si0.kabu.co.jp/ap/PC/Stocks/Stock/Search/ByKeyword?PageNo=5&Keyword=%e3%83%95%e3%83%aa%e3%83%bcETF&SortType.Value=0"]
for i in link_list:
    response = s.get(i)
    get_link(response)
driver.close()

result = pd.DataFrame(ETF_link, columns=['link'])
result.to_csv('ETF_link.csv', index=False, encoding='utf-8')
