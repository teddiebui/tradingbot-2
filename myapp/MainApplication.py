import time
import pprint
import threading
import json
import queue
import collections
import pprint
import os
import sys
import requests


from binance.enums import *
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from tradingbot2.APIBot import OneTimeCrawler

import tradingbot2.TradingBot.TestBot as tb
import tradingbot2.OrderManager.OrderManager as om

class MainApplication:
    def __init__(self,apiKey, apiSecret):
        self.client = Client(apiKey, apiSecret)
        self.BOTS = []
        
    def run(self):
        if len(self.BOTS) > 0:
            for each in self.BOTS:
                each.start()
        else:
            bot = tb.TestBot(self.client)
            bot.symbol = "BNBUSDT"
            self.BOTS.append(bot)

            bot.start()
        
    def stop(self):
        for each in self.BOTS:
            each.stop()





if __name__ == "__main__":
    from datetime import datetime

    apiKey = "XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6"
    apiSecret = "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg"
    
    main = MainApplication(apiKey, apiSecret)
    main.run()

    # o = om.OrderManager(main.client)
    # order = o.futures_new_order_market("BNBUSDT")
    # orders = main.client.futures_get_all_orders()
    # for each in orders:
    #     print(datetime.fromtimestamp(int(each['updateTime'])/1000))

    # order = o.futures_create_sl_order("BNBUSDT", 555.55, 0.1)

    # price = o.futures_get_price("BNBUSDT")
    # quantity = o.get_quantity(price, 100)
    # pprint.pprint(quantity);




