# from myapp.tradingbot2.APIBot import OneTimeCrawler
from ..TradingBot.GenericTradingBot import GenericTradingBot
from ..APIBot import OneTimeCrawler
from ..OrderManager import OrderManager
import threading
import datetime
import math
import time
from pprint import pprint

class TestBot(GenericTradingBot):
    def __init__(self, client, oneTimeCrawler = None, orderManager = None, indicator = None):
        super().__init__()
        self.client = client
        self.symbols = []
        self.futures_klines = []

        self.oneTimeCrawler = oneTimeCrawler
        self.oneTimeCrawler = orderManager
        self.indicator= indicator



            
    
    def _main(self):
        ##TODO: write logic for bots
        ##trading bot start
        
        self.scenario_01()
    
    def scenario_01(self):
        next_15m_candle_timer = self._timer(self.oneTimeCrawler.klines_update)  


    def stop(self):
        
        if self.timer:
            self.timer.cancel()
        
        self.running = False



        
        
if __name__ == "__main__":
    pass