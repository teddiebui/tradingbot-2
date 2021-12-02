# from myapp.tradingbot2.APIBot import OneTimeCrawler
from ..TradingBot.GenericTradingBot import GenericTradingBot
from ..APIBot import OneTimeCrawler
from ..OrderManager import OrderManager
import threading
import datetime
import math
import time
import pprint

class TestBot(GenericTradingBot):
    def __init__(self, client, oneTimeCrawler = None, orderManager = None, indicator = None):
        super().__init__()
        self.client = client
        self.symbols = []
        self.futures_klines = []

        self.oneTimeCrawler = oneTimeCrawler
        self.orderManager = orderManager
        self.indicator = indicator

    def _main(self):
        ##TODO: write logic for bots
        ##trading bot start
        
        self.scenario_01()
    
    def scenario_01(self):
        #start scheduler 15min to update klines, generate indicators and check buy signal
        next_15m_candle_scheduler = self._scheduler(self.scenario_01_callback, 15*60)  
    
    def scenario_01_callback(self):
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
            if not candles['15m']:
                continue
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
    


    def stop(self):
        
        if self.scheduler:
            self.scheduler.cancel()
        
        self.running = False



        
        
if __name__ == "__main__":
    pass