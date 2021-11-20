import threading
import websocket
import time
import pprint
import json
import datetime
import traceback

from collections import deque
from math import floor


from binance.client import Client

if __name__ == "__main__":
    from klineCrawlerHelper import KlineCrawlerHelper
else:
    from .klineCrawlerHelper import KlineCrawlerHelper


class CandleCrawler:

    def __init__(self, client, symbol):

        self.client = client
        self.symbol = symbol
        self.kline_crawler_helper = KlineCrawlerHelper()

        self.WEBSOCKETS = [
            "wss://stream.binance.com:9443/ws/{}@kline_1m".format(symbol.lower()),
            "wss://stream.binance.com:9443/ws/{}@kline_15m".format(symbol.lower()),
            "wss://stream.binance.com:9443/ws/!miniTicker@arr"
            ]
        
        self.FWEBSOCKETS = [
            "wss://fstream.binance.com/ws/!markPrice@arr@1s".format(symbol.lower())
        ]
        

        
        self.candles_15m, self.candles_1h, self.candles_4h = self.build_candle(symbol)

        
        
        
        
        
        websocket.enableTrace(True)
        
        self.is_running = False
        self.WS = []
        self.TIMERS = []
        self.THREADS = []
        self.spot_symbols = []
        self.futures_symbols = []
        self.data={}
        
        self.watch_list = {}
        self.fomo_watch_list = {}
        self.count = 0
        
       
        


    def candle_initiation(self,interval, time):

        # return  a list
        klines = self.client.get_historical_klines(self.symbol.upper(), interval, time)

        return [{'time': float(i[0])/1000,
                'open' : float(i[1]), 
                'high' : float(i[2]), 
                'low' : float(i[3]), 
                'close' :float(i[4])
                } for i in klines]
        
    def build_candle(self, symbol):

        candle_15m = []
        candle_1h = []
        candle_4h = []
        
        klines = self.client.get_historical_klines(symbol.upper(), Client.KLINE_INTERVAL_15MINUTE , "3 day ago UTC")

        for i in klines[:]:
            
            t = datetime.datetime.fromtimestamp(i[0]/1000)
            
            candle = {'time': float(i[0])/1000,
                'open' : float(i[1]), 
                'high' : float(i[2]), 
                'low' : float(i[3]), 
                'close' :float(i[4])
                }
                
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

        return [candle_15m, candle_1h, candle_4h]
    
    def build_candle_from_array(self, array):
        #array here is a list of candle lines

        candle_15m = []
        candle_1h = []
        candle_4h = []
        

        for i in array[:]:
            
            t = datetime.datetime.fromtimestamp(i[0]/1000)
            
            candle = {'time': float(i[0])/1000,
                'open' : float(i[1]), 
                'high' : float(i[2]), 
                'low' : float(i[3]), 
                'close' :float(i[4])
                }
                
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

        return [candle_15m, candle_1h, candle_4h]
        

    def start_crawling(self, callback1 = None, callback2 = None):

        def _private_on_message(ws, msg, callback1 = None, callback2 = None):

            msg = json.loads(msg)

            candle =    {'time': float(msg['k']['t'])/1000,
                            'open' : float(msg['k']['o']), 
                            'high' : float(msg['k']['h']), 
                            'low' : float(msg['k']['l']), 
                            'close' :float(msg['k']['c'])}
            
            self.candles_15m[-1] = candle
            try:
                if msg['k']['x'] == True:
                    del self.candles_15m[0]
                    self.candles_15m.append(candle)
                    
                    
                    try:
                        callback1()
                    except Exception as e:
                        print("error from 'callback1' in 'candleCrawler'...see below: ") 
                        traceback.print_tb(e.__traceback__)
                    
                    
                    
            except Exception as e:
                print("error from 'start_crawling' in 'candleCrawler'...see below: ") 
                print(repr(e))
                      
            return
        
        self.is_running = True
                
        thread = threading.Thread(target=self._start_crawling_handler, args=(self.WEBSOCKETS[1], _private_on_message, callback1, callback2))
        thread.start()
        self.THREADS.append(thread)
        
    def _timerHelper(self, function):
        print("timestamp: ", time.time(), " now: ", datetime.datetime.now())
        timer = threading.Timer(interval= 60*15, function = self._timerHelper, args=(function,))
        self.TIMERS.append(timer)
        timer.start()
        
        function()
    
    def _next_15m_timer(self, callback):
        dt = datetime.datetime.now()
        dt = dt.replace(second = 0, microsecond = 0, minute = dt.minute // 15 * 15)
        print("next interval: ", dt.timestamp() + 15*60 - time.time())
        timer = threading.Timer(interval=dt.timestamp() + 15*60 - time.time(), function = self._timerHelper, args=(callback,))
        self.TIMERS.append(timer)
        
        return timer
        
        
    def start_all_symbol(self, callback1 = None, callback2 = None):
        
        
        
        def _private_on_message(ws, msg, callback1 = None,  callback2 = None):
            # timer = threading.Timer(interval=1, function = self.dumb)
            # timer.start()
            # print("...sent timer")
            try:
                msg = json.loads(msg)
                
                # pprint.pprint(msg[0])
                t = datetime.datetime.fromtimestamp(msg[0]['E']/1000)
                if floor(t.second) % 2 == 0:
                    for i in msg:
                        try:
                            if i['s'].endswith("USDT"):

                                symbol = i['s'].upper()
                                timestamp = msg[-1]['E']/1000
                                candles_15m = self.data[symbol][0]
                                
                                self.data[symbol][0][-1]['close'] = round(float(i['c']),4) #change close price of the last candles until every 15min
                                self.data[symbol][1][-1]['close'] = round(float(i['c']),4) #change close price of the last candles until every 15min
                                self.data[symbol][2][-1]['close'] = round(float(i['c']),4) #change close price of the last candles until every 15min
                                self.data[symbol][0][-1]['time'] = timestamp #change close price of the last candles until every 15min
                                self.data[symbol][1][-1]['time'] = timestamp #change close price of the last candles until every 15min
                                self.data[symbol][2][-1]['time'] = timestamp #change close price of the last candles until every 15min
                                
                                # if symbol == "BTCUSDT":
                                    # pprint.pprint(self.data[symbol][0][-5:])
                                    # pprint.pprint(self.data[symbol][1][-5:])
                                    # pprint.pprint(self.data[symbol][2][-5:])
                                    
                                if callback1 != None:
                                    result = callback1(symbol, candles_15m) #return a list or an empty list
                                    if len(result) > 0:
                                        self.watch_list[symbol] = result
                                        
                                
                                if callback2 != None:
                                    change = callback2(symbol, self.data[symbol])
                                    self.fomo_watch_list[symbol] = change

                                    
                        except KeyError:
                            pass
                
                if len(self.watch_list) > 0 :
                    for symbol, rsi in self.watch_list.items():
                        print("\t{", symbol, str(rsi[1:]), "}")
                    print("\ttime: ", t)
                    self.watch_list = {}
                    print("---------------")
                if floor(t.second) == 0:
                    print("...hi, 1 minute passed away - ", t)
                if t.minute % 15 == 0 and floor(t.second) == 0:
                    print("...15min passed away.. ", str(t))
            except Exception as e:
                print("error websocket _pricate_on_message")
                # import traceback
                # traceback.print_tb(e.__traceback__)
                # print(repr(e))
        


        kline15mTimer = self._next_15m_timer(self._get_all_symbol_futures)
        kline15mTimer.start()
        
        self._get_all_symbol_futures()
        # self._get_all_symbol_futures()            
        
        print("OKAY...START NOW")
        self.is_running = True
        self.THREADS.append(threading.Thread(target=self._start_crawling_handler, args=(self.WEBSOCKETS[2], _private_on_message, callback1, callback2)))
        return
        self.THREADS[-1].start()
        
    def _get_all_symbol_futures(self):
        self.futures_symbols = [i['symbol'] for i in self.client.futures_ticker() if i['symbol'].endswith("USDT") and i['count'] != 1 and not i['symbol'].startswith("DEFI")]
        data = self.kline_crawler_helper.mainloop(self.futures_symbols, self.build_candle_from_array)
        self.data=data
            
        
    def _get_all_symbol_spot(self):
        self.spot_symbols = [i['symbol'] for i in self.client.get_ticker() if i['symbol'].endswith("USDT") and i['count'] != 1 and "UPUSDT" not in i['symbol'] and "DOWNUSDT" not in i['symbol']]
        data = self.kline_crawler_helper.mainloop(symbols, self.spot_symbols)
        self.data=data
        
    def start_futures_all_tickers(self):
        
        self.is_running = True
        
        thread = threading.Thread(target=self._start_crawling_handler, args=(self.FWEBSOCKETS[0], self._futures_on_message))
        thread.start()
        self.THREADS.append(thread)


    def _start_crawling_handler(self, socket, callback, callback1 = None, callback2 = None):
        
        
        ws = websocket.WebSocketApp(socket,
                                            on_open = lambda ws: self._wss_on_open(ws),
                                            on_error = lambda ws, error: self._wss_on_error(ws, error),
                                            on_close = lambda ws: self._wss_on_close(ws),
                                            on_message = lambda ws,msg: callback(ws, msg, callback1, callback2))
        self.WS.append(ws)
        ws.run_forever()
        


    def _wss_on_open(self, ws):
        print("open")
        pass

    def _wss_on_close(self, ws):
        print("stopped")
        pass

    def _wss_on_error(self, ws, error):
        print("error: ", error)

    

    def _futures_on_message(self, ws, msg, callback1 = None, callback2 = None):
        print("hi...")
        msg = json.loads(msg)
        pprint.pprint(msg)
        

        # pprint.pprint([[datetime.datetime.fromtimestamp(i['time']), i['close']] for i in self.candles_15m[-7:]])

    def stop(self):
        pprint.pprint(self.WS)
        for i in self.WS:
            i.keep_running = False
            self.is_running = False
        print("candle crawler stopped")
        
        for timer in self.TIMERS:
            timer.cancel()
        self.kline_crawler_helper.stop()

if __name__ == "__main__":
    from binance.client import Client
    apiKey = "TFWFmx5lPFNkkQnEIQsl2596kr1errGmaabzC3bFWI17mifeIYmnBybtU4Opkkyp"
    apiSecret = "kBzXtdMQsOVCrfV9qwyCabshmyALX3ABNjzGJF2a7ZoHF7oh6lzh4gEuvHOwQBSR"
    client = Client(apiKey, apiSecret)
    
    crawler = CandleCrawler(client, "bnbusdt")
    
    
    
    
    
    tickers = client.futures_ticker()
    symbols = [i['symbol'] for i in tickers if i['symbol'].endswith("USDT") and i['count'] != 1 and not i['symbol'].startswith("DEFI")]
    helper = KlineCrawlerHelper()
    data = helper.mainloop(symbols)
    pprint.pprint(len(data))
    for i in data:
        print(i)
        break
    
    # pprint.pprint(helper.data)
    
    # try:
        # while True:
            # time.sleep(3)
    # except:
        # print(helper._data)
        # print(len(helper._data))
        # helper.stop()
    
    
    
    #####################################
    # from time import time
    # from time import sleep
    
    # a = time()
    # tickers = client.get_ticker()
    # b = time()
    # c = time()
    # tickers = [i for i in tickers if i['symbol'].endswith("USDT") if i['count'] != 1]
    # d = time()
    
    # total = time()
    # for symbol in tickers:
        # if symbol['count'] == 1:
            # pprint.pprint(symbol)
        # sleep(0.1)
    # total = time() - total
    # print("total time: ", total)
    
    
    
    
    # print("symbols total: ", len(tickers))
    # print("crawl ticker time: ", b-a)
    # print("filter timeL ", d-c)
    
    # pprint.pprint(symbols)
    ##########################################
    