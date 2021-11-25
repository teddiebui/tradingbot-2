from ..APIBot.AbstractCrawler import AbstractCrawler
from ..TradingBot.GenericTradingBot import GenericTradingBot


import requests
import time
import datetime
import os
import json as json
import threading
from pprint import pprint
class OneTimeCrawler(AbstractCrawler):

    def __init__(self, client):
        # AbstractCrawler.__init__(self)
        # GenericTradingBot.__init__(self)
        super().__init__()
        print("hi im One time crawler")
        self.client = client
        self.ws = None
        self.lock = threading.Lock()


        
        self.START_TIME = int(time.time()) - (360 * 24 * 60 * 60) #60: days ago in timestamp
        self.FUTURES_SYMBOLS = []
        self.SYMBOLS = []
        self.KLINES = {}
        self.STABLE_COINS = set(["AUD", "BIDR", "BRL", "EUR", "GBP", "RUB", "TRY", "TUSD", "USDC", "DAI", "IDRT", "UAH", "NGN", "VAI", "USDP"])

        if not self.SYMBOLS:
            self.get_symbols()
        
        if not self.FUTURES_SYMBOLS:
            self.get_futures_symbols()

        if not self.KLINES:
            self.get_klines()

    def get_futures_symbols(self):
    
        if len(self.FUTURES_SYMBOLS) == 0:
            symbols = set(self.SYMBOLS)
            tickers = self.client.futures_symbol_ticker()
            for each in tickers:
                symbol = each['symbol']
                if symbol in symbols:
                    self.FUTURES_SYMBOLS.append(symbol)
        return self.FUTURES_SYMBOLS
    
    
        
    def get_symbols(self):
        
        if len(self.SYMBOLS) == 0:
            prices = self.client.get_all_tickers()
            
            for each in prices:
                symbol = each['symbol']
                
                if (symbol.endswith("USDT") 
                    and not symbol.startswith("DEFI")
                    and not "UPUSDT" in symbol
                    and not "DOWNUSDT" in symbol
                    and not "BULLUSDT" in symbol
                    and not "BEARUSDT" in symbol
                    and symbol not in self.STABLE_COINS):
                    self.SYMBOLS.append(symbol)
        
        return self.SYMBOLS


    def get_klines(self):

        #try to update klines before returning it
        self.klines_update()
        return self.KLINES
    
    def klines_update(self):
        #using Thread.Lock
        with self.lock:
            symbols = self.get_symbols()[:]
            total = 0 #timestamp
            for symbol in symbols:
                
                #step 1: get last timestamp to check up to date 
                a = time.time()
                try:
                    #read timestamp from memory
                    _klines = self.KLINES[symbol]['15m'][-1]
                    startTime = int(_klines['time'])
                    # print("startTime: ", startTime)
                except KeyError:
                    #read timestamp from json file
                    _klines = self._klines_from_file(symbol)
                    startTime = self.START_TIME if not _klines else self._kline_get_timestamp(_klines[-1])
                except IndexError:
                    startTime = self.START_TIME
                b = time.time()
                #step 2: force for update until up to date, return empty list if up to date
                data = self._kline_update(symbol, startTime)
                c = time.time()
                #step 3: append klines to json file
                self._klines_to_file(symbol, data)
                d = time.time()
                #stemp 4: refine the klines and append to dictionary
                try:              
                    refined_klines = self._build_klines_from_array(data)
                    self.KLINES[symbol]['15m'] += refined_klines['15m']
                    self.KLINES[symbol]['1h'] += refined_klines['1h']
                    self.KLINES[symbol]['4h'] += refined_klines['4h']
                except KeyError:
                    self.KLINES[symbol] = self._build_klines_from_array(_klines + data)
                e = time.time()
                #debug
                print("total: {:.2f}|read: {:.2f}|update: {:.2f}|append: {:.2f}|refine: {:.2f} - {} - {}/{}".format(
                    e-a, b-a, c-b, d-c, e-d, symbol.replace("USDT", "/USDT"), symbols.index(symbol) + 1, len(self.SYMBOLS)
                ))
            print("done updating")

        

    def _kline_update(self, symbol, startTime):
        #startTime: ìn timestamp of python
        if self._klines_up_to_date(startTime):
            return []
        _data = self._get_klines_from_api(self._klines_next_15m_timestamp(startTime), symbol)

        if not _data:
            return []

        return _data + self._kline_update(symbol, self._kline_get_timestamp(_data[-1]))

    def _get_klines_from_api(self, startTime, symbol, interval = "15m", limit = 1000):

        response = self.req.get(self.klines_url(symbol, startTime, interval, limit))

        if response.status_code != 200:
            print("{} error: {}".format(symbol, response.content))
            return []
        
        data = response.json()

        if not data: 
            print("DEBUG: --- THIS SYMBOL {} DOESN'T HAVE CANDLE LINES: {}".format(symbol, data))
            return []
        return data 
    
    def _klines_up_to_date(self, startTime):
        d = datetime.datetime.now()
        d = d.replace(microsecond= 0, second = 0, minute = d.minute // 15 * 15)

        _d = datetime.datetime.fromtimestamp(startTime)
        _d = _d.replace(microsecond= 0, second = 0, minute = _d.minute // 15 * 15)

        return d.timestamp() == _d.timestamp()

    def _kline_get_timestamp(self, kline):
        return int(kline[0]/1000)

    def _klines_next_15m_timestamp(self, timestamp):
        return timestamp + 15*60

    
 
    
    def _klines_from_file(self, symbol):
    
        try:
            filename = self._create_file_name(symbol.upper())
            if os.path.getsize(filename) == 0:
                return None
            with open(filename, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            return []
    
            
    def _klines_to_file(self, symbol, data):
        if not data:
            return None
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
            
    
    def _build_klines_from_array(self, array):
    
        #array here is a list of candle lines
        candle_15m = []
        candle_1h = []
        candle_4h = []
        
        if len(array) > 0:
            for i in array[:]:
                
                t = datetime.datetime.fromtimestamp(i[0]/1000)
                
                candle = {'time': int(float(i[0])/1000),
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
        print("OneTimeCrawler stopped")


        
    
