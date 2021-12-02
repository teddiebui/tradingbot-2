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


        
        self.START_TIME = int(time.time()) - (360 * 24 * 60 * 60) #360: days ago in timestamp
        self.FUTURES_SYMBOLS = []
        self.SYMBOLS = []
        self.KLINES = {}
        self.STABLE_COINS = set(["AUD", "BIDR", "BRL", "EUR", "GBP", "RUB", "TRY", "TUSD", "USDC", "DAI", "IDRT", "UAH", "NGN", "VAI", "USDP", "USDSB"])
        self.MAX_THRESH_HOLD = 2880


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
        if not self.KLINES:
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
                #stemp 4: refine the klines and load into memory
                try:              
                    self._build_klines_from_array(data, klines = self.KLINES[symbol])
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
        _data = self._get_klines_from_api(startTime + 15*60, symbol)

        if not _data:
            return []

        return _data + self._kline_update(symbol, self._kline_get_timestamp(_data[-1]))

    def _get_klines_from_api(self, startTime, symbol, interval = "15m", limit = 1000):

        response = self.req.get(self.klines_url(symbol, startTime, self._kline_get_endTime(), interval, limit))

        if response.status_code != 200:
            print("{} error: {}".format(symbol, response.content))
            return []
        
        data = response.json()

        if not data: 
            print("{} STOPPED TRADING ON BINANCE, REMOVE FROM LIST NOW".format(symbol.replace("USDT", "/USDT")))
            self.SYMBOLS.remove(symbol)
            return []
        return data 
    
    def _klines_up_to_date(self, startTime):
        endTime = self._kline_get_endTime()

        _d = datetime.datetime.fromtimestamp(startTime)
        _d = _d.replace(microsecond= 0, second = 0, minute = _d.minute // 15 * 15)
        return endTime == _d.timestamp()

    def _kline_get_endTime(self):
        d = datetime.datetime.now()
        d = d.replace(microsecond= 0, second = 0, minute = d.minute // 15 * 15)

        return int(d.timestamp() - 15*60)

    def _kline_get_timestamp(self, kline):
        return int(kline[0]/1000)

    
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
            

    def _build_klines_from_array(self, data, klines = None):

        candle_15m = klines['15m'] if klines else []
        candle_1h = klines['1h'] if klines else []
        candle_4h = klines['4h'] if klines else []
        candle_1d = klines['1d'] if klines else []
        candle_1w = klines['1w'] if klines else []

        if len(data) > 0:
            for i in data[-self.MAX_THRESH_HOLD:]:
                
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
                candle_15m.append(candle.copy())
                while len(candle_15m) >= self.MAX_THRESH_HOLD:
                    del candle_15m[0]
            
                #1h
                if t.minute == 0:
                    candle_1h.append(candle.copy())
                else:
                    if len(candle_1h) > 0:
                        self._build_merge_candle(candle, candle_1h[-1])
                while len(candle_1h) >= self.MAX_THRESH_HOLD:
                    del candle_1h[0]
                #4h
                if t.minute == 0 and t.hour % 4 == 0:
                    candle_4h.append(candle.copy())
                else:
                    if len(candle_4h) > 0:
                        self._build_merge_candle(candle, candle_4h[-1])
                while len(candle_4h) >= self.MAX_THRESH_HOLD:
                    del candle_4h[0]

                #1d
                if t.minute == 0 and t.hour == 8:
                    candle_1d.append(candle.copy())
                else:
                    if len(candle_1d) > 0:
                        self._build_merge_candle(candle, candle_1d[-1])
                while len(candle_1d) >= self.MAX_THRESH_HOLD:
                    del candle_1d[0]

                #1w
                if t.minute == 0 and t.hour == 8 and (t.timestamp()/60/60/24) % 7 == 4:
                    candle_1w.append(candle.copy())
                else:
                    if len(candle_1w) > 0:
                        self._build_merge_candle(candle, candle_1w[-1])
                
                while len(candle_1w) >= self.MAX_THRESH_HOLD:
                    del candle_1w[0]

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



            
    def stop(self):
        self.running = False
        print("OneTimeCrawler stopped")


        
    
