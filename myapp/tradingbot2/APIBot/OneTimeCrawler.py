from ..APIBot.AbstractCrawler import AbstractCrawler
import requests
import time
import datetime
import os
import json as json
from pprint import pprint
class OneTimeCrawler(AbstractCrawler):

    def __init__(self, client):
        super().__init__()
        self.client = client
        print("hi im One time crawler")
        
        self.futures_symbols = []
        self.symbols = []
        self.futures_klines = {}
        self.req = requests.Session()
        self.running = False
        self.START_TIME = int(time.time()) - (360 * 24 * 60 * 60) #360: days ago
        
        self._init()
    
    def _init(self):
        self.running = True
        self.futures_symbols = self.get_all_futures_symbol_name()
        self.futures_get_klines()
    
    def get_all_futures_symbol_name(self):
    
        if len(self.futures_symbols) == 0:
        
            tickers = self.client.futures_symbol_ticker()
            
            for each in tickers:
                symbol = each['symbol']
                
                if (symbol.endswith("USDT") and not symbol.startswith("DEFI")):
                    self.futures_symbols.append(symbol)

        print("done get all futures symbol name: len(self.futures_symbols: ", len(self.futures_symbols))
       
        return self.futures_symbols
    
    
        
    def get_all_symbol_name(self):
        
        if len(self.symbols) == 0:

            prices = self.client.get_all_tickers()
            
            for each in prices:
                symbol = each['symbol']
                
                if (symbol.endswith("USDT") and not symbol.startswith("DEFI")):
                    self.symbols.append(symbol)
        
        return self.symbols
            
    
        
    def futures_get_klines(self):
        if not self.futures_klines:
            read = 0
            update  = 0
            refining = 0
            self.futures_klines = {}
            a=time.time()
            for symbol in self.futures_symbols:
                b=time.time()
                _klines = self._klines_from_file(symbol)
                c=time.time()

                while not self._klines_up_to_date(_klines):
                    _klines = self._klines_update(_klines, symbol)
                    if not _klines:
                        break
                if not _klines:
                    continue
                d= time.time()
                self.futures_klines[symbol] = self._build_klines_from_array(_klines)
                e=time.time()
                print("total: {:.2f}|read: {:.2f}|update: {:.2f}|refining: {:.2f}|len: {}| {}/{}".format(e-a,c-b,d-c,e-d,len(_klines), self.futures_symbols.index(symbol),len(self.futures_symbols)))
                read += c-b
                update += d-c
                refining += e-d
        print("total: {:.2f}|t-read: {:.2f}|t-update: {:.2f}|t-refining: {:.2f}|{}/{}".format(e-a,read, update, refining,self.futures_symbols.index(symbol),len(self.futures_symbols)))
        return self.futures_klines
        
    def _klines_up_to_date(self, klines):
        if not klines:
            return False
        
        last = klines[-1]
        timestamp = int(last[0]/1000)
        
        now = datetime.datetime.now()
        _now = now.replace(microsecond = 0, second = 0, minute = now.minute // 15 * 15)
        current_timestamp = int(_now.timestamp())
        
        print("... UP TO DATE? {} - {}".format(datetime.datetime.fromtimestamp(timestamp), datetime.datetime.fromtimestamp(current_timestamp)))
        print("............", timestamp == current_timestamp)
        return timestamp == current_timestamp
        
    
    def _klines_update(self, data, symbol):
        start_time = self.START_TIME if not data else self._klines_next_15m_timestamp(data)
        self._klines_get_and_update(start_time, symbol)
        return self._klines_from_file(symbol)
    
    def _klines_get_and_update(self, startTime, symbol, interval = "15m", limit = 1000):

        data = self._get_klines_from_api(startTime, symbol)
        if data:
            self._klines_to_file(symbol, data)
        else:
            self.futures_symbols.remove(symbol)

    def _get_klines_from_api(self, startTime, symbol, interval = "15m", limit = 1000):

        response = self.req.get(self.klines_url(symbol, startTime, interval, limit))
        if response.status_code != 200:
            print("{} eror: {}".format(symbol, response.content))
            return None
        return response.json()
 
    
    def _klines_from_file(self, symbol):
    
        try:
            filename = self._create_file_name(symbol.upper())
            if os.path.getsize(filename) == 0:
                return None
            with open(filename, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            return None
    
            
    def _klines_to_file(self, symbol, data):
        filename = self._create_file_name(symbol.upper())
        
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
            
        with open(filename, "a+", encoding ="utf-8") as f:
            if os.path.getsize(filename) != 0:
                self._dump_each(data, f)
            else:
                json.dump(data, f, ensure_ascii=False)
    
    def _dump_each(self, data, f):
        #data: a list of candles
        #f: the opened json file in a+ mode
        #process: append each candle into f
        
        #step 1: retrieve and remove last character in f
        
        f.seek(f.tell()-1, 0)
        last_character = f.read()
        
        f.seek(f.tell()-1, 0)
        f.truncate()
        
        #step 2: loop candles and append to f for example: ", []"
        for candle in data:
            target = "," + json.dumps(candle)
            f.write(target)
            
        
        #step 3: enclose f with the last character retrieved in step 1
        f.write(last_character)
            
    def _create_file_name(self, symbol):
        filename = "../jsondata/klines/" + symbol.upper() + ".json"
        filename = os.path.normpath(os.path.join(os.path.dirname(__file__), filename))
        return filename
            
    
    def _klines_next_15m_timestamp(self, klines):
        last = klines[-1]
        timestamp = int(last[0]/1000)
        
        print("last klines is: {}, next klines = {}".format(datetime.datetime.fromtimestamp(timestamp), datetime.datetime.fromtimestamp(int(timestamp + 15*60))))
        return int(timestamp + 15*60)
    
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
            
    def stop(self):
        self.running = False
        
    
