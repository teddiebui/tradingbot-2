# from myapp.tradingbot2.APIBot import OneTimeCrawler
import json
import threading
import datetime
import math
import time
import pprint
import requests
import traceback

from collections import defaultdict, deque

from ..APIBot.WebSocketCrawler import WebSocketCrawler
from ..TradingBot.GenericTradingBot import GenericTradingBot


class TestBot(GenericTradingBot):
    def __init__(self, client, oneTimeCrawler = None, orderManager = None, indicator = None):
        super().__init__()
        self.client = client

        self.oneTimeCrawler = oneTimeCrawler
        self.orderManager = orderManager
        self.indicator = indicator
        self.webSocketCrawler = WebSocketCrawler()
        

        self.SCHEDULER = [None, ]
        self.DESTRUCTURED_KLINES = {}
        self.KLINES = {}
        self.WATCH_LIST = []

        self.symbols = []
        self.futures_klines = []

    def _main(self):
        ##TODO: write logic for bots
        ##trading bot start
        self.scenario_02()

    def scenario_02(self):
        def _callback(self, ws, msg):
            data = json.loads(msg)

            spot = {}
            futures = {}
            rsi={}
            
            try:
                if self.count == 0:
                    for ticker in data:
                        symbol = ticker['s']
                        if not symbol in self.KLINES.keys():
                            continue

                        candle = {
                            'time': ticker['e'],
                            'open': float(ticker['o']),
                            'high': float(ticker['h']),
                            'low': float(ticker['l']),
                            'close': float(ticker['c']),
                            'volume': 0
                        }
                        for k,v in self.KLINES[symbol].items():
                            last_candle = v[-1]
                            ##variable initiation
                            if k not in spot.keys():
                                spot[k] = {}
                            if k not in futures.keys(): 
                                futures[k] = {}
                            if k not in rsi.keys(): 
                                rsi[k] = {}

                            ##merging BUG: need to fix
                            self._merge_candle(candle.copy(), last_candle)   

                            ##check change
                            change = round(last_candle['close']/last_candle['open']*100 - 100, 2)
                            if change >= 5:
                                spot[k][symbol]=change
                                if symbol in self.futures_symbols:
                                    futures[k][symbol] = change

                            ##check rsi
                            self.indicator.set_data([i['close'] for i in v])
                            rsi_list = self.indicator.rsi()
                            if rsi_list[-1]<30:
                                rsi[k][symbol]=rsi_list[-1]
                                if symbol in self.futures_symbols:
                                    rsi[k][symbol] = rsi_list[-1]
                        #UPDATE CURRENT FUTURES ORDER
                        self.orderManager.futures_update_order(symbol, candle['close'])

                        ##GENERATE FUTURES SIGNAL
                        signal = symbol in futures['15m'] and symbol in futures['1h'] and symbol in futures['4h']
                        signal = symbol in futures['1h'] and symbol in futures['4h']
                            
                        #PLACE FUTURES ORDER
                        if signal == True:
                            order = self.orderManager.futures_create_order(symbol, candle['close'])
                            if order != None:
                                print("Place futures order " + symbol + "successfully")

                        
                        #UPDATE CURRENT ORDER
                        self.orderManager.update_order(symbol, candle['close'])

                        ##GENERATE FUTURES SIGNAL
                        signal = symbol in spot['15m'] and symbol in spot['1h'] and symbol in spot['4h']
                            
                        #PLACE ORDER
                        if signal == True:
                            order = self.orderManager.create_order(symbol, 12)
                            if order != None:
                                print("Place order " + symbol + "successfully")
                self.count += 1
                if self.count > 3:
                    self.count = 0
            except Exception as e:
                traceback.print_exc()
                print(symbol)
                self.stop()

        self.symbols = self.oneTimeCrawler.get_symbols()
        self.futures_symbols = self.oneTimeCrawler.futures_get_symbols()
        self.MAX_THRESH_HOLD = self.oneTimeCrawler.MAX_THRESH_HOLD
        self.webSocketCrawler.callback = lambda ws, msg: _callback(self, ws, msg)
        

        next_15m_candle_scheduler = self._scheduler(self.scenario_02_callback, 15*60) 
        self.SCHEDULER[0] = next_15m_candle_scheduler

    def scenario_02_callback(self):
        self.count = 0
        req = requests.Session()
        #END PREVIOUS WEBSOCKET
        if self.webSocketCrawler.running:
            self.webSocketCrawler.stop()

        for symbol in self.symbols:
            total=time.time()
            #step 1: crawl api
            url = "https://api.binance.com/api/v3/klines?symbol={}&interval=15m&limit=1000".format(symbol.upper())
            data = req.get(url).json()
            # data = requests.Session().get(url).json()
            a=time.time()

            if not data or not self._klines_up_to_date(data[-1][0]/1000) or len(data) < 500:
                self.symbols.remove(symbol)
                continue
            #step 2: refine raw klines
            try:
                self.KLINES[symbol] = self._build_klines_from_array(data, self.KLINES[symbol])
            except KeyError:
                self.KLINES[symbol] = self._build_klines_from_array(data)
            b=time.time()
            #step 3: destructure refined klines
            self.DESTRUCTURED_KLINES[symbol] = self.destructure_klines(symbol, self.KLINES[symbol])
            c=time.time()
     
            # print("total: {:.2f}|download: {:.2f}|refine: {:.2f}|destructure: {:.2f}| {}/{} {}".format(time.time() - total, a-total, b-a, c-b, self.symbols.index(symbol)+1, len(self.symbols), symbol.replace("USDT", "/USDT")))
        ##START WEBSOCKET
        # INSIDE WEBSOCKET ON_MESSAGE WILL RUN INDICATORSs
        if not self.webSocketCrawler.running:
            self.webSocketCrawler.start()

    def _merge_candle(self, candle, merging_candle):
        merging_candle['high'] = candle['close'] if candle['close'] > merging_candle['high'] else merging_candle['high']
        merging_candle['low'] = candle['close'] if candle['close'] < merging_candle['low'] else merging_candle['low']
        merging_candle['close'] = candle['close']

    
    def destructure_klines(self, symbol, klines):
        _temp = {}

        for timeframe, _klines in klines.items():
            
            try:
                time = self.DESTRUCTURED_KLINES[symbol][timeframe]['time']
                open = self.DESTRUCTURED_KLINES[symbol][timeframe]['open']
                high = self.DESTRUCTURED_KLINES[symbol][timeframe]['high']
                low = self.DESTRUCTURED_KLINES[symbol][timeframe]['low']
                close = self.DESTRUCTURED_KLINES[symbol][timeframe]['close']
                volume = self.DESTRUCTURED_KLINES[symbol][timeframe]['volume']
                buyVolume = self.DESTRUCTURED_KLINES[symbol][timeframe]['buyVolume']

            except KeyError:
                time = [] 
                open = []
                high = []
                low = []
                close = []
                volume = []
                buyVolume = []

            for i in _klines:
                    time.append(i['time'])
                    open.append(i['open'])
                    high.append(i['high'])
                    low.append(i['low'])
                    close.append(i['close'])
                    volume.append(i['volume'])
                    buyVolume.append(i['buyVolume'])

            _temp[timeframe] = {
                'time': time,
                'open': open,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'buyVolume': buyVolume,
            }
        return _temp

    def generate_indicators(self, klines):
        

        return None

    
    
    
    def _scheduler(self, callback, interval):
        
        remaining_time =  2
        scheduler = threading.Timer(interval= remaining_time, function = self._scheduler_handler, args=(callback, interval))
        scheduler.start()

        return scheduler
    
    def _scheduler_handler(self, callback, interval):

        try:
            print("now execution: ", math.floor(time.time()), " now: ", datetime.datetime.now())
            callback()
        except Exception as e:
            raise e
        

        dt = datetime.datetime.now()
        dt = dt.replace(second = 0, microsecond = 0, minute = dt.minute // 15 * 15)
        future_time = math.floor(dt.timestamp()) + interval + self.buffered
        remaining_time = future_time - time.time()
        print("next interval: {} - {}".format(remaining_time, datetime.datetime.fromtimestamp(future_time)))

        scheduler = threading.Timer(interval = remaining_time, function = self._scheduler_handler, args=(callback, interval))
        scheduler.start()
        
        self.SCHEDULER[0] = scheduler
        
    def _klines_up_to_date(self, startTime):
        d = datetime.datetime.now()
        endTime = d.replace(microsecond= 0, second = 0, minute = d.minute // 15 * 15)

        _d = datetime.datetime.fromtimestamp(startTime)
        _d = _d.replace(microsecond= 0, second = 0, minute = _d.minute // 15 * 15)
        return endTime.timestamp() == _d.timestamp()

    def _build_klines_from_array(self, data, klines = None):

        candle_15m = klines['15m'] if klines else []
        candle_1h = klines['1h'] if klines else []
        candle_4h = klines['4h'] if klines else []
        candle_1d = klines['1d'] if klines else []

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
                candle_15m.append(dict.copy(candle))
                while len(candle_15m) >= self.MAX_THRESH_HOLD:
                    del candle_15m[0]
            
                #1h
                if t.minute == 0:
                    candle_1h.append(dict.copy(candle))
                else:
                    if len(candle_1h) > 0:
                        self._build_merge_candle(candle, candle_1h[-1])
                while len(candle_1h) >= self.MAX_THRESH_HOLD:
                    del candle_1h[0]

                #4h
                if t.minute == 0 and t.hour % 4 == 0:
                    candle_4h.append(dict.copy(candle))
                else:
                    if len(candle_4h) > 0:
                        self._build_merge_candle(candle, candle_4h[-1])

                while len(candle_4h) >= self.MAX_THRESH_HOLD:
                    del candle_4h[0]

                #1d
                if t.minute == 0 and t.hour == 8:
                    candle_1d.append(dict.copy(candle))
                else:
                    if len(candle_1d) > 0:
                        self._build_merge_candle(candle, candle_1d[-1])
                while len(candle_1d) >= self.MAX_THRESH_HOLD:
                    del candle_1d[0]

        return {"15m": candle_15m, "1h" : candle_1h, "4h" : candle_4h, "1d": candle_1d}
    
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
        
        if self.SCHEDULER:
            for each in self.SCHEDULER:
                print("canceling: ",each)
                each.cancel()

        if self.webSocketCrawler:
            self.webSocketCrawler.stop()
        
        super().stop()



        
        
if __name__ == "__main__":
    pass