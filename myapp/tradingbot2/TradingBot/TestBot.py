# from myapp.tradingbot2.APIBot import OneTimeCrawler
import json
import threading
import datetime
import math
import time
import pprint
import requests

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

            
            if self.count == 0:
                for ticker in data:
                    symbol = ticker['s']
                    if not symbol in self.KLINES.keys():
                        continue
                    #DATA: 
                    # {
                    #     "e": "24hrMiniTicker",  // Event type
                    #     "E": 123456789,         // Event time
                    #     "s": "BNBBTC",          // Symbol
                    #     "c": "0.0025",          // Close price
                    #     "o": "0.0010",          // Open price
                    #     "h": "0.0025",          // High price
                    #     "l": "0.0010",          // Low price
                    #     "v": "10000",           // Total traded base asset volume
                    #     "q": "18"               // Total traded quote asset volume
                    # }
                    
                    time = round(ticker['E']/1000)
                    kline = self.KLINES[symbol]['15m'][-1]

                    kline['close'] = float(ticker['c'])
                    kline['high'] = float(ticker['c']) if float(ticker['c']) > kline['high'] else kline['high']
                    kline['low'] = float(ticker['c']) if float(ticker['c']) < kline['low'] else kline['low']

        
            self.count += 1
            if self.count > 3:
                self.count = 0
            

        self.symbols = self.oneTimeCrawler.get_symbols()
        self.futures_symbols = self.oneTimeCrawler.get_symbols()
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
            # data = self.oneTimeCrawler._kline_update(symbol, self.oneTimeCrawler.START_TIME)
            # if not data or not self.oneTimeCrawler._klines_up_to_date(self.oneTimeCrawler._kline_get_timestamp(data[-1])): #symbol has no latest trading, maybe it has been delisted
            #     self.symbols.remove(symbol)
            #     continue
            url = "https://api.binance.com/api/v3/klines?symbol={}&interval=15m&limit=1000".format(symbol.upper())
            data = req.get(url).json()
            a=time.time()

            if not data or not self._klines_up_to_date(data[-1][0]/1000):
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

            #step 4: generate indicator
            # self.WATCH_LIST[symbol] = self.generate_indicators(self.DESTRUCTURED_KLINES[symbol])

            
            print("total: {:.2f}|download: {:.2f}|refine: {:.2f}|destructure: {:.2f}| {}/{} {}".format(time.time() - total, a-total, b-a, c-b, self.symbols.index(symbol)+1, len(self.symbols), symbol.replace("USDT", "/USDT")))

        ##START WEBSOCKET
        # INSIDE WEBSOCKET ON_MESSAGE WILL RUN INDICATORSs
        if not self.webSocketCrawler.running:
            self.webSocketCrawler.start()

    
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

    
    def scenario_01(self):
        #update klines
        self.oneTimeCrawler.klines_update()
        self.indicators = {}




        self.diamond = []
        self.golden = []
        self.silver = []
        self.copper = []

        #loop thru symbols to generate indicators and check buy signal
        grand_total = time.time()
        for symbol in self.oneTimeCrawler.get_klines():

            total = time.time()
            append_time = 0
            ema10_time = 0
            ema50_time = 0
            ema200_time = 0
            rsi14_time = 0
            bbands_time = 0
            volume_osc_time = 0
            indicators_time= 0

            
            indicators = {}
            candles = self.oneTimeCrawler.get_klines()[symbol]
            # if not candles['15m']:
            #     continue
            for kline in candles:


                
                close = []
                volume = []
                
                z = time.time()
                for each in candles[kline]:
                    close.append(each['close'])
                    volume.append(each['volume'])
                append_time += time.time() - z
                
                #generate indicators
                ## notice: not persist into memory
                self.indicator.set_data(close)

                a = time.time()
                ema10 = self.indicator.ema(10)
                ema10_time = time.time() - a

                
                b = time.time()
                ema50 = self.indicator.ema(20)
                ema50_time = time.time() - b

                c = time.time()
                ema200 = self.indicator.ema(200)
                ema200_time = time.time() - c

                d = time.time()
                rsi14 = self.indicator.rsi()
                rsi14_time = time.time() - d


                e = time.time()
                bbands = self.indicator.bbands()
                bbands_time = time.time() - e

                self.indicator.set_data(volume)

                f = time.time()
                volume_osc = self.indicator.pvo(short=14, long=28)
                volume_osc_time = time.time() - f
                ##notce: persist into memory

                g = time.time()
                indicators[str(kline)] = {
                    "ema10": ema10,
                    "ema50": ema50,
                    "ema200": ema200,
                    "rsi14" : rsi14,
                    "bbands": bbands,
                    "volume_osc": volume_osc
                    }
                indicators_time += time.time() - g
            # print(indicators)
            self.indicators[symbol] = indicators

            #check indicators if entry is good
            can_buy_time = time.time()
            can_buy = self.check_if_can_buy(symbol, candles, indicators)
            can_buy_time = time.time() - can_buy_time


            #if entry is good, create buy order
            ##before creating order, check if this symbol is in position
            check_position_time = time.time()
            currently_in_position = symbol in self.orderManager.IN_POSITION if symbol in self.oneTimeCrawler.get_futures_symbols() else symbol in self.orderManager.IN_HOLDING
            check_position_time = time.time() - check_position_time

            total = time.time() - total

            if currently_in_position:
                self.orderManager.test_check_order_status(symbol)
            if not currently_in_position and can_buy:
                pass

            # print(" total: {:.4f}|append: {:.4f}|ema10: {:.4f}|ema50: {:.4f}|ema200: {:.4f}|rsi14: {:.4f}|osc: {:.4f}|bband: {:.4f}|can_buy: {:.4f}|indicators: {:.4f}|indicators: {:.4f} {}".format(
            #     total, append_time, ema10_time, ema50_time, ema200_time, rsi14_time, volume_osc_time, bbands_time, can_buy_time, indicators_time, check_position_time, symbol.replace("USDT", "/USDT")
            # ))

        print("diamond: ", self.diamond)
        print("golden: ", self.golden)
        print("silver: ", self.silver)
        print("copper: ", self.copper)
      

        grand_total = time.time() - grand_total
        print("grand total time: {:.4f}".format(grand_total))

    def check_if_can_buy(self, symbol, candles, indicators):
        UPPER_BOUND = 70
        LOWER_BOUND = 30

        green_4h = []
        green_1h = []
        green_15m = []


        try:
            candle = candles['4h'][-1]
            if candle['close']/candle['open']*100 - 100 >= 5:
                print("close/open: ", candle['close']/candle['open']*100 - 100)
                self.copper.append(symbol)
                green_4h.append(symbol)
                candle = candles['1h'][-1]
                if candle['close']/candle['open']*100 - 100 >= 5:
                    print("close/open: ", candle['close']/candle['open']*100 - 100)
                    self.silver.append(symbol)
                    green_1h.append(symbol)
                    candle = candles['15m'][-1]

                    if candle['close']/candle['open']*100 - 100 >= 5:
                        print("close/open: ", candle['close']/candle['open']*100 - 100)
                        green_15m.append(symbol)
                        self.golden.append(symbol)
        except Exception as e:
            print(e)
            print("ERROR SYMBOL: " + symbol)

        

        return True

    def trailing_stop(self, symbol, orders, low):

        order = orders[0]
        stoploss_order = orders[-1]

        if float(self.orderManager.LAST_BUY_PRICE[symbol]) < low:

            cancelled_order = self.client.cancel_order(symbol= symbol.upper(), orderId=str(stoploss_order['orderId']))
            print("------DEBUG update_trailing_stop(): cancelled_order['status'], " + cancelled_order['status'])

            stoploss_price = low * (1 - self.orderManager.stop_loss)
            order_qty = order['executedQty']
            new_stoploss_order = self.orderManager.create_stoploss_order(order['symbol'], order_qty, stoploss_price)

            orders.append(new_stoploss_order)
            self.orderManager.LAST_BUY_PRICE = low
            return True

        return False

    
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
        
        if self.SCHEDULER:
            for each in self.SCHEDULER:
                print("canceling: ",each)
                each.cancel()

        if self.webSocketCrawler:
            self.webSocketCrawler.stop()
        
        super().stop()



        
        
if __name__ == "__main__":
    pass