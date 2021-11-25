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

from tradingbot2.APIBot.OneTimeCrawler import OneTimeCrawler
from tradingbot2.APIBot.WebSocketCrawler import WebSocketCrawler
from tradingbot2.OrderManager.OrderManager import OrderManager
from tradingbot2.Indicator.Indicator import OrderManager

import tradingbot2.TradingBot.TestBot as tb

class MainApplication:
    def __init__(self):
        self.client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")
        self.BOTS = []
        
    def run(self):
        if len(self.BOTS) > 0:
            for each in self.BOTS:
                each.start()
        else:
            orderManager = OrderManager(self.client)
            oneTimeCrawler = OneTimeCrawler(self.client)
            indicator = Indicator

            bot = tb.TestBot(self.client, orderManager, oneTimeCrawle, indicator)
            bot.orderManager = orderManager
            bot.oneTimeCrawler = oneTimeCrawler
            bot.symbol = "BNBUSDT"
            self.BOTS.append(bot)

            bot.start()
        
    def stop(self):
        for each in self.BOTS:
            each.stop()





if __name__ == "__main__":

    
    
    main = MainApplication()
    main.run()


