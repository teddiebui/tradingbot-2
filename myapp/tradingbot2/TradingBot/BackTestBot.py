import os
import json
import pprint
import time
import datetime
import pandas

class BackTestBot:
    def __init__(self, client, oneTimeCrawler = None, orderManager = None, indicator = None):
        super().__init__()
        self.client = client
        self.symbols = []
        self.futures_klines = []

        self.oneTimeCrawler = oneTimeCrawler
        self.orderManager = orderManager
        self.indicator = indicator

        self.orderManager.testMode = True

        self.symbols = ["BNBUSDT","BTCUSDT","DOTUSDT","ADAUSDT","LTCUSDT","LINKUSDT", "SOLUSDT", "AVAXUSDT"]
        self.klines = {}
        self.indicators = {}

        print("back test bot created")

    
    def start(self):
        for symbol in self.symbols:
            # read data
            klines = self.oneTimeCrawler._klines_from_file(symbol)
            refined_klines = self.oneTimeCrawler._build_klines_from_array(klines)
            current_klines = refined_klines['15m']

            # for i in range(1,11):
            #     self.orderManager.stop_loss = i/100
            #     self.orderManager.ORDERS[symbol] = {}
            #     self.logic_01(current_klines, symbol)

                

            self.logic_01(current_klines, symbol)
            return
        print("done")
    
    def logic_01(self, current_klines, symbol):
        close = [i['close'] for i in current_klines]
        self.indicator.set_data(close)
        rsi14 = self.indicator.rsi()

        for i in range(len(current_klines)):
                
            low_price = current_klines[i]['low']

            try:
                orders = self.orderManager.ORDERS[symbol][str(len(self.orderManager.ORDERS[symbol]))]
                order = orders[0]
                stoploss_order = orders[-1]
                
                if stoploss_order['status'] == "NEW":
                    if low_price <= float(stoploss_order['price']):
                        print("order: {}, stop loss met {},  stoploss_price: {}, buy price: {} - loss: {}".format(str(len(self.orderManager.ORDERS[symbol])), datetime.datetime.fromtimestamp(current_klines[i]['time']), stoploss_order['price'], self.orderManager.LAST_BUY_PRICE[symbol], (stoploss_order['price'] - orders[0]['price'])/orders[0]['price'] * 100))
                        stoploss_order['status'] = "FILLED"
                        self.orderManager.IN_HOLDING.remove(symbol)
                    else:
                        trailing_stop = self.test_trailing_stop(symbol, orders, close[i], current_klines[i]['time'])
                        continue
                        
            except KeyError as e:
                #dont have any order
                pass
                
            can_buy = self.check_if_can_buy(symbol, current_klines[i], rsi14[i])

            if can_buy:
                new_order = self.orderManager.test_create_order(symbol, close[i], current_klines[i]['time'])
                new_stoploss_order = self.orderManager.test_create_stoploss_order(symbol,close[i] * (1-self.orderManager.stop_loss), current_klines[i]['time'])
                self.orderManager._add_to_memory(symbol, [new_order, new_stoploss_order])
                self.orderManager.IN_HOLDING.append(symbol)
                self.orderManager.LAST_BUY_PRICE[symbol] = float(new_order['price'])

                

        # print("done")
        # print("there are {} orders".format(len(self.orderManager.ORDERS[symbol])))
        # print("of which:")

        total_revenue = 1
        for i, v in self.orderManager.ORDERS[symbol].items():
            revenue = (float(v[-1]['price']) - float(v[0]['price']))/float(v[0]['price']) * 100 
            total_revenue *= (100 + revenue)/100
            print("order {} has {} orders, {:.2f} - revenue: {:.2f}".format(i, len(v), revenue, total_revenue))

        print("{}, total revenue: {:.4f}".format(symbol, total_revenue))
        
    
    def logic_02(self):
        pass

    def check_if_can_buy(self, symbol, candle, rsi):
        UPPER_BOUND = 70
        LOWER_BOUND = 30

        
        if rsi < LOWER_BOUND:
            print("symbol: {}| time: {}, rsi: {:.4f}, close: {}".format(symbol, datetime.datetime.fromtimestamp(candle['time']), rsi, candle['close']))
            return True

    def test_trailing_stop(self, symbol, orders, close, time):
        #symbol:    string
        #orders:    list
        #close:       float
        #time:      python timestamp
        #return:    boolean

        order = orders[0]
        stoploss_order = orders[-1]

        if self.orderManager.LAST_BUY_PRICE[symbol] < close:

            stoploss_order['status'] = "CANCELED"

            stoploss_price = close * (1 - self.orderManager.stop_loss)
            new_stoploss_order = self.orderManager.test_create_stoploss_order(symbol, stoploss_price, time)

            orders.append(new_stoploss_order)
            self.orderManager.LAST_BUY_PRICE[symbol] = close
            return True

        return False
        

if __name__ == "__main__":
    pass