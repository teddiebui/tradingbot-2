from ..APIBot.AbstractCrawler import AbstractCrawler
import requests
import time
import datetime
from pprint import pprint
class OneTimeCrawler(AbstractCrawler):

    def __init__(self, client):
        super().__init__()
        self.client = client
        print("hi im One time crawler")
        
        self.futures_symbols = []
        self.symbols = []
        self.klines = {}
        self.req = requests.Session()
        self.running = False
    
    def get_all_futures_symbol_name(self):
    
        if len(self.futures_symbols) == 0:
        
            tickers = self.client.futures_symbol_ticker()
            
            for each in tickers:
                symbol = each['symbol']
                
                if (symbol.endswith("USDT") and not symbol.startswith("DEFI")):
                    self.futures_symbols.append(symbol)

        print("done get all futures symbol name")
       
        return self.futures_symbols
    
    
        
    def get_all_symbol_name(self):
        
        if len(self.symbols) == 0:

            prices = self.client.get_all_tickers()
            
            for each in prices:
                symbol = each['symbol']
                
                if (symbol.endswith("USDT") and not symbol.startswith("DEFI")):
                    self.symbols.append(symbol)
        
        return self.symbols
            
    
    def get_klines(self, startTime, symbols = None, interval = "15m", limit = 1000):
        
        t = time.time()
        for symbol in symbols[:]:
            if not self.running:
                return None
            a=time.time()
            url = self.klines_url(symbol, interval, startTime, limit = limit)
            response = self.req.get(url)
            if (response.status_code != 200):
                symbols.remove(symbol)
                print("error symbol:", symbol, response.status_code, response.text)
                continue
            self.klines[symbol] = self.build_klines_from_array(response.json())
            elapsed_time = time.time()-a
            print("{:.2f} - {:.2f}, symbol: {}, {}/{}".format(time.time()-t, elapsed_time, symbol, symbols.index(symbol)+1,len(symbols)))
        return self.klines
        
    
    def build_klines_from_array(self, array):
    
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
    def stop(self):
        self.running = False
    
