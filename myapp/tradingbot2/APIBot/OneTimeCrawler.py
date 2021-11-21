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
        
        self.futures_klines = {}
        self.klines = {}
        self.req = requests.Session()
        self.running = False
        self.START_TIME = int(time.time()) - (60 * 24 * 60 * 60) #60: days ago in timestamp
        self.FUTURES_SYMBOLS = []
        self.SYMBOLS = []
        self.FUTURES_KLINES = {}
        self.KLINES = {}
        self.STABLE_COINS = set(["AUD", "BIDR", "BRL", "EUR", "GBP", "RUB", "TRY", "TUSD", "USDC", "DAI", "IDRT", "UAH", "NGN", "VAI", "USDP"])
        self._init()

        self.temp_count = 0
    
    def _init(self):
        pass
    
    def start(self):
        self.running = True
        self.get_symbols()
        self.get_futures_symbols()
        self.get_klines()

    def get_klines(self, futures = False):
        self.target_symbols = self.get_futures_symbols() if futures else self.get_symbols()
        symbols = self.target_symbols
        klines = self.FUTURES_KLINES if futures else self.KLINES


        if len(klines) == 0:

            total = 0
            read = 0
            update  = 0
            refining = 0

            for symbol in symbols[:]:
                flag = False
                _total = time.time()
                _read = 0
                _update = 0
                _refining = 0

                b=time.time()
                _klines = self._klines_from_file(symbol)
                data = []
                c=time.time()
                _read += c-b
                while True: #customized do-while
                    if not self._klines_up_to_date(symbol, _klines if not flag else data):
                        d=time.time()
                        flag = True
                        json = self._klines_update(symbol, _klines if not flag else data)
                        
                        if json:
                            data += json
                            __update = time.time() - d
                            _update += __update
                            print(".........read: {:.2f}|update: {:.2f}| {}/{}"
                            .format(c-b, __update, symbols.index(symbol)+1,len(symbols)))
                        else:
                            print("ATTEMPT TO UPDATE FAILED - MAYBE THE COIN HAS BEEN DELISTED")
                            break
                    else:
                        print("THE TOKEN IS UP TO DATED")
                        _klines += data
                        aa=time.time()
                        klines[symbol] = self._build_klines_from_array(_klines)
                        bb=time.time()

                        self._klines_to_file(symbol, data)

                        _refining += bb - aa
                        _total = time.time() - _total
                        print("total: {:.2f}|read: {:.2f}|update: {:.2f}|refining: {:.2f}|len: {}| {}/{}"
                        .format(_total, _read, _update, _refining, len(_klines), symbols.index(symbol)+1,len(symbols)))
                        
                        read += _read
                        update += _update
                        refining += _refining
                        total += _total
                        break       
        print("total: {:.2f}|total-read: {:.2f}|total-update: {:.2f}|total-refining: {:.2f}|{}/{}"
        .format(total, read, update, refining, symbols.index(symbol) + 1,len(symbols))) 
        return klines

       
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
                    and symbol not in self.STABLE_COINS):
                    self.SYMBOLS.append(symbol)
        
        return self.SYMBOLS
    
    def _klines_up_to_date(self,symbol, klines):
        if not klines:
            return False
        
        last = klines[-1]
        # pprint(klines)
        timestamp = int(last[0]/1000)
        
        now = datetime.datetime.now()
        _now = now.replace(microsecond = 0, second = 0, minute = now.minute // 15 * 15)
        current_timestamp = int(_now.timestamp())
        
        print("...{} UP TO DATE? {} - {}".format(symbol.replace("USDT","/USDT"), datetime.datetime.fromtimestamp(timestamp), datetime.datetime.fromtimestamp(current_timestamp)))

        #return type: boolean
        return timestamp == current_timestamp
        
    
    def _klines_update(self, symbol, klines):
        start_time = self.START_TIME if not klines else self._klines_next_15m_timestamp(klines)
        return self._klines_get_and_update(start_time, symbol)
    
    def _klines_get_and_update(self, startTime, symbol, interval = "15m", limit = 1000):
        data = self._get_klines_from_api(startTime, symbol)
        if not data:
            self.target_symbols.remove(symbol)
        return data 

    def _get_klines_from_api(self, startTime, symbol, interval = "15m", limit = 1000):

        response = self.req.get(self.klines_url(symbol, startTime, interval, limit))
        if response.status_code != 200:
            print("{} error: {}".format(symbol, response.content))
            return []
        
        data = response.json()
        return data if data else print("DEBUG: --- THIS SYMBOL {} DOESN'T HAVE CANDLE LINES: {}".format(symbol, data))
 
    
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
            
    
    def _klines_next_15m_timestamp(self, klines):
        last = klines[-1]
        timestamp = int(last[0]/1000)
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


        
    
