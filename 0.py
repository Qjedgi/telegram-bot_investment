from datetime import datetime, timedelta

from pandas import DataFrame
from ta.trend import ema_indicator
from tinkoff.invest import Client, RequestError, CandleInterval, HistoricCandle

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
exchange = os.getenv('TOKEN_TINKOFF')
acc = os.getenv('TIN_AKK_ID')
import pandas as pd
import matplotlib.pyplot as plt


def run():
    try:
        with Client(exchange) as client:
            r = client.market_data.get_candles(
                figi='USD000UTSTOM',
                from_=datetime.utcnow() - timedelta(days=7),
                to=datetime.utcnow(),
                interval=CandleInterval.CANDLE_INTERVAL_HOUR  # см. utils.get_all_candles
            )
            # print(r)

            df = create_df(r.candles)
            # https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ema_indicator
            df['ema'] = ema_indicator(close=df['close'], window=9)

            print(df[['time', 'close', 'ema']].tail(30))
            ax = df.plot(x='time', y='close')
            df.plot(ax=ax, x='time', y='ema')
            plt.show()

    except RequestError as e:
        print(str(e))


def create_df(candles: [HistoricCandle]):
    df = DataFrame([{
        'time': c.time,
        'volume': c.volume,
        'open': cast_money(c.open),
        'close': cast_money(c.close),
        'high': cast_money(c.high),
        'low': cast_money(c.low),
    } for c in candles])

    return df


def cast_money(v):
    return v.units + v.nano / 1e9  # nano - 9 нулей

if __name__ == "__main__":
    run()