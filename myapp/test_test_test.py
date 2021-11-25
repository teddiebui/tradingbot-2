import json
import datetime
import time

import tradingbot2.Indicator.Indicator as Indicator

class Test:
    def __init__(self):
        self.indicator = Indicator.Indicator()
        self.check_klines()

    def test(self):

        data = self.read("btcusdt")
        data = self._build_klines_from_array(data)
        _15m = data['15m']


        price =[i['close'] for i in _15m]
        rsi = self.indicator.rsi(price)

        for i in range(len(rsi)):
            print("{} -R:{} - O:{} H:{} L:{} C:{}".format(datetime.datetime.fromtimestamp(_15m[i]['time']), rsi[i], _15m[i]['open'], _15m[i]['high'], _15m[i]['low'], _15m[i]['close']))

    def check_klines(self):
        data = self.read("btcusdt")
        self.print(data)

    def read(self, symbol):
        with open(r"C:\Users\teddi\Desktop\temp\tradingbot-2\myapp\tradingbot2\jsondata\klines\{}.json".format(symbol.upper()), "r") as f:
            data = json.load(f)
            return data
    
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

    def _build_klines_from_array(self, array):
    
        #array here is a list of candle lines
        candle_15m = []
        candle_1h = []
        candle_4h = []
        
        if len(array) > 0:
            for i in array[:]:
                
                t = datetime.datetime.fromtimestamp(i[0]/1000)
                
                candle = {'time': float(i[0])/1000,
                    'open' : float(i[1]), 
                    'high' : float(i[2]), 
                    'low' : float(i[3]), 
                    'close' :float(i[4])
                    }
                    
                #15m
                candle_15m.append(candle)
            
                #1h
                if t.minute == 0:
                    candle_1h.append(dict.copy(candle))
                if len(candle_1h) > 0:
                    if candle['high'] > candle_1h[-1]['high']:
                        candle_1h[-1]['high'] = float(candle['high'])
                    if candle['low'] < candle_1h[-1]['low']:
                        candle_1h[-1]['low'] = candle['low']
                    
                    candle_1h[-1]['close'] = candle['close']
                    
                #4h
                if t.minute == 0 and t.hour % 4 == 0:
                    candle_4h.append(dict.copy(candle))
                if len(candle_4h) > 0:
                    if candle['high'] > candle_4h[-1]['high']:
                        candle_4h[-1]['high'] = candle['high']
                    if candle['low'] < candle_4h[-1]['low']:
                        candle_4h[-1]['low'] = candle['low']
                    
                    candle_4h[-1]['close'] = candle['close']

        return {"15m": candle_15m, "1h" : candle_1h, "4h" : candle_4h}
           


if __name__ == "__main__":
    from binance.enums import *
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    t = Test();
    client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")
