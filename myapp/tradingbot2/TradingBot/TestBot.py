# from myapp.tradingbot2.APIBot import OneTimeCrawler
from ..TradingBot.GenericTradingBot import GenericTradingBot
from ..APIBot import OneTimeCrawler
from ..OrderManager import OrderManager
from pprint import pprint

class TestBot(GenericTradingBot):
    def __init__(self, client):
        super().__init__();
        self.client = client
        self.symbols = []
        self.futures_klines = []

        self.oneTimeCrawler = None
        self.orderManager = None
            

    def _initialize(self):
        self.running = True
        #create one time crawler
        self.oneTimeCrawler = OneTimeCrawler.OneTimeCrawler(self.client)
        #create orderManager
        self.orderManager = OrderManager.OrderManager(self.client)

    
    def _main(self):
        ##TODO: write logic for bots
        ##trading bot start
        if self.running == False:
            self.running = True
            self._initialize()

        self.logic_1()
    
    def logic_1(self):
        pass
   
    
    
    def stop(self):
        if self.oneTimeCrawler:
            self.oneTimeCrawler.stop()
        
        if self.timer:
            self.timer.cancel()
        
        self.running = False



        
        
if __name__ == "__main__":
    pass