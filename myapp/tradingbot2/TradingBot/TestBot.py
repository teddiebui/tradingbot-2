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

        if self.running == False:
            self._initialize()

    def _initialize(self):

        self.running = True
        #create one time crawler
        self.oneTimeCrawler = OneTimeCrawler.OneTimeCrawler(self.client)
        #create orderManager
        self.orderManager = OrderManager.OrderManager(self.client)

    
    def _main(self):
        ##trading bot start
        self.running = True

        
        ##TODO: write logic for bots
        self.logic_1()
    
    def logic_1(self):

        def _call_back(self):
            self.futures_klines = self.oneTimeCrawler.get_klines(symbols=self.symbols)


        self.symbols = self.oneTimeCrawler.get_all_futures_symbol_name()
        self.futures_klines = self.oneTimeCrawler.get_klines(symbols=self.symbols, startTime = self.oneTimeCrawler._timestamp(30))
        ##automated crawling
        timer = self._next_15m_timer(lambda: self._call_back())
        timer.start()
        
   
    
    
    def stop(self):
        if self.oneTimeCrawler:
            self.oneTimeCrawler.stop()
        
        if self.timer:
            self.timer.cancel()
        
        self.running = False



        
        
if __name__ == "__main__":
    t = TestBot()
    c = OneTimeCrawler.OneTimeCrawler()