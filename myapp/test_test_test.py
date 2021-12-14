import json
import datetime
import time
import plotly.graph_objects as go

import pandas as pd
import pprint
import tradingbot2.Indicator.Indicator as Indicator

class Test:
    def __init__(self, client):
        self.indicator = Indicator.Indicator()
        self.client = client
        self.read_klines("BTCUSDT")


    def read_klines(self, symbol):
        self.data = self.read(symbol)
        self.kline_print(self.data)


    def test(self, symbol):

        self.data = self.read("BTCUSDT")
        self.data = self._build_klines_from_array(self.data)
        _15m = self.data['15m']

        price =[i['close'] for i in _15m]
        self.indicator.set_data(price)
        indicator = self.indicator.rsi()

        for i in range(len(price)):
            if i > 15:
                
                print("{} - {}, indicator:{:.4f} - O:{} H:{} L:{} C:{} vol: {}".format(symbol, datetime.datetime.fromtimestamp(_15m[i]['time']), indicator[i], _15m[i]['open'], _15m[i]['high'], _15m[i]['low'], _15m[i]['close'], _15m[i]['volume']))
        print(len(_15m))
        print(len(price))


    def test_indicator(self, symbol):
        self.data = self.read(symbol)
        self.data = self._build_klines_from_array(self.data)
        _15m = self.data['15m']


        price =[i['close'] for i in _15m]
        volume = [i['volume'] for i in _15m]

        self.indicator.set_data(price)
        indicator = self.indicator.rsi()

        self.indicator.set_data(volume)
        volume_ma = self.indicator.ma(14)

        for i in range(len(indicator)):
            print("{} -indicator:{:.4f} - O:{} H:{} L:{} C:{} vol: {}".format(datetime.datetime.fromtimestamp(_15m[i]['time']), volume_ma[i], _15m[i]['open'], _15m[i]['high'], _15m[i]['low'], _15m[i]['close'], _15m[i]['volume'] ))
    
    def plot(self):
        df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv')

        fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                        open=df['AAPL.Open'],
                        high=df['AAPL.High'],
                        low=df['AAPL.Low'],
                        close=df['AAPL.Close'])])

        fig.show()

    def check_klines(self):
        data = self.read("btcusdt")
        self.print(data)

    def read(self, symbol):
        with open(r"C:\Users\teddi\Desktop\temp\tradingbot-2\myapp\tradingbot2\jsondata\klines\{}.json".format(symbol.upper()), "r") as f:
            data = json.load(f)
            print(len(data))
            return data

    def refined_kline_print(self, data):
        for i in data:
            print("{} - O:{:.2f} H:{:.2f} L:{:.2f} C:{:.2f} Vol:{:.4f} quoteVol: {:.4f} Trades: {:.4f} buyVolume: {:.4f} buyQuoteVolume: {:.4f} ".format(
                datetime.datetime.fromtimestamp(i['time']), i['open'], i['high'], i['low'], i['close'], i['volume'], i['quoteVolume'], i['trades'], i['buyVolume'], i['buyQuoteVolume'])
                )

    def kline_print(self, data):
        for i in data:
            print("{} - O:{} H:{} L:{} C:{}".format(datetime.datetime.fromtimestamp(i[0]/1000), i[1], i[2], i[3], i[4]))

    def print(self, data):

        for i in data:
            
            print(i)

        print("len(data): ", len(data))

    def test2(self):

        with open(r"C:\Users\teddi\Desktop\temp\tradingbot-2\myapp\tradingbot2\jsondata\klines\BTCUSDT.json", "r") as f:
            data = json.load(f)
            klines = self._build_klines_from_array(data)

            print(klines['15m'][-1])
            print(datetime.datetime.fromtimestamp(klines['15m'][-1]["time"]))
    
    def _build_klines_from_array(self, data, klines = None):

        candle_15m = klines['15m'] if klines else []
        candle_1h = klines['1h'] if klines else []
        candle_4h = klines['4h'] if klines else []
        candle_1d = klines['1d'] if klines else []
        candle_1w = klines['1w'] if klines else []

        if len(data) > 0:
            for i in data[-500:]:
                
                t = datetime.datetime.fromtimestamp(i[0]/1000)
                
                candle = {'time': int(float(i[0])/1000),
                    'open' : float(i[1]), 
                    'high' : float(i[2]), 
                    'low' : float(i[3]), 
                    'close' : float(i[4]),
                    'volume': float(i[5]),
                    'closeTime': float(i[6]),
                    'quoteVolume': float(i[7]),
                    'trades': int(i[8]),
                    'buyVolume' : float(i[9]),
                    'buyQuoteVolume': float(i[10])
                    }
                    
                #15m
                candle_15m.append(candle)
            
                #1h
                if t.minute == 0:
                    candle_1h.append(dict.copy(candle))
                else:
                    if len(candle_1h) > 0:
                        self._build_merge_candle(candle, candle_1h[-1])
                #4h
                if t.minute == 0 and t.hour % 4 == 0:
                    candle_4h.append(dict.copy(candle))
                else:
                    if len(candle_4h) > 0:
                        self._build_merge_candle(candle, candle_4h[-1])

                #1d
                if t.minute == 0 and t.hour == 8:
                    candle_1d.append(dict.copy(candle))
                else:
                    if len(candle_1d) > 0:
                        self._build_merge_candle(candle, candle_1d[-1])

                #1w
                if t.minute == 0 and t.hour == 8 and (t.timestamp()/60/60/24) % 7 == 4:
                    candle_1w.append(dict.copy(candle))
                else:
                    if len(candle_1w) > 0:
                        self._build_merge_candle(candle, candle_1w[-1])

        return {"15m": candle_15m, "1h" : candle_1h, "4h" : candle_4h, "1d": candle_1d, "1w": candle_1w}
    
    def _build_merge_candle(self, candle, merging_candle):

        merging_candle['high'] = candle['high'] if candle['high'] > merging_candle['high'] else merging_candle['high']
        merging_candle['low'] = candle['low'] if candle['low'] < merging_candle['low'] else merging_candle['low']
        merging_candle['close'] = candle['close']
        merging_candle['volume'] +=  candle['volume']
        merging_candle['quoteVolume'] += candle['quoteVolume']
        merging_candle['trades'] += candle['trades']
        merging_candle['buyVolume'] += candle['buyVolume']
        merging_candle['buyQuoteVolume'] += candle['buyQuoteVolume']     


if __name__ == "__main__":
    from binance.enums import *
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    
    client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")
    t = Test(client)