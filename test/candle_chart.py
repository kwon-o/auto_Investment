import mplfinance as mpt
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup

df = pd.read_csv('StockPriceHistory.csv', encoding='CP932')
df = df.drop(["Unnamed: 7", "前日比"], axis=1)
df = df.rename(columns={'基準日':'Date', '始値':'Open', '高値':'High', '安値':'Low', '終値':'Close', '出来高':'Volume'})
df = df.sort_values(by='Date')
def fix_date(row):
    return row.split('(')[0]
df['Date'] = df['Date'].apply(fix_date)
df.index = pd.to_datetime(df.Date)
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
kwargs = dict(title='Celltrion candle chart', type='candle',
        mav=(2,4,6), volume=True, ylabel='ohlc candles')
mc = mpt.make_marketcolors(up='r', down='b', inherit=True)
s = mpt.make_mpf_style(marketcolors=mc)
mpt.plot(df, **kwargs, style=s)