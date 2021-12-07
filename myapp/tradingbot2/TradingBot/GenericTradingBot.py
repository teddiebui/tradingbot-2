import threading
import time
import math
import datetime

from ..OrderManager.OrderManager import OrderManager as om

class GenericTradingBot():
    def __init__(self):
        ## thread config
        super().__init__()
        self.thread_count = 0
        self.thread = None
        self.running = False
        self.exc = None
        self.buffered = 3

        print("generic bot created")
        ##

    
    def start(self):
        self.thread = threading.Thread(target = self._main, args=())
        self.thread.start()
        self.thread_count += 1
        self.running = True
        self.scheduler = None

    

        
    def stop(self):
        self.running = False
        
    def _main(self):
        
        pass
        
        #implemented by sub class
        #should handle while self.running == True
    def _raise_exc_if_any(self):
        if self.exc:
            raise self.exc
            



if __name__ == "__main__":
    tf = GenericTradingBot()
    tf.start()
            
    
        