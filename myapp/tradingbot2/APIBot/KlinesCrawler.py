import requests
import time
import datetime
import os
import json as json
import threading
import math

from pprint import pprint

class KlinesCrawler():

    def __init__(self, client):
        # AbstractCrawler.__init__(self)
        # GenericTradingBot.__init__(self)
        super().__init__()
        print("hi im One time crawler")
        self.client = client
        self.ws = None
        self.lock = threading.Lock()
        self.host = "https://api.binance.com"
        self.req = requests.Session()


        self.MAX_THRESH_HOLD = 1000
        self.START_TIME = self._kline_get_endTime() - (15*60) * self.MAX_THRESH_HOLD #365 days ago in timestamp
        self.FUTURES_SYMBOLS = []
        self.SYMBOLS = []
        self.KLINES = {}
        self.KLINES_MEMORY = {}
        self.STABLE_COINS = set(["AUD", "BIDR", "BRL", "EUR", "GBP", "RUB", "TRY", "TUSD", "USDC", "DAI", "IDRT", "UAH", "NGN", "VAI", "USDP", "USDS"])
        self.file = __file__
        


    def futures_get_symbols(self):
    
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

    def klines_update(self):
        #using Thread.Lock
        with self.lock:
            symbols = self.get_symbols()
            total = 0 #timestamp
            for symbol in symbols:
                
                #step 1: get last timestamp to check up to date 
                a = time.time()
                try:
                    #read timestamp from memory
                    latest_klines = self.KLINES_MEMORY[symbol][-1]
                except KeyError:
                    #read klines from storage
                    self.KLINES_MEMORY[symbol] = self._klines_from_file(symbol)
                    if self.KLINES_MEMORY[symbol]:
                        latest_klines = self.KLINES_MEMORY[symbol][-1]
                        startTime = self._kline_get_timestamp(latest_klines)
                    else:
                        #start over if no klines in storage
                        startTime = self.START_TIME
                b = time.time()



                #step 2: update if not up to date
                if startTime == self.START_TIME or not self._klines_up_to_date(latest_klines[0]/1000):
                    data = self._kline_update(symbol, startTime)
                    if not data:
                        symbols.remove(symbol)
                        print("symbol %s is delisted, remove from list now..." % (symbol))
                        continue

                    c = time.time()
                    #step 3: append klines to json file
                    self._klines_to_file(symbol, data)
                    d = time.time()

                
                    #step 4: save to memory
                    self.KLINES_MEMORY[symbol] = data


                    print("total: {:.2f}|read: {:.2f}|update: {:.2f}|append: {:.2f} - {} - {}/{}".format(
                        d-a, b-a, c-b, d-c, symbol.replace("USDT", "/USDT"), symbols.index(symbol) + 1, len(self.SYMBOLS)
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

        # if not data: 
            # print("{} STOPPED TRADING ON BINANCE, REMOVE FROM LIST NOW".format(symbol.replace("USDT", "/USDT")))
            # self.SYMBOLS.remove(symbol)
            # return []
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
        filename = os.path.normpath(os.path.join(os.path.dirname(self.file), filename))
        return filename

    
    def _timestamp(self, start_day):
        dt = datetime.now()
        t = (math.floor(time.time()) - start_day * 24 * 60 * 60)
        if start_day == 0:
            t = t - 15*60
        return t * 1000
        # dt = dt.replace(second = 0, microsecond = 0, minute = dt.minute // 15 * 15, day = dt.day - start_day)
        # return str(int(dt.timestamp()*1000))
    
    def klines_url(self, symbol, startTime, endTime, inverval, limit):
        url = self.host + "/api/v3/klines?symbol={}&interval={}&limit={}&startTime={}&endTime={}".format(symbol, "15m", limit, startTime * 1000, endTime * 1000)
        # print(url)
        return url
                      

    def _scheduler(self, callback, interval):
        
        remaining_time =  2
        self.scheduler = threading.Timer(interval= remaining_time, function = self._scheduler_handler, args=(callback, interval))
        self.scheduler.start()

        return self.scheduler
    
    def _scheduler_handler(self, callback, interval):

        try:
            print("now execution: ", math.floor(time.time()), " now: ", datetime.datetime.now())
            callback()
        except Exception as e:
            raise e
        

        dt = datetime.datetime.now()
        dt = dt.replace(second = 0, microsecond = 0, minute = dt.minute // 15 * 15)
        future_time = math.floor(dt.timestamp()) + interval + 2
        remaining_time = future_time - time.time()
        print("next interval: {} - {}".format(remaining_time, datetime.datetime.fromtimestamp(future_time)))

        self.scheduler = threading.Timer(interval = remaining_time, function = self._scheduler_handler, args=(callback, interval))
        self.scheduler.start()

    def stop(self):
        self.running = False
        if self.scheduler:
            self.scheduler.cancel()
        print("OneTimeCrawler stopped")

if __name__ == "__main__":
    from binance.enums import *
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")

    a = KlinesCrawler(client)
    # a.klines_update()
    
    scheduler = a._scheduler(a.klines_update, 15*60)


        
    
