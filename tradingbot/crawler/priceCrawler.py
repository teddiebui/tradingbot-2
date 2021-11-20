

import threading
import time
import queue



import pprint

class PriceCrawler:

    def __init__(self, client):

        self.prices_list = queue.Queue()
        self.prices=[]
        self.client = client
        self.THREADS = []
        self.is_running = False
        
        self.count = 0



    def start_crawling(self):

        thread = threading.Thread(target=self._start_crawling_handler, args=())
        thread.start()
        self.THREADS.append(thread)


    def get(self, symbol=""):

        if not symbol: #return a dict
            return self.get(timeout=3)

        #return a float 
        self.prices = self.prices_list.get(timeout=3)
        for i in self.prices:
            if i['symbol'].upper() == symbol.upper():
                return float(i['price'])

        return 0


    def _start_crawling_handler(self):

        self.is_running = True
        
        a = time.time()
        while self.is_running == True:
            b = time.time()

            self.prices_list.put(self.client.get_all_tickers())


            #internal counter
            self.count += 1
            #debug
            done = time.time() - b
            print("--time: {:5.2f} -- lapsed: {:5.2f} -- count: {}--".format(
                done, 
                time.time() - a,
                self.count))
            if done < 0.25:
                time.sleep(0.35-done)
            if self.count % 1000 == 0 and self.count > 0:
                self.start_crawling()
                return
            
    def terminate(self):

        self.is_running = False

if __name__ == "__main__":
    import alertBot
    
    bot = alertBot.AlertBot()

    ## BACK TESTING

    from binance.client import Client

    client = Client("TFWFmx5lPFNkkQnEIQsl2596kr1errGmaabzC3bFWI17mifeIYmnBybtU4Opkkyp", "kBzXtdMQsOVCrfV9qwyCabshmyALX3ABNjzGJF2a7ZoHF7oh6lzh4gEuvHOwQBSR")

    p = PriceCrawler(client)

    p.start_crawling()

    try:
        while True:
            price = p.get(symbol="BTCUSDT")
            print(price)
            
            if price <= 50100:
                bot.alert()
    except KeyboardInterrupt as e:
        print("---------STOPPED")
        print(repr(e))
        p.terminate()
    
